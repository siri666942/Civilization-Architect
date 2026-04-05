"""
模拟分析器

深入分析模拟结果，发现问题，验证机制
"""

from typing import List, Dict
import numpy as np
import json

from core.engine import GameEngine, Civilization
from models.agent import ArchitectureType


def analyze_civilization_detail(civ: Civilization) -> Dict:
    """详细分析单个文明"""
    agents = civ.agents

    # 性格分布
    personalities = {
        "avg_selfishness": np.mean([a.personality.selfishness for a in agents]),
        "avg_altruism": np.mean([a.personality.altruism for a in agents]),
        "avg_loyalty_base": np.mean([a.personality.loyalty_base for a in agents]),
        "avg_resilience": np.mean([a.personality.resilience for a in agents])
    }

    # 状态分布
    states = {
        "avg_loyalty": np.mean([a.state.loyalty for a in agents]),
        "std_loyalty": np.std([a.state.loyalty for a in agents]),
        "avg_entropy": np.mean([a.state.cognitive_entropy for a in agents]),
        "avg_efficiency": np.mean([a.state.efficiency for a in agents]),
        "avg_trust": np.mean([a.get_avg_trust() for a in agents])
    }

    # 内鬼分析
    traitor_analysis = {
        "high_tendency_count": sum(1 for a in agents if a.traitor_tendency > 0.6),
        "active_traitors": sum(1 for a in agents if a.is_active_traitor),
        "avg_traitor_tendency": np.mean([a.traitor_tendency for a in agents])
    }

    # 架构信息
    arch_info = {
        "type": civ.architecture_type.value,
        "cycles_per_round": civ.config.cycles_per_round,
        "reachability": civ.config.reachability,
        "efficiency_coefficient": civ.config.efficiency_coefficient,
        "robustness": civ.config.robustness_coefficient
    }

    # 产出分析
    cycle_outputs = civ.state.cycle_outputs
    output_analysis = {
        "total_output": sum(cycle_outputs),
        "avg_per_cycle": np.mean(cycle_outputs) if cycle_outputs else 0,
        "std_per_cycle": np.std(cycle_outputs) if cycle_outputs else 0,
        "num_cycles": len(cycle_outputs)
    }

    # 宏观变量趋势
    macro_trends = {
        "energy_level_start": civ.state.energy_level_history[0] if civ.state.energy_level_history else 0,
        "energy_level_end": civ.state.energy_level_history[-1] if civ.state.energy_level_history else 0,
        "cohesion_start": civ.state.cohesion_history[0] if civ.state.cohesion_history else 0,
        "cohesion_end": civ.state.cohesion_history[-1] if civ.state.cohesion_history else 0,
        "fidelity_start": civ.state.fidelity_history[0] if civ.state.fidelity_history else 0,
        "fidelity_end": civ.state.fidelity_history[-1] if civ.state.fidelity_history else 0
    }

    return {
        "civilization_id": civ.civilization_id,
        "personalities": personalities,
        "states": states,
        "traitor_analysis": traitor_analysis,
        "arch_info": arch_info,
        "output_analysis": output_analysis,
        "macro_trends": macro_trends
    }


def diagnose_issues(game: GameEngine) -> List[Dict]:
    """诊断机制问题"""
    issues = []

    for civ in game.civilizations:
        analysis = analyze_civilization_detail(civ)

        # 问题1：向心力过低
        if analysis["macro_trends"]["cohesion_end"] < 0.2:
            issues.append({
                "type": "LOW_COHESION",
                "civilization": civ.civilization_id,
                "severity": "WARNING",
                "value": analysis["macro_trends"]["cohesion_end"],
                "expected": "> 0.5",
                "possible_causes": [
                    "忠诚度方差归一化分母过大",
                    "忠诚度变化幅度不够",
                    "忠诚度向基准回归过快"
                ]
            })

        # 问题2：保真度过低
        if analysis["macro_trends"]["fidelity_end"] < 0.5:
            issues.append({
                "type": "LOW_FIDELITY",
                "civilization": civ.civilization_id,
                "severity": "WARNING",
                "value": analysis["macro_trends"]["fidelity_end"],
                "expected": "> 0.5",
                "possible_causes": [
                    "基础保真度系数需要调整",
                    "信任初始化值偏低",
                    "认知熵影响过大"
                ]
            })

        # 问题3：内鬼未激活
        if analysis["traitor_analysis"]["active_traitors"] == 0:
            high_tendency = analysis["traitor_analysis"]["high_tendency_count"]
            if high_tendency > 0:
                issues.append({
                    "type": "NO_TRAITOR_ACTIVATION",
                    "civilization": civ.civilization_id,
                    "severity": "INFO",
                    "high_tendency_count": high_tendency,
                    "avg_tendency": analysis["traitor_analysis"]["avg_traitor_tendency"],
                    "possible_causes": [
                        "激活阈值过高",
                        "机会因子计算偏低",
                        "忠诚度下降不够快"
                    ]
                })

    # 问题4：架构平衡
    outputs = {civ.architecture_type.value: civ.state.total_output
               for civ in game.civilizations}
    max_output = max(outputs.values())
    min_output = min(outputs.values())
    ratio = max_output / min_output if min_output > 0 else float('inf')

    if ratio > 2.0:
        issues.append({
            "type": "ARCHITECTURE_IMBALANCE",
            "severity": "HIGH",
            "ratio": ratio,
            "outputs": outputs,
            "expected": "ratio < 1.5",
            "possible_causes": [
                "循环效率补偿不足",
                "架构效率系数需要调整",
                "通达度计算导致差距过大"
            ]
        })

    return issues


