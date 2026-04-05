"""
游戏配置管理

集中管理所有可调参数，支持配置文件加载和参数验证
这是一个独立模块，不依赖其他backend模块，避免循环导入
"""

from dataclasses import dataclass, field
from typing import Optional
import json


@dataclass
class TraitorConfig:
    """内鬼机制配置"""
    # 内鬼激活阈值
    activate_tendency_threshold: float = 0.4

    # 激活概率乘数
    activate_probability_multiplier: float = 0.5

    # 机会因子基础值
    opportunity_base: float = 0.3

    # 机会因子-信任权重
    opportunity_trust_weight: float = 0.2

    # 机会因子-认知熵权重
    opportunity_entropy_weight: float = 0.2

    # 消极怠工基础比例
    slack_base_rate: float = 0.3

    # 消极怠工倾向乘数
    slack_tendency_multiplier: float = 0.4

    # 资源挪用比例乘数
    steal_rate_multiplier: float = 0.1

    # 提示词注入强度
    injection_base_strength: float = 0.5

    # 提示词注入忠诚度影响
    injection_loyalty_delta: float = 0.08


@dataclass
class EnergyConfig:
    """能量分配配置"""
    # 默认分配
    default_work: float = 50.0
    default_conflict: float = 10.0
    default_comm: float = 20.0

    # 性格调整阈值
    personality_threshold: float = 0.6

    # 高私心倾向工作增量
    high_selfishness_work_bonus: float = 10.0
    high_selfishness_conflict_bonus: float = 5.0

    # 高利他性工作增量
    high_altruism_work_bonus: float = 15.0

    # 高权威感度通讯增量
    high_authority_comm_bonus: float = 10.0

    # 边界约束
    work_min: float = 20.0
    work_max: float = 80.0
    conflict_min: float = 0.0
    conflict_max: float = 40.0
    comm_min: float = 5.0
    comm_max: float = 30.0


@dataclass
class StateUpdateConfig:
    """状态更新配置"""
    # 认知熵自然恢复率
    entropy_recovery_base: float = 0.02

    # 心理负担阈值
    mental_load_threshold: float = 0.6

    # 高心理负担认知熵增量
    high_load_entropy_increase: float = 0.02

    # 位置压力值
    core_position_stress: float = 0.5
    middle_position_stress: float = 0.3
    edge_position_stress: float = 0.1


@dataclass
class TrustConfig:
    """信任矩阵配置"""
    # 初始信任基准
    initial_trust_base: float = 0.6

    # 初始信任社交性权重
    initial_trust_sociability_weight: float = 0.1

    # 衰减率
    decay_rate: float = 0.02

    # 学习率基础值
    learning_rate_base: float = 0.1

    # 学习率社交性权重
    learning_rate_sociability_weight: float = 0.1

    # Hebbian系数
    hebbian_coefficient: float = 0.02


@dataclass
class PersonalityConfig:
    """性格生成配置"""
    # 多样性检查最大尝试次数
    diversity_max_attempts: int = 100

    # 多样性阈值
    diversity_threshold: float = 0.5

    # 相似性阈值
    similarity_threshold: float = 0.85


@dataclass
class ArchitectureConfigParams:
    """架构配置参数"""
    # 星形架构参数
    star_structure_coefficient: float = 1.5
    star_robustness_coefficient: float = 0.1
    star_base_fidelity: float = 0.9
    star_efficiency_coefficient: float = 1.3

    # 树形架构参数
    tree_structure_coefficient: float = 0.8
    tree_robustness_coefficient: float = 0.3
    tree_base_fidelity: float = 0.7
    tree_efficiency_coefficient: float = 1.0

    # 网状架构参数
    mesh_structure_coefficient: float = 1.0
    mesh_robustness_coefficient: float = 0.9
    mesh_base_fidelity: float = 0.85
    mesh_efficiency_coefficient: float = 1.0

    # 部落架构参数
    tribal_structure_coefficient: float = 0.6
    tribal_robustness_coefficient: float = 0.6
    tribal_base_fidelity: float = 0.6
    tribal_efficiency_coefficient: float = 1.1

    # 部落间弱连接数
    tribal_inter_connections: int = 2


