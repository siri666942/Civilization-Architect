"""
核心游戏引擎

管理游戏循环、状态更新、产出结算
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
import json
from datetime import datetime
import numpy as np

from backend.models.agent import Agent, ArchitectureType, TraitorBehavior
from backend.models.architecture import create_architecture, ArchitectureConfig, ArchitectureAnalyzer
from backend.core.god_agent import initialize_agents
from backend.core.macro_variables import (
    ProductionCalculator,
    calculate_all_macro_variables
)
from backend.common.config import GameConfig, default_config


@dataclass
class GameState:
    """游戏状态"""
    civilization_id: str
    round: int = 1
    cycle: int = 0
    total_output: float = 0.0
    cycle_outputs: List[float] = field(default_factory=list)

    # 宏观变量历史
    energy_level_history: List[float] = field(default_factory=list)
    cohesion_history: List[float] = field(default_factory=list)
    fidelity_history: List[float] = field(default_factory=list)
    social_capital_history: List[float] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "civilization_id": self.civilization_id,
            "round": self.round,
            "cycle": self.cycle,
            "total_output": self.total_output,
            "cycle_outputs": self.cycle_outputs,
            "energy_level_history": self.energy_level_history,
            "cohesion_history": self.cohesion_history,
            "fidelity_history": self.fidelity_history,
            "social_capital_history": self.social_capital_history
        }


@dataclass
class TraitorEvent:
    """内鬼事件"""
    agent_id: str
    cycle: int
    behavior: TraitorBehavior
    target_id: Optional[str]
    effect: Dict
    detected: bool = False


class Civilization:
    """文明类：管理一个完整的文明"""

    def __init__(self, civilization_id: str, architecture_type: ArchitectureType,
                 agents: List[Agent], config: ArchitectureConfig):
        self.civilization_id = civilization_id
        self.architecture_type = architecture_type
        self.agents = agents
        self.config = config
        self.state = GameState(civilization_id=civilization_id)
        self.traitor_events: List[TraitorEvent] = []

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取指定Agent"""
        for agent in self.agents:
            if agent.id == agent_id:
                return agent
        return None

    def get_connected_agents(self, agent_id: str) -> List[Agent]:
        """获取与指定Agent有连接的所有Agent"""
        agent_idx = -1
        for i, agent in enumerate(self.agents):
            if agent.id == agent_id:
                agent_idx = i
                break

        if agent_idx < 0:
            return []

        connected = []
        adj = self.config.adjacency_matrix

        for j, agent in enumerate(self.agents):
            if adj[agent_idx, j] > 0 or adj[j, agent_idx] > 0:
                connected.append(agent)

        return connected

    def to_dict(self) -> dict:
        return {
            "civilization_id": self.civilization_id,
            "architecture_type": self.architecture_type.value,
            "agents": [a.to_dict() for a in self.agents],
            "state": self.state.to_dict(),
            "config": {
                "reachability": self.config.reachability,
                "average_path_length": self.config.average_path_length,
                "cycles_per_round": self.config.cycles_per_round,
                "efficiency_coefficient": self.config.efficiency_coefficient,
                "robustness_coefficient": self.config.robustness_coefficient
            }
        }