def run_diagnostic_test(num_rounds: int = 10, seed: int = 42) -> Dict:
    """运行诊断测试"""
    print("=" * 70)
    print("智械星海 - 机制诊断测试")
    print("=" * 70)

    # 创建游戏
    game = GameEngine(
        num_civilizations=4,
        architecture_types=[
            ArchitectureType.STAR,
            ArchitectureType.TREE,
            ArchitectureType.MESH,
            ArchitectureType.TRIBAL
        ],
        total_rounds=num_rounds,
        seed=seed
    )

    # 运行
    game.initialize()

    # 初始状态分析
    print("\n【初始状态】")
    print("-" * 70)
    for civ in game.civilizations:
        analysis = analyze_civilization_detail(civ)
        print(f"{civ.civilization_id} ({civ.architecture_type.value}):")
        print(f"  循环数/回合: {analysis['arch_info']['cycles_per_round']}")
        print(f"  通达度: {analysis['arch_info']['reachability']:.4f}")
        print(f"  架构效率系数: {analysis['arch_info']['efficiency_coefficient']}")
        print(f"  平均内鬼倾向: {analysis['traitor_analysis']['avg_traitor_tendency']:.4f}")
        print(f"  高内鬼倾向Agent数: {analysis['traitor_analysis']['high_tendency_count']}")

    # 运行游戏
    for round_num in range(num_rounds):
        for civ in game.civilizations:
            game.run_round(civ)

    # 最终分析
    print("\n【最终结果】")
    print("-" * 70)
    for civ in game.civilizations:
        analysis = analyze_civilization_detail(civ)
        print(f"{civ.civilization_id} ({civ.architecture_type.value}):")
        print(f"  总产出: {analysis['output_analysis']['total_output']:.2f}")
        print(f"  循环数: {analysis['output_analysis']['num_cycles']}")
        print(f"  平均忠诚度: {analysis['states']['avg_loyalty']:.4f}")
        print(f"  忠诚度标准差: {analysis['states']['std_loyalty']:.4f}")
        print(f"  最终向心力: {analysis['macro_trends']['cohesion_end']:.4f}")
        print(f"  最终保真度: {analysis['macro_trends']['fidelity_end']:.4f}")
        print(f"  活跃内鬼: {analysis['traitor_analysis']['active_traitors']}")

    # 诊断问题
    print("\n【问题诊断】")
    print("-" * 70)
    issues = diagnose_issues(game)

    for issue in issues:
        print(f"[{issue['severity']}] {issue['type']}")
        if 'value' in issue:
            print(f"  当前值: {issue['value']}")
        if 'expected' in issue:
            print(f"  期望值: {issue['expected']}")
        if 'ratio' in issue:
            print(f"  最大/最小比例: {issue['ratio']:.2f}")
        if 'outputs' in issue:
            print(f"  各架构产出: {issue['outputs']}")
        print("  可能原因:")
        for cause in issue.get('possible_causes', []):
            print(f"    - {cause}")
        print()

    # 架构平衡性评估
    print("\n【架构平衡性评估】")
    print("-" * 70)

    outputs = {civ.architecture_type.value: civ.state.total_output
               for civ in game.civilizations}
    cycles = {civ.architecture_type.value: len(civ.state.cycle_outputs)
              for civ in game.civilizations}
    efficiencies = {civ.architecture_type.value: civ.config.efficiency_coefficient
                   for civ in game.civilizations}

    print(f"{'架构':<10} {'产出':<15} {'循环数':<10} {'效率系数':<10} {'产出/循环':<15}")
    for arch in outputs:
        output_per_cycle = outputs[arch] / cycles[arch] if cycles[arch] > 0 else 0
        print(f"{arch:<10} {outputs[arch]:<15.2f} {cycles[arch]:<10} {efficiencies[arch]:<10} {output_per_cycle:<15.2f}")

    return {
        "issues": issues,
        "outputs": outputs,
        "cycles": cycles
    }


if __name__ == "__main__":
    run_diagnostic_test()