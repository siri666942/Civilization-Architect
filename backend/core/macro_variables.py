"""
宏观变量计算

计算能级、向心力、信息保真度、社会资本、最终产出
"""

from typing import List, Dict
import numpy as np

from backend.models.agent import Agent, ArchitectureType
from backend.models.architecture import ArchitectureConfig
from backend.common.config import GameConfig, default_config


class MacroVariableCalculator:
    """宏观变量计算器"""

    @staticmethod
    def calculate_energy_level(agents: List[Agent]) -> float:
        """
        计算能级
        E_level = (1/N) × Σ (E_i/100) × η_i
        """
        if not agents:
            return 0.0

        total = 0.0
        for agent in agents:
            total += (agent.state.energy / 100) * agent.state.efficiency

        return total / len(agents)

    @staticmethod
    def calculate_centripetal_force(agents: List[Agent]) -> float:
        """
        计算向心力
        C = 平均忠诚度 × (1 - min(Var(L)/0.25, 1))

        注：使用0.25作为归一化分母，避免过于敏感
        """
        if not agents:
            return 0.0

        # 计算平均忠诚度
        loyalties = [a.state.loyalty for a in agents]
        avg_loyalty = np.mean(loyalties)

        # 计算方差
        variance = np.var(loyalties)

        # 归一化方差（使用0.25作为分母，避免过于敏感）
        normalized_variance = min(variance / 0.25, 1.0)

        # 向心力（使用二次衰减，更平滑）
        cohesion = avg_loyalty * (1 - normalized_variance ** 1.5)

        return max(0.0, cohesion)

    @staticmethod
    def calculate_fidelity(agents: List[Agent],
                          config: ArchitectureConfig) -> float:
        """
        计算信息保真度
        F = max(0.5, F_base × Trust_factor × Entropy_factor)

        注：保真度下限设为0.5，避免过低
        """
        if not agents:
            return 0.5

        # 基础保真度
        base_fidelity = config.base_fidelity

        # 信任因子（提高到基准0.6）
        avg_trust = np.mean([
            agent.get_avg_trust() for agent in agents
        ])
        trust_factor = 0.6 + 0.4 * avg_trust  # 最小0.6

        # 认知熵因子
        avg_entropy = np.mean([
            agent.state.cognitive_entropy for agent in agents
        ])
        entropy_factor = 1 - 0.3 * avg_entropy

        fidelity = base_fidelity * trust_factor * entropy_factor

        # 保真度下限
        return max(0.5, fidelity)

    @staticmethod
    def calculate_social_capital(agents: List[Agent],
                                 config: ArchitectureConfig) -> float:
        """
        计算社会资本
        S = 平均信任 + 0.2 × 边密度
        """
        if not agents:
            return 0.0

        # 平均信任
        avg_trust = np.mean([
            agent.get_avg_trust() for agent in agents
        ])

        # 密度因子
        density_factor = 0.2 * config.edge_density

        return avg_trust + density_factor

    @staticmethod
    def calculate_average_efficiency(agents: List[Agent]) -> float:
        """计算平均效率"""
        if not agents:
            return 0.0
        return np.mean([a.state.efficiency for a in agents])


class ProductionCalculator:
    """产出计算器"""

    @staticmethod
    def calculate_cycle_output(agents: List[Agent],
                               config: ArchitectureConfig,
                               game_config: GameConfig = None) -> Dict[str, float]:
        """
        计算单循环产出

        P_cycle = Σ(E_work × η × PositionBonus)
                  × K_energy × K_cohesion × K_fidelity × K_social × K_arch
        """
        if game_config is None:
            game_config = default_config

        prod_config = game_config.production

        # 基础产出
        base_output = 0.0

        for agent in agents:
            # 位置加成（星形架构核心节点有加成）
            position_bonus = 1.0
            if config.architecture_type == ArchitectureType.STAR and agent.position == "core":
                position_bonus = prod_config.star_core_position_bonus

            # 计算贡献
            contribution = (
                agent.state.energy_work *
                agent.state.efficiency *
                position_bonus
            )
            base_output += contribution

            # 更新Agent的贡献累计
            agent.state.contribution += contribution

        # 计算宏观变量
        energy_level = MacroVariableCalculator.calculate_energy_level(agents)
        cohesion = MacroVariableCalculator.calculate_centripetal_force(agents)
        fidelity = MacroVariableCalculator.calculate_fidelity(agents, config)
        social_capital = MacroVariableCalculator.calculate_social_capital(agents, config)

        # 计算修正系数（使用配置参数）
        k_energy = prod_config.k_energy_base + prod_config.k_energy_weight * energy_level
        k_cohesion = prod_config.k_cohesion_base + prod_config.k_cohesion_weight * cohesion
        k_fidelity = prod_config.k_fidelity_base + prod_config.k_fidelity_weight * fidelity
        k_social = prod_config.k_social_base + prod_config.k_social_weight * social_capital
        k_arch = config.efficiency_coefficient

        # 最终产出
        cycle_output = base_output * k_energy * k_cohesion * k_fidelity * k_social * k_arch

        # 应用循环效率补偿（低通达度架构获得补偿）
        cycle_efficiency_bonus = ProductionCalculator.calculate_cycle_efficiency_bonus(
            config, prod_config.cycle_efficiency_bonus_weight
        )
        cycle_output *= cycle_efficiency_bonus

        return {
            "base_output": base_output,
            "cycle_output": cycle_output,
            "cycle_efficiency_bonus": cycle_efficiency_bonus,
            "energy_level": energy_level,
            "cohesion": cohesion,
            "fidelity": fidelity,
            "social_capital": social_capital,
            "modifiers": {
                "k_energy": k_energy,
                "k_cohesion": k_cohesion,
                "k_fidelity": k_fidelity,
                "k_social": k_social,
                "k_arch": k_arch
            }
        }

    @staticmethod
    def calculate_cycle_efficiency_bonus(config: ArchitectureConfig,
                                         weight: float = 0.5) -> float:
        """
        计算循环效率补偿
        低通达度架构获得补偿

        CycleEfficiencyBonus = 1 + weight × (1 - R_normalized)
        """
        r_normalized = config.reachability  # 因为网状R=1.0
        return 1 + weight * (1 - r_normalized)


def calculate_all_macro_variables(agents: List[Agent],
                                  config: ArchitectureConfig) -> Dict[str, float]:
    """计算所有宏观变量"""
    return {
        "energy_level": MacroVariableCalculator.calculate_energy_level(agents),
        "cohesion": MacroVariableCalculator.calculate_centripetal_force(agents),
        "fidelity": MacroVariableCalculator.calculate_fidelity(agents, config),
        "social_capital": MacroVariableCalculator.calculate_social_capital(agents, config),
        "average_efficiency": MacroVariableCalculator.calculate_average_efficiency(agents)
    }
