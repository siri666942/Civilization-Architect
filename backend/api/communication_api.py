"""
通讯系统API

提供前端展示所需的API接口
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

from backend.models.message import Message, MessageType, ConversationThread
from backend.models.message_store import MessageStore, get_message_store
from backend.core.dialogue_generator import DialogueGenerator


# ============================================
# API响应模型
# ============================================

@dataclass
class ApiResponse:
    """通用API响应"""
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MessageSummary:
    """消息摘要（用于列表展示）"""
    message_id: str
    sender_name: str
    receiver_name: str
    message_type: str
    preview: str          # 消息预览
    tone: str             # 语气
    timestamp: str
    importance: float
    is_traitor: bool

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ConversationView:
    """对话视图（用于对话展示）"""
    thread_id: str
    participants: List[Dict]   # [{id, name}]
    messages: List[Dict]
    topic: str
    message_count: int
    last_activity: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class CivilizationActivity:
    """文明活动摘要"""
    civilization_id: str
    total_messages: int
    active_agents: List[Dict]
    recent_important: List[Dict]
    traitor_alerts: int
    mood_distribution: Dict[str, float]

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================
# API接口
# ============================================

class CommunicationAPI:
    """
    通讯系统API

    提供以下接口：
    1. 获取消息列表
    2. 获取对话详情
    3. 获取文明活动
    4. 获取内鬼消息
    5. 按时间线展示
    """

    def __init__(self, store: MessageStore = None):
        self.store = store or get_message_store()

    # ----------------------------------------
    # 1. 消息列表接口
    # ----------------------------------------

    def get_messages(
        self,
        civilization_id: str,
        round_num: int = None,
        cycle_num: int = None,
        message_type: str = None,
        min_importance: float = 0.0,
        limit: int = 50,
        offset: int = 0
    ) -> ApiResponse:
        """
        获取消息列表

        Args:
            civilization_id: 文明ID
            round_num: 筛选回合（可选）
            cycle_num: 筛选循环（可选）
            message_type: 筛选消息类型（可选）
            min_importance: 最小重要性
            limit: 返回数量
            offset: 偏移量（分页）

        Returns:
            ApiResponse with MessageSummary list
        """
        try:
            msg_type = MessageType(message_type) if message_type else None

            messages = self.store.get_messages_by_civilization(
                civilization_id=civilization_id,
                round_num=round_num,
                cycle_num=cycle_num,
                message_type=msg_type,
                limit=limit + offset
            )

            # 过滤重要性
            messages = [m for m in messages if m.importance_score >= min_importance]

            # 分页
            messages = messages[offset:offset + limit]

            # 转换为摘要
            summaries = [self._message_to_summary(m) for m in messages]

            return ApiResponse(
                success=True,
                data={
                    "messages": [s.to_dict() for s in summaries],
                    "total": len(summaries),
                    "has_more": len(summaries) == limit
                }
            )

        except Exception as e:
            return ApiResponse(success=False, error=str(e))

    def _message_to_summary(self, msg: Message) -> MessageSummary:
        """消息转摘要"""
        preview = ""
        tone = "neutral"
        if msg.natural_language:
            preview = msg.natural_language.message[:50]
            if len(msg.natural_language.message) > 50:
                preview += "..."
            tone = msg.natural_language.tone.value

        return MessageSummary(
            message_id=msg.message_id,
            sender_name=msg.sender_name or msg.sender_id,
            receiver_name=msg.receiver_name or msg.receiver_id,
            message_type=msg.message_type.value,
            preview=preview,
            tone=tone,
            timestamp=msg.timestamp,
            importance=msg.importance_score,
            is_traitor=msg.is_traitor_action
        )

    # ----------------------------------------
    # 2. 对话详情接口
    # ----------------------------------------

    def get_conversation(
        self,
        agent1_id: str,
        agent2_id: str,
        civilization_id: str,
        limit: int = 100
    ) -> ApiResponse:
        """
        获取两个Agent之间的完整对话

        Args:
            agent1_id: Agent1 ID
            agent2_id: Agent2 ID
            civilization_id: 文明ID
            limit: 消息数量限制

        Returns:
            ApiResponse with ConversationView
        """
        try:
            thread = self.store.get_thread(agent1_id, agent2_id, civilization_id)

            view = ConversationView(
                thread_id=thread.thread_id,
                participants=[
                    {"id": pid, "name": pid} for pid in thread.participants
                ],
                messages=[m.to_dict() for m in thread.messages[-limit:]],
                topic=thread.topic or f"{agent1_id}与{agent2_id}的对话",
                message_count=len(thread.messages),
                last_activity=thread.last_activity
            )

            return ApiResponse(
                success=True,
                data=view.to_dict()
            )

        except Exception as e:
            return ApiResponse(success=False, error=str(e))

    # ----------------------------------------
    # 3. 文明活动接口
    # ----------------------------------------

    def get_civilization_activity(
        self,
        civilization_id: str,
        rounds: int = 3
    ) -> ApiResponse:
        """
        获取文明活动摘要（首页展示用）

        Args:
            civilization_id: 文明ID
            rounds: 统计最近几回合

        Returns:
            ApiResponse with CivilizationActivity
        """
        try:
            activity_data = self.store.get_recent_activity(civilization_id, rounds)

            # 统计内鬼警报
            traitor_msgs = self.store.get_traitor_messages(civilization_id)
            traitor_alerts = len([m for m in traitor_msgs if m.message_type == MessageType.ALERT])

            # 计算心情分布
            recent_messages = self.store.get_messages_by_civilization(
                civilization_id, limit=100
            )
            mood_dist = self._calculate_mood_distribution(recent_messages)

            activity = CivilizationActivity(
                civilization_id=civilization_id,
                total_messages=sum(
                    stats.get("count", 0)
                    for stats in activity_data.get("message_type_stats", {}).values()
                ),
                active_agents=activity_data.get("active_agents", []),
                recent_important=activity_data.get("important_messages", []),
                traitor_alerts=traitor_alerts,
                mood_distribution=mood_dist
            )

            return ApiResponse(
                success=True,
                data=activity.to_dict()
            )

        except Exception as e:
            return ApiResponse(success=False, error=str(e))

    def _calculate_mood_distribution(self, messages: List[Message]) -> Dict[str, float]:
        """计算心情分布"""
        tone_counts = {}
        for msg in messages:
            if msg.natural_language:
                tone = msg.natural_language.tone.value
                tone_counts[tone] = tone_counts.get(tone, 0) + 1

        total = sum(tone_counts.values())
        if total == 0:
            return {}

        return {tone: count / total for tone, count in tone_counts.items()}

    # ----------------------------------------
    # 4. 内鬼消息接口
    # ----------------------------------------

    def get_traitor_messages(
        self,
        civilization_id: str,
        include_detected: bool = False
    ) -> ApiResponse:
        """
        获取内鬼相关消息（用于展示内鬼活动）

        Args:
            civilization_id: 文明ID
            include_detected: 是否包含已检测到的

        Returns:
            ApiResponse with traitor messages
        """
        try:
            messages = self.store.get_traitor_messages(
                civilization_id, include_detected
            )

            return ApiResponse(
                success=True,
                data={
                    "messages": [m.to_dict() for m in messages],
                    "total": len(messages),
                    "undetected_count": len([m for m in messages if not m.was_detected])
                }
            )

        except Exception as e:
            return ApiResponse(success=False, error=str(e))

    # ----------------------------------------
    # 5. 时间线接口
    # ----------------------------------------

    def get_timeline(
        self,
        civilization_id: str,
        round_num: int = None
    ) -> ApiResponse:
        """
        获取消息时间线（用于可视化展示）

        Args:
            civilization_id: 文明ID
            round_num: 回合号（可选，默认最近回合）

        Returns:
            ApiResponse with timeline data
        """
        try:
            # 获取消息
            if round_num is None:
                # 获取最近回合
                all_msgs = self.store.get_messages_by_civilization(
                    civilization_id, limit=1
                )
                if all_msgs:
                    round_num = all_msgs[0].round_num
                else:
                    round_num = 1

            messages = self.store.get_messages_by_civilization(
                civilization_id, round_num=round_num
            )

            # 按循环分组
            timeline = {}
            for msg in messages:
                cycle = msg.cycle_num
                if cycle not in timeline:
                    timeline[cycle] = []
                timeline[cycle].append(msg.to_dict())

            return ApiResponse(
                success=True,
                data={
                    "civilization_id": civilization_id,
                    "round_num": round_num,
                    "timeline": timeline,
                    "total_messages": len(messages)
                }
            )

        except Exception as e:
            return ApiResponse(success=False, error=str(e))

    # ----------------------------------------
    # 6. 热门对话接口
    # ----------------------------------------

    def get_hot_conversations(
        self,
        civilization_id: str,
        limit: int = 5
    ) -> ApiResponse:
        """
        获取热门对话（消息最多、最重要的对话）

        Args:
            civilization_id: 文明ID
            limit: 返回数量

        Returns:
            ApiResponse with conversation list
        """
        try:
            # 获取活跃Agent
            activity = self.store.get_recent_activity(civilization_id)
            active_agents = activity.get("active_agents", [])[:limit * 2]

            # 获取这些Agent之间的对话
            conversations = []
            checked_pairs = set()

            for i, agent1 in enumerate(active_agents):
                for agent2 in active_agents[i + 1:]:
                    pair = tuple(sorted([agent1["id"], agent2["id"]]))
                    if pair in checked_pairs:
                        continue
                    checked_pairs.add(pair)

                    thread = self.store.get_thread(
                        agent1["id"], agent2["id"], civilization_id
                    )
                    if thread.messages:
                        conversations.append({
                            "participants": [
                                {"id": agent1["id"], "name": agent1["name"]},
                                {"id": agent2["id"], "name": agent2["name"]}
                            ],
                            "message_count": len(thread.messages),
                            "preview": thread.get_preview(),
                            "last_activity": thread.last_activity
                        })

            # 按消息数排序
            conversations.sort(key=lambda x: x["message_count"], reverse=True)

            return ApiResponse(
                success=True,
                data={
                    "conversations": conversations[:limit]
                }
            )

        except Exception as e:
            return ApiResponse(success=False, error=str(e))


# ============================================
# 便捷函数
# ============================================

def create_api_response(success: bool, data=None, error=None) -> Dict:
    """创建API响应的便捷函数"""
    return ApiResponse(success=success, data=data, error=error).to_dict()


# 全局API实例
_api_instance: Optional[CommunicationAPI] = None


def get_communication_api() -> CommunicationAPI:
    """获取通讯API实例"""
    global _api_instance
    if _api_instance is None:
        _api_instance = CommunicationAPI()
    return _api_instance