class GameEngine:
    """
    游戏引擎

    管理完整的游戏流程：
    1. 初始化文明
    2. 执行回合和循环
    3. 更新状态
    4. 计算产出
    5. 判定胜负
    """

    def __init__(self, num_civilizations: int = None,
                 architecture_types: List[ArchitectureType] = None,
                 agents_per_civilization: int = None,
                 total_rounds: int = None,
                 seed: Optional[int] = None,
                 config: GameConfig = None):
        """
        初始化游戏引擎

        Args:
            num_civilizations: 文明数量
            architecture_types: 各文明使用的架构类型
            agents_per_civilization: 每个文明的Agent数量
            total_rounds: 总回合数
            seed: 随机种子
            config: 游戏配置
        """
        # 使用配置或默认值
        self.config = config or default_config

        self.num_civilizations = num_civilizations or self.config.default_num_civilizations
        self.agents_per_civ = agents_per_civilization or self.config.default_agents_per_civilization
        self.total_rounds = total_rounds or self.config.default_total_rounds

        # 初始化随机数生成器
        self.seed = seed if seed is not None else self.config.default_seed
        self.rng = np.random.default_rng(self.seed)

        # 默认架构类型
        if architecture_types is None:
            architecture_types = [
                ArchitectureType.STAR,
                ArchitectureType.TREE,
                ArchitectureType.MESH
            ][:self.num_civilizations]

        self.architecture_types = architecture_types
        self.civilizations: List[Civilization] = []

        # 初始化完成标志
        self.initialized = False

    def initialize(self):
        """初始化游戏：创建所有文明"""
        for i in range(self.num_civilizations):
            civ_id = f"CIV-{i+1:03d}"
            arch_type = self.architecture_types[i]

            # 创建Agent（使用引擎的随机数生成器）
            agents = self._initialize_agents(
                n=self.agents_per_civ,
                civilization_id=civ_id
            )

            # 初始化信任矩阵
            agent_ids = [a.id for a in agents]
            for agent in agents:
                agent.initialize_trust(agent_ids)

            # 创建架构（动态生成）
            config = create_architecture(arch_type, agent_ids)

            # 分配Agent位置
            agents = ArchitectureAnalyzer.assign_agent_positions(config, agents)

            # 计算初始效率
            for agent in agents:
                connected = self._get_connected_trusts(agent, config, agents)
                agent.calculate_efficiency(connected)

            # 创建文明
            civ = Civilization(civ_id, arch_type, agents, config)
            self.civilizations.append(civ)

        self.initialized = True

    def _initialize_agents(self, n: int, civilization_id: str) -> List[Agent]:
        """
        初始化Agent（使用引擎的随机数生成器）

        Args:
            n: Agent数量
            civilization_id: 文明ID

        Returns:
            Agent列表
        """
        from backend.core.god_agent import GodAgent

        # 使用引擎的随机种子为每个文明创建独立的种子
        civ_seed = self.rng.integers(0, 2**31) if self.seed is not None else None
        god = GodAgent(seed=civ_seed)

        return god.generate_agents(n, civilization_id)

    def _get_connected_trusts(self, agent: Agent, config: ArchitectureConfig,
                              agents: List[Agent]) -> List[float]:
        """获取连接Agent对目标Agent的信任"""
        agent_idx = agents.index(agent)
        adj = config.adjacency_matrix
        trusts = []

        for j, other in enumerate(agents):
            if adj[j, agent_idx] > 0:  # j 可以向 agent 发送信息
                trusts.append(other.trust_matrix_row.get(agent.id, 0.5))

        return trusts if trusts else [0.5]

    def run_round(self, civilization: Civilization):
        """执行一个回合"""
        cycles = civilization.config.cycles_per_round

        for cycle in range(cycles):
            civilization.state.cycle += 1
            self.run_cycle(civilization)

        civilization.state.round += 1
        civilization.state.cycle = 0  # 重置循环计数

    def run_cycle(self, civilization: Civilization):
        """执行一个循环"""
        agents = civilization.agents
        config = civilization.config

        # 1. 重置体力
        for agent in agents:
            agent.state.reset_energy()

        # 2. 能量分配决策（使用配置参数）
        self._auto_allocate_energy(agents)

        # 3. 模拟内鬼行为（如果有内鬼）
        self._process_traitor_actions(civilization)

        # 4. 更新状态
        self._update_agent_states(civilization)

        # 5. 计算产出
        output = ProductionCalculator.calculate_cycle_output(agents, config, self.config)

        civilization.state.total_output += output["cycle_output"]
        civilization.state.cycle_outputs.append(output["cycle_output"])

        # 记录宏观变量
        macro = calculate_all_macro_variables(agents, config)
        civilization.state.energy_level_history.append(macro["energy_level"])
        civilization.state.cohesion_history.append(macro["cohesion"])
        civilization.state.fidelity_history.append(macro["fidelity"])
        civilization.state.social_capital_history.append(macro["social_capital"])

    def _auto_allocate_energy(self, agents: List[Agent]):
        """
        自动能量分配（使用配置参数）

        基于性格属性决定分配
        """
        energy_config = self.config.energy

        for agent in agents:
            # 基础分配
            work = energy_config.default_work
            conflict = energy_config.default_conflict
            comm = energy_config.default_comm

            # 根据性格调整
            # 高私心倾向：更多工作或内斗
            if agent.personality.selfishness > energy_config.personality_threshold:
                work += energy_config.high_selfishness_work_bonus
                conflict += energy_config.high_selfishness_conflict_bonus

            # 高利他性：更多工作
            if agent.personality.altruism > energy_config.personality_threshold:
                work += energy_config.high_altruism_work_bonus

            # 高权威感度：更多通讯（汇报）
            if agent.personality.authority > energy_config.personality_threshold:
                comm += energy_config.high_authority_comm_bonus

            # 确保在边界内
            work = max(energy_config.work_min, min(energy_config.work_max, work))
            conflict = max(energy_config.conflict_min, min(energy_config.conflict_max, conflict))
            comm = max(energy_config.comm_min, min(energy_config.comm_max, comm))

            # 如果超过100，按比例缩减
            total = work + conflict + comm
            if total > 100:
                scale = 100 / total
                work *= scale
                conflict *= scale
                comm *= scale

            agent.state.energy_work = work
            agent.state.energy_conflict = conflict
            agent.state.energy_comm = comm

    def _process_traitor_actions(self, civilization: Civilization):
        """处理内鬼行为（使用配置参数）"""
        agents = civilization.agents
        traitor_config = self.config.traitor

        for agent in agents:
            # 检查是否激活内鬼
            if (agent.traitor_tendency > traitor_config.activate_tendency_threshold
                and not agent.is_active_traitor):
                # 计算激活概率（使用配置参数）
                opportunity = (
                    traitor_config.opportunity_base +
                    traitor_config.opportunity_trust_weight * (1 - agent.get_avg_trust()) +
                    traitor_config.opportunity_entropy_weight * agent.state.cognitive_entropy
                )
                p_activate = agent.traitor_tendency * (1 - agent.state.loyalty) * opportunity

                # 使用引擎的随机数生成器
                if self.rng.random() < p_activate * traitor_config.activate_probability_multiplier:
                    agent.is_active_traitor = True

            if agent.is_active_traitor:
                # 执行内鬼行为
                self._execute_traitor_behavior(agent, civilization)

    def _execute_traitor_behavior(self, traitor: Agent, civilization: Civilization):
        """执行内鬼行为（使用配置参数）"""
        traitor_config = self.config.traitor

        # 使用引擎的随机数生成器选择行为
        behaviors = [
            TraitorBehavior.SLACK,    # 最常见
            TraitorBehavior.TAMPER,
            TraitorBehavior.STEAL,
            TraitorBehavior.INJECT
        ]

        behavior = behaviors[self.rng.integers(0, len(behaviors))]

        if behavior == TraitorBehavior.SLACK:
            # 消极怠工：减少产出
            slack_rate = (traitor_config.slack_base_rate +
                         traitor_config.slack_tendency_multiplier * traitor.traitor_tendency)
            traitor.state.energy_work *= (1 - slack_rate)

        elif behavior == TraitorBehavior.STEAL:
            # 资源挪用
            steal_rate = (traitor_config.steal_rate_multiplier *
                         traitor.centrality * traitor.traitor_tendency)
            stolen = traitor.state.contribution * steal_rate
            traitor.private_account += stolen
            traitor.state.contribution -= stolen

        elif behavior == TraitorBehavior.INJECT:
            # 提示词注入：降低目标忠诚度
            connected = civilization.get_connected_agents(traitor.id)
            if connected:
                target = connected[self.rng.integers(0, len(connected))]
                injection_strength = (traitor_config.injection_base_strength *
                                     target.trust_matrix_row.get(traitor.id, 0.5))
                delta = (-traitor_config.injection_loyalty_delta *
                        injection_strength * (1 - target.personality.resilience))
                target.update_loyalty(delta)

        # 记录事件
        event = TraitorEvent(
            agent_id=traitor.id,
            cycle=civilization.state.cycle,
            behavior=behavior,
            target_id=None,
            effect={"type": behavior.value}
        )
        civilization.traitor_events.append(event)

    def _update_agent_states(self, civilization: Civilization):
        """更新Agent状态（使用配置参数）"""
        agents = civilization.agents
        state_config = self.config.state_update

        for agent in agents:
            # 认知熵自然恢复
            recovery = state_config.entropy_recovery_base * (1 - agent.state.cognitive_entropy)
            agent.update_cognitive_entropy(-recovery)

            # 计算信任平均值
            avg_trust = agent.get_avg_trust()

            # 心理负担
            position_stress = {
                "core": state_config.core_position_stress,
                "middle": state_config.middle_position_stress,
                "edge": state_config.edge_position_stress
            }.get(agent.position, state_config.edge_position_stress)

            mental_load = agent.state.calculate_mental_load(avg_trust, position_stress)

            # 高心理负担增加认知熵
            if mental_load > state_config.mental_load_threshold:
                agent.update_cognitive_entropy(state_config.high_load_entropy_increase)

            # 重新计算效率
            connected = self._get_connected_trusts(
                agent, civilization.config, agents
            )
            agent.calculate_efficiency(connected)

    def run_full_game(self) -> Dict:
        """运行完整游戏"""
        if not self.initialized:
            self.initialize()

        # 运行所有回合
        for round_num in range(self.total_rounds):
            for civ in self.civilizations:
                self.run_round(civ)

        # 返回结果
        return self.get_final_results()

    def get_final_results(self) -> Dict:
        """获取最终结果"""
        results = []

        for civ in self.civilizations:
            results.append({
                "civilization_id": civ.civilization_id,
                "architecture_type": civ.architecture_type.value,
                "total_output": civ.state.total_output,
                "final_energy_level": civ.state.energy_level_history[-1] if civ.state.energy_level_history else 0,
                "final_cohesion": civ.state.cohesion_history[-1] if civ.state.cohesion_history else 0,
                "final_fidelity": civ.state.fidelity_history[-1] if civ.state.fidelity_history else 0,
                "final_social_capital": civ.state.social_capital_history[-1] if civ.state.social_capital_history else 0,
                "traitor_count": sum(1 for a in civ.agents if a.is_active_traitor),
                "total_cycles": len(civ.state.cycle_outputs)
            })

        # 排序
        results.sort(key=lambda x: x["total_output"], reverse=True)

        for i, r in enumerate(results):
            r["rank"] = i + 1

        return {
            "rankings": results,
            "civilizations": [civ.to_dict() for civ in self.civilizations]
        }


def create_game(num_civilizations: int = None,
                architecture_types: List[ArchitectureType] = None,
                total_rounds: int = None,
                seed: int = None,
                config: GameConfig = None) -> GameEngine:
    """创建游戏实例"""
    return GameEngine(
        num_civilizations=num_civilizations,
        architecture_types=architecture_types,
        total_rounds=total_rounds,
        seed=seed,
        config=config
    )
