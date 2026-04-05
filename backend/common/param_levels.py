"""
参数层级与调整机制设计

定义游戏中哪些参数可以被谁、在什么时候调整
"""

from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, List
from enum import Enum
import json

from backend.common.config import GameConfig


class ParamLevel(Enum):
    """参数层级"""
    SYSTEM = "system"       # 系统级：开发者预设，整个游戏期间不变
    GAME = "game"           # 游戏级：玩家开局时设定，游戏期间不变
    ROUND = "round"         # 回合级：每回合开始时可调整
    CYCLE = "cycle"         # 循环级：每个循环内动态变化
    AGENT = "agent"         # Agent级：Agent自己决定


class ParamOwner(Enum):
    """参数所有者"""
    DEVELOPER = "developer"   # 开发者
    PLAYER = "player"         # 玩家
    GAME_MASTER = "game_master"  # 游戏主持（如果有的话）
    AGENT = "agent"           # Agent自己


@dataclass
class ParamDefinition:
    """参数定义"""
    name: str                          # 参数名
    category: str                      # 分类（traitor, energy, trust等）
    level: ParamLevel                  # 层级
    owner: ParamOwner                  # 所有者
    description: str                   # 描述
    default_value: float               # 默认值
    min_value: float                   # 最小值
    max_value: float                   # 最大值
    adjustment_cost: float = 0.0       # 调整代价（用于游戏机制）
    requires_unlock: bool = False      # 是否需要解锁
    unlock_condition: str = ""         # 解锁条件


# ============================================
# 参数定义表：定义每个参数的调整规则
# ============================================

PARAM_DEFINITIONS: Dict[str, ParamDefinition] = {
    # ===== 内鬼机制参数 =====
    "traitor.activate_tendency_threshold": ParamDefinition(
        name="内鬼激活阈值",
        category="traitor",
        level=ParamLevel.GAME,
        owner=ParamOwner.PLAYER,
        description="Agent内鬼倾向超过此值才可能激活",
        default_value=0.4,
        min_value=0.1,
        max_value=0.8,
        requires_unlock=False
    ),
    "traitor.activate_probability_multiplier": ParamDefinition(
        name="内鬼激活概率乘数",
        category="traitor",
        level=ParamLevel.GAME,
        owner=ParamOwner.PLAYER,
        description="影响内鬼激活的基础概率",
        default_value=0.5,
        min_value=0.1,
        max_value=1.0,
        requires_unlock=False
    ),
    "traitor.slack_base_rate": ParamDefinition(
        name="消极怠工基础比例",
        category="traitor",
        level=ParamLevel.AGENT,
        owner=ParamOwner.AGENT,
        description="内鬼选择消极怠工时的工作损失比例（Agent可自主决定）",
        default_value=0.3,
        min_value=0.1,
        max_value=0.8,
        adjustment_cost=0.1,  # 调整需要消耗认知资源
        requires_unlock=False
    ),

    # ===== 能量分配参数 =====
    "energy.default_work": ParamDefinition(
        name="默认工作能量分配",
        category="energy",
        level=ParamLevel.AGENT,
        owner=ParamOwner.AGENT,
        description="Agent默认分配给工作的能量（Agent可自主调整）",
        default_value=50.0,
        min_value=20.0,
        max_value=80.0,
        requires_unlock=False
    ),
    "energy.default_conflict": ParamDefinition(
        name="默认内斗能量分配",
        category="energy",
        level=ParamLevel.AGENT,
        owner=ParamOwner.AGENT,
        description="Agent默认分配给内斗的能量",
        default_value=10.0,
        min_value=0.0,
        max_value=40.0,
        requires_unlock=False
    ),

    # ===== 信任机制参数 =====
    "trust.decay_rate": ParamDefinition(
        name="信任衰减率",
        category="trust",
        level=ParamLevel.GAME,
        owner=ParamOwner.PLAYER,
        description="每循环信任自动衰减的比例",
        default_value=0.02,
        min_value=0.0,
        max_value=0.1,
        requires_unlock=False
    ),
    "trust.learning_rate_base": ParamDefinition(
        name="信任学习率",
        category="trust",
        level=ParamLevel.SYSTEM,
        owner=ParamOwner.DEVELOPER,
        description="Agent更新信任时的学习速率（核心机制参数）",
        default_value=0.1,
        min_value=0.05,
        max_value=0.3,
        requires_unlock=False
    ),

    # ===== 状态更新参数 =====
    "state_update.mental_load_threshold": ParamDefinition(
        name="心理负担阈值",
        category="state_update",
        level=ParamLevel.ROUND,
        owner=ParamOwner.PLAYER,
        description="心理负担超过此阈值会增加认知熵",
        default_value=0.6,
        min_value=0.3,
        max_value=0.9,
        requires_unlock=False
    ),

    # ===== 架构参数 =====
    "architecture.star_efficiency_coefficient": ParamDefinition(
        name="星形架构效率系数",
        category="architecture",
        level=ParamLevel.SYSTEM,
        owner=ParamOwner.DEVELOPER,
        description="星形架构的产出效率系数（核心平衡参数）",
        default_value=1.3,
        min_value=0.5,
        max_value=2.0,
        requires_unlock=True,
        unlock_condition="完成10局游戏后解锁"
    ),
}


@dataclass
class ParamAdjustment:
    """参数调整记录"""
    param_name: str
    old_value: float
    new_value: float
    adjuster: str           # 谁调整的
    cycle: int              # 在哪个循环调整的
    reason: str = ""        # 调整原因


