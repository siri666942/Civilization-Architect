"""
游戏控制 API

提供游戏流程控制的REST接口
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from enum import Enum
import uuid
import asyncio
import json

from backend.core.engine import GameEngine, Civilization
from backend.models.agent import ArchitectureType, Agent
from backend.models.architecture import ArchitectureConfig, create_architecture
from backend.common.config import GameConfig, default_config


router = APIRouter()


# ============================================
# 请求/响应模型
# ============================================

class ArchitectureTypeEnum(str, Enum):
    """架构类型枚举（用于API）"""
    STAR = "star"
    TREE = "tree"
    MESH = "mesh"
    TRIBAL = "tribal"


class StartGameRequest(BaseModel):
    """开始游戏请求"""
    username: str
    architecture_type: ArchitectureTypeEnum
    total_rounds: int = 10
    seed: Optional[int] = None


class AgentPosition(BaseModel):
    """Agent位置信息"""
    agent_id: str
    position_index: int  # 在架构中的位置索引
    connections: List[int] = []  # 连接的其他位置索引（用于网状架构）


class UpdateArchitectureRequest(BaseModel):
    """更新架构请求"""
    positions: List[AgentPosition]


class RunRoundRequest(BaseModel):
    """执行轮次请求"""
    round_num: Optional[int] = None


class AgentCardResponse(BaseModel):
    """Agent卡片响应"""
    id: str
    name: str
    description: str
    personality: Dict[str, float]
    position: str
    level: int
    centrality: float
    is_traitor: bool


class GameStateResponse(BaseModel):
    """游戏状态响应"""
    game_id: str
    username: str
    architecture_type: str
    current_round: int
    total_rounds: int
    agents: List[AgentCardResponse]
    civilization_state: Dict[str, Any]
    adjacency_matrix: List[List[float]]


class RoundResultResponse(BaseModel):
    """轮次结果响应"""
    round_num: int
    cycle_outputs: List[float]
    total_output: float
    macro_variables: Dict[str, float]
    messages: List[Dict[str, Any]]


class FinalResultResponse(BaseModel):
    """最终结果响应"""
    game_id: str
    username: str
    architecture_type: str
    total_output: float
    final_macro_variables: Dict[str, float]
    traitor_count: int
    achievements: List[str]
    analysis_report: str
    history: List[Dict[str, Any]]


# ============================================
# 游戏会话管理
# ============================================

class GameSession:
    """游戏会话"""
    def __init__(self, game_id: str, username: str, engine: GameEngine):
        self.game_id = game_id
        self.username = username
        self.engine = engine
        self.architecture_type: ArchitectureType = None
        self.civilization: Civilization = None
        self.custom_adjacency: Optional[List[List[float]]] = None
        self.agent_positions: Dict[int, str] = {}  # 位置索引 -> Agent ID
        self.messages: List[Dict[str, Any]] = []
        self.round_history: List[Dict[str, Any]] = []


# 全局会话存储
_sessions: Dict[str, GameSession] = {}


def get_session(game_id: str) -> GameSession:
    """获取游戏会话"""
    if game_id not in _sessions:
        raise HTTPException(status_code=404, detail="游戏会话不存在")
    return _sessions[game_id]


def to_architecture_type(api_type: ArchitectureTypeEnum) -> ArchitectureType:
    """转换架构类型"""
    mapping = {
        ArchitectureTypeEnum.STAR: ArchitectureType.STAR,
        ArchitectureTypeEnum.TREE: ArchitectureType.TREE,
        ArchitectureTypeEnum.MESH: ArchitectureType.MESH,
        ArchitectureTypeEnum.TRIBAL: ArchitectureType.TRIBAL,
    }
    return mapping[api_type]


# ============================================
# API接口
# ============================================

@router.post("/start", response_model=GameStateResponse)
async def start_game(request: StartGameRequest):
    """
    开始新游戏

    创建游戏引擎，初始化Agent，返回初始状态
    """
    # 生成游戏ID
    game_id = f"GAME-{uuid.uuid4().hex[:8]}"

    # 创建游戏引擎
    arch_type = to_architecture_type(request.architecture_type)

    engine = GameEngine(
        num_civilizations=1,
        architecture_types=[arch_type],
        agents_per_civilization=10,
        total_rounds=request.total_rounds,
        seed=request.seed,
        config=default_config
    )

    # 初始化
    engine.initialize()

    # 创建会话
    session = GameSession(game_id, request.username, engine)
    session.architecture_type = arch_type
    session.civilization = engine.civilizations[0]

    _sessions[game_id] = session

    # 返回初始状态
    return _build_game_state_response(session)


@router.get("/{game_id}/status", response_model=GameStateResponse)
async def get_game_status(game_id: str):
    """
    获取游戏状态
    """
    session = get_session(game_id)
    return _build_game_state_response(session)


@router.post("/{game_id}/update-architecture")
async def update_architecture(game_id: str, request: UpdateArchitectureRequest):
    """
    更新架构配置

    接收前端传来的Agent位置信息，更新邻接矩阵
    """
    session = get_session(game_id)

    # 更新Agent位置映射
    session.agent_positions = {}
    for pos in request.positions:
        session.agent_positions[pos.position_index] = pos.agent_id

    # 如果是网状架构，需要根据connections更新邻接矩阵
    if session.architecture_type == ArchitectureType.MESH:
        n = len(session.civilization.agents)
        custom_adj = [[0.0] * n for _ in range(n)]

        for pos in request.positions:
            idx = pos.position_index
            for connected_idx in pos.connections:
                if 0 <= connected_idx < n:
                    custom_adj[idx][connected_idx] = 1.0
                    custom_adj[connected_idx][idx] = 1.0

        session.custom_adjacency = custom_adj

    return {"success": True, "message": "架构已更新"}


@router.post("/{game_id}/run-round", response_model=RoundResultResponse)
async def run_round(game_id: str, request: RunRoundRequest = None):
    """
    执行一轮模拟

    运行游戏引擎，计算产出，生成消息
    """
    session = get_session(game_id)

    # 应用自定义邻接矩阵（如果有）
    if session.custom_adjacency is not None:
        import numpy as np
        session.civilization.config.adjacency_matrix = np.array(
            session.custom_adjacency, dtype=float
        )

    # 执行一轮
    session.engine.run_round(session.civilization)

    # 记录历史
    round_data = {
        "round": session.civilization.state.round,
        "total_output": session.civilization.state.total_output,
        "energy_level": session.civilization.state.energy_level_history[-1] if session.civilization.state.energy_level_history else 0,
        "cohesion": session.civilization.state.cohesion_history[-1] if session.civilization.state.cohesion_history else 0,
        "fidelity": session.civilization.state.fidelity_history[-1] if session.civilization.state.fidelity_history else 0,
        "social_capital": session.civilization.state.social_capital_history[-1] if session.civilization.state.social_capital_history else 0,
    }
    session.round_history.append(round_data)

    # 生成模拟消息（简化版）
    messages = _generate_round_messages(session)

    return RoundResultResponse(
        round_num=session.civilization.state.round,
        cycle_outputs=session.civilization.state.cycle_outputs,
        total_output=session.civilization.state.total_output,
        macro_variables={
            "energy_level": round_data["energy_level"],
            "cohesion": round_data["cohesion"],
            "fidelity": round_data["fidelity"],
            "social_capital": round_data["social_capital"],
        },
        messages=messages
    )


@router.post("/{game_id}/end", response_model=FinalResultResponse)
async def end_game(game_id: str):
    """
    结束游戏

    计算最终结果，生成分析报告
    """
    session = get_session(game_id)

    # 计算最终宏观变量
    final_vars = {
        "energy_level": session.civilization.state.energy_level_history[-1] if session.civilization.state.energy_level_history else 0,
        "cohesion": session.civilization.state.cohesion_history[-1] if session.civilization.state.cohesion_history else 0,
        "fidelity": session.civilization.state.fidelity_history[-1] if session.civilization.state.fidelity_history else 0,
        "social_capital": session.civilization.state.social_capital_history[-1] if session.civilization.state.social_capital_history else 0,
    }

    # 统计内鬼数量
    traitor_count = sum(1 for a in session.civilization.agents if a.is_active_traitor)

    # 生成成就
    achievements = _generate_achievements(session)

    # 生成分析报告
    analysis = _generate_analysis_report(session)

    # 清理会话
    del _sessions[game_id]

    return FinalResultResponse(
        game_id=game_id,
        username=session.username,
        architecture_type=session.architecture_type.value,
        total_output=session.civilization.state.total_output,
        final_macro_variables=final_vars,
        traitor_count=traitor_count,
        achievements=achievements,
        analysis_report=analysis,
        history=session.round_history
    )


# ============================================
# WebSocket 实时通讯
# ============================================

class ConnectionManager:
    """WebSocket连接管理器"""
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.active_connections:
            self.active_connections[game_id] = []
        self.active_connections[game_id].append(websocket)

    def disconnect(self, game_id: str, websocket: WebSocket):
        if game_id in self.active_connections:
            self.active_connections[game_id].remove(websocket)

    async def broadcast(self, game_id: str, message: dict):
        if game_id in self.active_connections:
            for connection in self.active_connections[game_id]:
                await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/{game_id}/ws")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    """
    WebSocket连接

    实时推送游戏消息和状态更新
    """
    await manager.connect(game_id, websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()

            # 处理消息
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except json.JSONDecodeError:
                pass

    except WebSocketDisconnect:
        manager.disconnect(game_id, websocket)


# ============================================
# 辅助函数
# ============================================

def _build_game_state_response(session: GameSession) -> GameStateResponse:
    """构建游戏状态响应"""
    agents = []
    for agent in session.civilization.agents:
        agents.append(AgentCardResponse(
            id=agent.id,
            name=agent.name,
            description=agent.description,
            personality={
                "authority": agent.personality.authority,
                "selfishness": agent.personality.selfishness,
                "resilience": agent.personality.resilience,
                "altruism": agent.personality.altruism,
                "sociability": agent.personality.sociability,
                "risk_appetite": agent.personality.risk_appetite,
                "intelligence": agent.personality.intelligence,
                "loyalty_base": agent.personality.loyalty_base,
            },
            position=agent.position,
            level=agent.level,
            centrality=agent.centrality,
            is_traitor=agent.is_active_traitor
        ))

    # 获取邻接矩阵
    adj = session.civilization.config.adjacency_matrix.tolist()

    return GameStateResponse(
        game_id=session.game_id,
        username=session.username,
        architecture_type=session.architecture_type.value,
        current_round=session.civilization.state.round,
        total_rounds=session.engine.total_rounds,
        agents=agents,
        civilization_state={
            "total_output": session.civilization.state.total_output,
            "cycle_outputs": session.civilization.state.cycle_outputs,
        },
        adjacency_matrix=adj
    )


def _generate_round_messages(session: GameSession) -> List[Dict[str, Any]]:
    """生成轮次消息"""
    import random
    from datetime import datetime

    agents = session.civilization.agents
    messages = []

    # 获取连接关系
    adj = session.civilization.config.adjacency_matrix

    # 为每对连接的Agent生成消息
    for i, sender in enumerate(agents):
        for j, receiver in enumerate(agents):
            if adj[i, j] > 0 and i != j:
                # 简单消息生成
                msg_types = ["report", "chat", "status"]
                msg_type = random.choice(msg_types)

                tones = ["friendly", "neutral", "hostile"]
                tone = random.choice(tones)

                templates = {
                    "report": {
                        "friendly": f"@{receiver.name} 这轮贡献了{random.randint(20, 50)}单位，感觉不错！",
                        "neutral": f"汇报：完成{random.randint(30, 60)}单位工作。",
                        "hostile": f"做了{random.randint(20, 40)}，就这样。",
                    },
                    "chat": {
                        "friendly": f"@{receiver.name} 最近感觉进展不错啊~",
                        "neutral": f"状态同步一下。",
                        "hostile": f"没什么好说的。",
                    },
                    "status": {
                        "friendly": f"嘿{receiver.name}，进度正常！",
                        "neutral": f"状态更新：一切正常。",
                        "hostile": f"还在撑着。",
                    }
                }

                content = templates[msg_type][tone]

                messages.append({
                    "sender_id": sender.id,
                    "sender_name": sender.name,
                    "receiver_id": receiver.id,
                    "receiver_name": receiver.name,
                    "message_type": msg_type,
                    "content": content,
                    "tone": tone,
                    "timestamp": datetime.now().isoformat(),
                    "is_traitor": sender.is_active_traitor
                })

    return messages[:20]  # 限制消息数量


def _generate_achievements(session: GameSession) -> List[str]:
    """生成成就"""
    achievements = []

    output = session.civilization.state.total_output
    if output > 1000:
        achievements.append("🌟 文明缔造者")
    if output > 2000:
        achievements.append("🏆 战略大师")

    traitor_count = sum(1 for a in session.civilization.agents if a.is_active_traitor)
    if traitor_count == 0:
        achievements.append("🛡️ 净土守护者")

    cohesion = session.civilization.state.cohesion_history[-1] if session.civilization.state.cohesion_history else 0
    if cohesion > 0.8:
        achievements.append("✨ 团结之星")

    return achievements


def _generate_analysis_report(session: GameSession) -> str:
    """生成分析报告"""
    output = session.civilization.state.total_output
    arch_type = session.architecture_type.value
    rounds = session.civilization.state.round

    arch_names = {
        "star": "星形架构",
        "tree": "树形架构",
        "mesh": "网状架构",
        "tribal": "部落架构",
    }

    report = f"""
## 游戏分析报告

**指挥官**: {session.username}
**架构选择**: {arch_names.get(arch_type, arch_type)}
**总轮次**: {rounds}
**最终星辰值**: {output:.2f}

### 架构分析
您选择了{arch_names.get(arch_type, arch_type)}，这种架构的特点是...

### Agent表现分析
在本次游戏中，各Agent的表现如下：
"""

    for agent in session.civilization.agents[:5]:
        report += f"- **{agent.name}**: 贡献值 {agent.state.contribution:.2f}, 效率 {agent.state.efficiency:.2%}\n"

    traitor_count = sum(1 for a in session.civilization.agents if a.is_active_traitor)
    if traitor_count > 0:
        report += f"\n### 警告\n检测到 {traitor_count} 个Agent存在内鬼行为，这影响了文明的整体产出。\n"

    report += "\n### 改进建议\n建议在下次游戏中尝试不同的架构组合，优化Agent的位置分配。\n"

    return report