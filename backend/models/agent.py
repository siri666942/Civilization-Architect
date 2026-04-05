"""
Agent数据模型

定义Agent的性格属性、状态变量和信任矩阵
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import numpy as np
from enum import Enum

from backend.common.config import default_config


class ArchitectureType(Enum):
    """架构类型"""
    STAR = "star"
    TREE = "tree"
    MESH = "mesh"
    TRIBAL = "tribal"


class TraitorBehavior(Enum):
    """内鬼行为类型"""
    TAMPER = "TAMPER"      # 信息篡改
    INJECT = "INJECT"      # 提示词注入
    SLACK = "SLACK"        # 消极怠工
    STEAL = "STEAL"        # 资源挪用
    INCITE = "INCITE"      # 煽动叛变
    LEAK = "LEAK"          # 情报泄露
    NORMAL = "NORMAL"      # 正常行为


@dataclass
class Personality:
    """八维性格属性"""
    authority: float      # 权威感度 [0,1]
    selfishness: float    # 私心倾向 [0,1]
    resilience: float     # 韧性 [0,1]
    altruism: float       # 利他性 [0,1]
    sociability: float    # 社交性 [0,1]
    risk_appetite: float  # 风险偏好 [0,1]
    intelligence: float   # 智力 [0,1]
    loyalty_base: float   # 忠诚度基准 [0,1]

    def to_array(self) -> np.ndarray:
        """转换为数组"""
        return np.array([
            self.authority, self.selfishness, self.resilience,
            self.altruism, self.sociability, self.risk_appetite,
            self.intelligence, self.loyalty_base
        ])

    @classmethod
    def from_array(cls, arr: np.ndarray) -> 'Personality':
        """从数组创建"""
        return cls(
            authority=float(arr[0]),
            selfishness=float(arr[1]),
            resilience=float(arr[2]),
            altruism=float(arr[3]),
            sociability=float(arr[4]),
            risk_appetite=float(arr[5]),
            intelligence=float(arr[6]),
            loyalty_base=float(arr[7])
        )

    def calculate_traitor_tendency(self) -> float:
        """计算内鬼倾向"""
        from scipy.special import expit as sigmoid

        value = (
            2.0 * self.selfishness
            - 1.5 * self.loyalty_base
            - 1.0 * self.altruism
            + 0.5 * self.risk_appetite
            - 0.5
        )
        return float(sigmoid(value))


@dataclass
class AgentState:
    """Agent动态状态"""
    energy: float = 100.0                    # 体力值 [0, 100]
    cognitive_entropy: float = 0.1           # 认知熵 [0, 1]
    loyalty: float = 0.5                     # 当前忠诚度 [0, 1]
    contribution: float = 0.0                # 累计贡献值
    efficiency: float = 0.5                  # 转化率

    # 体力分配
    energy_work: float = 50.0                # 干活分配
    energy_conflict: float = 20.0            # 内斗分配
    energy_comm: float = 10.0                # 通讯分配

    def reset_energy(self):
        """重置体力（每循环开始）"""
        self.energy = 100.0

    def calculate_mental_load(self, avg_trust: float, position_stress: float = 0.1) -> float:
        """计算心理负担"""
        return (
            self.cognitive_entropy
            + 0.3 * (1 - self.loyalty)
            + 0.2 * (1 - avg_trust)
            + 0.1 * position_stress
        )


@dataclass
class EnergyAllocation:
    """体力分配决策"""
    work: float
    conflict: float
    comm: float

    def validate(self) -> bool:
        """验证分配是否合法"""
        if not (20 <= self.work <= 80):
            return False
        if not (0 <= self.conflict <= 40):
            return False
        if not (5 <= self.comm <= 30):
            return False
        if self.work + self.conflict + self.comm > 100:
            return False
        return True


@dataclass
class Agent:
    """完整Agent模型"""
    id: str
    name: str
    description: str
    personality: Personality
    state: AgentState = field(default_factory=AgentState)
    trust_matrix_row: Dict[str, float] = field(default_factory=dict)  # 对其他Agent的信任

    # 位置信息
    position: str = "edge"  # core, middle, edge
    level: int = 0          # 层级（树形架构）
    centrality: float = 0.0

    # 内鬼相关
    traitor_tendency: float = 0.0
    is_active_traitor: bool = False
    private_account: float = 0.0  # 挪用的资源

    def __post_init__(self):
        """初始化后处理"""
        # 初始化忠诚度为忠诚度基准
        self.state.loyalty = self.personality.loyalty_base

        # 计算内鬼倾向
        self.traitor_tendency = self.personality.calculate_traitor_tendency()

        # 初始化认知熵（基于韧性）
        self.state.cognitive_entropy = 0.1 + 0.05 * (1 - self.personality.resilience)

    def initialize_trust(self, agent_ids: List[str]):
        """初始化信任矩阵行（使用配置参数）"""
        trust_config = default_config.trust

        for agent_id in agent_ids:
            if agent_id == self.id:
                self.trust_matrix_row[agent_id] = 1.0
            else:
                # 基于社交性的初始信任
                base_trust = (
                    trust_config.initial_trust_base +
                    trust_config.initial_trust_sociability_weight *
                    (self.personality.sociability - 0.5)
                )
                self.trust_matrix_row[agent_id] = base_trust

    def get_avg_trust(self, exclude_self: bool = True) -> float:
        """计算平均信任度"""
        trusts = [v for k, v in self.trust_matrix_row.items()
                  if not exclude_self or k != self.id]
        return sum(trusts) / len(trusts) if trusts else 0.5

    def calculate_efficiency(self, connected_trusts: List[float] = None) -> float:
        """
        计算转化率
        η = 0.8 × (0.8 + 0.2×智力) × (0.5 + 0.5×忠诚度) × (1 - 0.5×认知熵) × 平均信任
        """
        # 智力因子
        eta_int = 0.8 + 0.2 * self.personality.intelligence

        # 忠诚度因子
        eta_loyal = 0.5 + 0.5 * self.state.loyalty

        # 认知熵因子
        eta_entropy = 1 - 0.5 * self.state.cognitive_entropy

        # 信任因子
        if connected_trusts:
            eta_trust = sum(connected_trusts) / len(connected_trusts)
        else:
            eta_trust = self.get_avg_trust()

        # 综合转化率
        eta = 0.8 * eta_int * eta_loyal * eta_entropy * eta_trust

        # 边界约束
        self.state.efficiency = max(0.16, min(1.0, eta))
        return self.state.efficiency

    def update_trust(self, target_id: str, observed: float, expected: float,
                     co_activation: float = 0.0):
        """
        更新信任值（含衰减，使用配置参数）
        T(t+1) = T(t) × (1-decay_rate) + learning_rate×(观察-期望) + hebbian×共激活
        """
        if target_id not in self.trust_matrix_row:
            return

        trust_config = default_config.trust
        current = self.trust_matrix_row[target_id]

        # 衰减
        decayed = current * (1 - trust_config.decay_rate)

        # 学习更新
        learning_rate = (
            trust_config.learning_rate_base +
            trust_config.learning_rate_sociability_weight *
            self.personality.sociability
        )
        delta = learning_rate * (observed - expected)

        # Hebbian项
        hebbian = trust_config.hebbian_coefficient * co_activation

        # 更新
        new_trust = decayed + delta + hebbian
        self.trust_matrix_row[target_id] = max(0.0, min(1.0, new_trust))

    def update_loyalty(self, delta: float, regression: bool = True):
        """
        更新忠诚度
        L(t+1) = L(t) + delta
        然后向基准回归
        """
        self.state.loyalty += delta
        self.state.loyalty = max(0.0, min(1.0, self.state.loyalty))

        # 向基准回归
        if regression:
            self.state.loyalty = (
                0.9 * self.state.loyalty +
                0.1 * self.personality.loyalty_base
            )

    def update_cognitive_entropy(self, delta: float):
        """更新认知熵"""
        # 应用韧性衰减
        delta *= (1 - 0.5 * self.personality.resilience)

        self.state.cognitive_entropy += delta
        self.state.cognitive_entropy = max(0.0, min(1.0, self.state.cognitive_entropy))

    def calculate_activation(self) -> float:
        """
        计算激活值
        Activation = 0.4×L + 0.3×(E/100) - 0.3×H
        """
        return (
            0.4 * self.state.loyalty +
            0.3 * (self.state.energy / 100) -
            0.3 * self.state.cognitive_entropy
        )

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "personality": {
                "authority": self.personality.authority,
                "selfishness": self.personality.selfishness,
                "resilience": self.personality.resilience,
                "altruism": self.personality.altruism,
                "sociability": self.personality.sociability,
                "risk_appetite": self.personality.risk_appetite,
                "intelligence": self.personality.intelligence,
                "loyalty_base": self.personality.loyalty_base
            },
            "state": {
                "energy": self.state.energy,
                "cognitive_entropy": self.state.cognitive_entropy,
                "loyalty": self.state.loyalty,
                "contribution": self.state.contribution,
                "efficiency": self.state.efficiency,
                "energy_work": self.state.energy_work,
                "energy_conflict": self.state.energy_conflict,
                "energy_comm": self.state.energy_comm
            },
            "trust_matrix_row": dict(self.trust_matrix_row),
            "position": self.position,
            "level": self.level,
            "centrality": self.centrality,
            "traitor_tendency": self.traitor_tendency,
            "is_active_traitor": self.is_active_traitor
        }