class ParamManager:
    """
    参数管理器

    负责：
    1. 验证参数调整是否合法
    2. 记录参数调整历史
    3. 提供参数查询接口
    """

    def __init__(self, config: GameConfig = None):
        self.config = config or GameConfig()
        self.adjustment_history: List[ParamAdjustment] = []
        self.unlocked_params: set = set()

    def can_adjust(self, param_path: str, requester: ParamOwner) -> tuple[bool, str]:
        """
        检查参数是否可以被调整

        Returns:
            (是否可以调整, 原因说明)
        """
        if param_path not in PARAM_DEFINITIONS:
            return False, f"未知参数: {param_path}"

        param_def = PARAM_DEFINITIONS[param_path]

        # 检查所有者权限
        if param_def.owner != requester:
            return False, f"此参数只能由 {param_def.owner.value} 调整"

        # 检查是否需要解锁
        if param_def.requires_unlock and param_path not in self.unlocked_params:
            return False, f"此参数需要解锁: {param_def.unlock_condition}"

        return True, "可以调整"

    def adjust_param(self, param_path: str, new_value: float,
                     requester: ParamOwner, cycle: int,
                     reason: str = "") -> tuple[bool, str]:
        """
        调整参数

        Returns:
            (是否成功, 消息)
        """
        # 检查权限
        can_adj, msg = self.can_adjust(param_path, requester)
        if not can_adj:
            return False, msg

        param_def = PARAM_DEFINITIONS[param_path]

        # 检查值范围
        if new_value < param_def.min_value or new_value > param_def.max_value:
            return False, f"值必须在 [{param_def.min_value}, {param_def.max_value}] 范围内"

        # 获取旧值
        old_value = self._get_param_value(param_path)

        # 更新值
        self._set_param_value(param_path, new_value)

        # 记录调整历史
        self.adjustment_history.append(ParamAdjustment(
            param_name=param_path,
            old_value=old_value,
            new_value=new_value,
            adjuster=requester.value,
            cycle=cycle,
            reason=reason
        ))

        return True, f"参数 {param_path} 已从 {old_value} 调整为 {new_value}"

    def _get_param_value(self, param_path: str) -> float:
        """获取参数当前值"""
        parts = param_path.split(".")
        obj = self.config
        for part in parts:
            obj = getattr(obj, part)
        return obj

    def _set_param_value(self, param_path: str, value: float):
        """设置参数值"""
        parts = param_path.split(".")
        obj = self.config
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

    def get_adjustable_params(self, owner: ParamOwner) -> List[ParamDefinition]:
        """获取某角色可调整的所有参数"""
        return [
            param for param in PARAM_DEFINITIONS.values()
            if param.owner == owner
        ]

    def export_adjustable_params(self) -> dict:
        """导出玩家可调整的参数（用于前端UI）"""
        player_params = {}
        for path, param_def in PARAM_DEFINITIONS.items():
            if param_def.owner == ParamOwner.PLAYER:
                player_params[path] = {
                    "name": param_def.name,
                    "description": param_def.description,
                    "current_value": self._get_param_value(path),
                    "min": param_def.min_value,
                    "max": param_def.max_value,
                    "level": param_def.level.value,
                    "requires_unlock": param_def.requires_unlock
                }
        return player_params


# ============================================
# 使用示例
# ============================================

def example_usage():
    """演示参数调整机制的使用"""

    # 创建参数管理器
    param_manager = ParamManager()

    print("=" * 60)
    print("参数调整机制演示")
    print("=" * 60)

    # 1. 查看玩家可调整的参数
    print("\n【玩家可调整的参数】")
    player_params = param_manager.get_adjustable_params(ParamOwner.PLAYER)
    for param in player_params:
        print(f"  - {param.name}: {param.description}")

    # 2. 查看Agent可调整的参数
    print("\n【Agent可调整的参数】")
    agent_params = param_manager.get_adjustable_params(ParamOwner.AGENT)
    for param in agent_params:
        print(f"  - {param.name}: {param.description}")

    # 3. 尝试调整参数
    print("\n【尝试调整参数】")

    # 玩家调整游戏级参数 - 应该成功
    success, msg = param_manager.adjust_param(
        "traitor.activate_tendency_threshold",
        0.5,
        ParamOwner.PLAYER,
        cycle=0,
        reason="想让游戏更难"
    )
    print(f"  玩家调整内鬼阈值: {msg}")

    # Agent尝试调整自己的参数 - 应该成功
    success, msg = param_manager.adjust_param(
        "energy.default_work",
        60.0,
        ParamOwner.AGENT,
        cycle=1,
        reason="我是个勤劳的Agent"
    )
    print(f"  Agent调整工作能量: {msg}")

    # Agent尝试调整玩家参数 - 应该失败
    success, msg = param_manager.adjust_param(
        "traitor.activate_tendency_threshold",
        0.3,
        ParamOwner.AGENT,
        cycle=1,
        reason="我不想当内鬼"
    )
    print(f"  Agent尝试调整内鬼阈值: {msg}")

    # 4. 导出玩家可调参数（用于前端）
    print("\n【导出给前端UI的参数】")
    exportable = param_manager.export_adjustable_params()
    for path, info in exportable.items():
        print(f"  {path}: {info['current_value']} (范围: {info['min']}-{info['max']})")

    # 5. 查看调整历史
    print("\n【参数调整历史】")
    for adj in param_manager.adjustment_history:
        print(f"  回合{adj.cycle}: {adj.param_name} {adj.old_value}->{adj.new_value} by {adj.adjuster}")


if __name__ == "__main__":
    example_usage()