@dataclass
class ProductionConfig:
    """产出计算配置"""
    # 星形架构核心节点位置加成
    star_core_position_bonus: float = 1.5

    # 能级系数
    k_energy_base: float = 0.7
    k_energy_weight: float = 0.3

    # 向心力系数
    k_cohesion_base: float = 0.5
    k_cohesion_weight: float = 0.5

    # 保真度系数
    k_fidelity_base: float = 0.8
    k_fidelity_weight: float = 0.2

    # 社会资本系数
    k_social_base: float = 0.7
    k_social_weight: float = 0.3

    # 循环效率补偿系数
    cycle_efficiency_bonus_weight: float = 0.5


@dataclass
class GameConfig:
    """游戏总配置"""
    # 子配置
    traitor: TraitorConfig = field(default_factory=TraitorConfig)
    energy: EnergyConfig = field(default_factory=EnergyConfig)
    state_update: StateUpdateConfig = field(default_factory=StateUpdateConfig)
    trust: TrustConfig = field(default_factory=TrustConfig)
    personality: PersonalityConfig = field(default_factory=PersonalityConfig)
    architecture: ArchitectureConfigParams = field(default_factory=ArchitectureConfigParams)
    production: ProductionConfig = field(default_factory=ProductionConfig)

    # 游戏参数
    default_num_civilizations: int = 3
    default_agents_per_civilization: int = 10
    default_total_rounds: int = 10

    # 随机种子
    default_seed: Optional[int] = None

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "traitor": {
                "activate_tendency_threshold": self.traitor.activate_tendency_threshold,
                "activate_probability_multiplier": self.traitor.activate_probability_multiplier,
                "opportunity_base": self.traitor.opportunity_base,
                "opportunity_trust_weight": self.traitor.opportunity_trust_weight,
                "opportunity_entropy_weight": self.traitor.opportunity_entropy_weight,
                "slack_base_rate": self.traitor.slack_base_rate,
                "slack_tendency_multiplier": self.traitor.slack_tendency_multiplier,
                "steal_rate_multiplier": self.traitor.steal_rate_multiplier,
                "injection_base_strength": self.traitor.injection_base_strength,
                "injection_loyalty_delta": self.traitor.injection_loyalty_delta
            },
            "energy": {
                "default_work": self.energy.default_work,
                "default_conflict": self.energy.default_conflict,
                "default_comm": self.energy.default_comm,
                "personality_threshold": self.energy.personality_threshold,
                "high_selfishness_work_bonus": self.energy.high_selfishness_work_bonus,
                "high_selfishness_conflict_bonus": self.energy.high_selfishness_conflict_bonus,
                "high_altruism_work_bonus": self.energy.high_altruism_work_bonus,
                "high_authority_comm_bonus": self.energy.high_authority_comm_bonus
            },
            "state_update": {
                "entropy_recovery_base": self.state_update.entropy_recovery_base,
                "mental_load_threshold": self.state_update.mental_load_threshold,
                "high_load_entropy_increase": self.state_update.high_load_entropy_increase,
                "core_position_stress": self.state_update.core_position_stress,
                "middle_position_stress": self.state_update.middle_position_stress,
                "edge_position_stress": self.state_update.edge_position_stress
            },
            "trust": {
                "initial_trust_base": self.trust.initial_trust_base,
                "initial_trust_sociability_weight": self.trust.initial_trust_sociability_weight,
                "decay_rate": self.trust.decay_rate,
                "learning_rate_base": self.trust.learning_rate_base,
                "learning_rate_sociability_weight": self.trust.learning_rate_sociability_weight,
                "hebbian_coefficient": self.trust.hebbian_coefficient
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'GameConfig':
        """从字典创建配置"""
        config = cls()

        if "traitor" in data:
            for key, value in data["traitor"].items():
                if hasattr(config.traitor, key):
                    setattr(config.traitor, key, value)

        if "energy" in data:
            for key, value in data["energy"].items():
                if hasattr(config.energy, key):
                    setattr(config.energy, key, value)

        if "state_update" in data:
            for key, value in data["state_update"].items():
                if hasattr(config.state_update, key):
                    setattr(config.state_update, key, value)

        if "trust" in data:
            for key, value in data["trust"].items():
                if hasattr(config.trust, key):
                    setattr(config.trust, key, value)

        return config

    def save_to_file(self, filepath: str):
        """保存配置到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'GameConfig':
        """从文件加载配置"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


# 默认配置实例（全局单例）
default_config = GameConfig()
