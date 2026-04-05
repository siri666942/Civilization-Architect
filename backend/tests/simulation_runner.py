"""
模拟运行器

运行模拟并收集数据，用于分析和评估
"""

from typing import List, Dict, Optional
import json
import time
from datetime import datetime
import numpy as np

from backend.core.engine import GameEngine, Civilization
from backend.models.agent import ArchitectureType
from backend.common.config import GameConfig, default_config


class SimulationRunner:
    """模拟运行器"""

    def __init__(self, game: GameEngine):
        self.game = game
        self.results = []
        self.execution_time = 0.0

    def run(self) -> Dict:
        """运行模拟"""
        start_time = time.time()

        results = self.game.run_full_game()

        self.execution_time = time.time() - start_time
        self.results = results

        return results

    def get_summary(self) -> Dict:
        """获取模拟摘要"""
        if not self.results:
            return {}

        summary = {
            "execution_time": self.execution_time,
            "total_rounds": self.game.total_rounds,
            "civilizations": []
        }

        for civ_data in self.results["rankings"]:
            summary["civilizations"].append({
                "rank": civ_data["rank"],
                "civilization_id": civ_data["civilization_id"],
                "architecture": civ_data["architecture_type"],
                "total_output": civ_data["total_output"],
                "traitor_count": civ_data["traitor_count"]
            })

        return summary

    def export_results(self, filepath: str):
        """导出结果到JSON文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)


def run_comparison_simulation(num_runs: int = 10,
                               total_rounds: int = 10,
                               seed_start: int = 42,
                               config: GameConfig = None) -> Dict:
    """
    运行多次模拟比较不同架构

    Args:
        num_runs: 运行次数
        total_rounds: 每次运行的回合数
        seed_start: 起始随机种子
        config: 游戏配置

    Returns:
        统计结果
    """
    all_results = []

    for i in range(num_runs):
        game = GameEngine(
            num_civilizations=4,
            architecture_types=[
                ArchitectureType.STAR,
                ArchitectureType.TREE,
                ArchitectureType.MESH,
                ArchitectureType.TRIBAL
            ],
            total_rounds=total_rounds,
            seed=seed_start + i,
            config=config
        )

        runner = SimulationRunner(game)
        result = runner.run()
        all_results.append(result)

    # 汇总统计
    stats = aggregate_statistics(all_results)

    return stats


def aggregate_statistics(all_results: List[Dict]) -> Dict:
    """汇总多次运行的统计结果"""
    architecture_stats = {}

    for result in all_results:
        for civ in result["rankings"]:
            arch = civ["architecture_type"]

            if arch not in architecture_stats:
                architecture_stats[arch] = {
                    "total_outputs": [],
                    "ranks": [],
                    "traitor_counts": [],
                    "final_cohesions": [],
                    "final_fidelities": []
                }

            architecture_stats[arch]["total_outputs"].append(civ["total_output"])
            architecture_stats[arch]["ranks"].append(civ["rank"])
            architecture_stats[arch]["traitor_counts"].append(civ["traitor_count"])
            architecture_stats[arch]["final_cohesions"].append(civ["final_cohesion"])
            architecture_stats[arch]["final_fidelities"].append(civ["final_fidelity"])

    # 计算平均值和标准差
    summary = {}
    for arch, data in architecture_stats.items():
        summary[arch] = {
            "avg_output": np.mean(data["total_outputs"]),
            "std_output": np.std(data["total_outputs"]),
            "avg_rank": np.mean(data["ranks"]),
            "win_rate": sum(1 for r in data["ranks"] if r == 1) / len(data["ranks"]),
            "avg_traitor_count": np.mean(data["traitor_counts"]),
            "avg_final_cohesion": np.mean(data["final_cohesions"]),
            "avg_final_fidelity": np.mean(data["final_fidelities"])
        }

    return summary


def quick_test(num_agents: int = 10, num_rounds: int = 10, seed: int = 42):
    """
    快速测试

    Args:
        num_agents: 每个文明的Agent数量
        num_rounds: 总回合数
        seed: 随机种子
    """
    print("=" * 60)
    print("智械星海：戴森球拓荒者 - 快速模拟测试")
    print("=" * 60)
    print(f"配置: 每文明{num_agents}个Agent, {num_rounds}回合, 种子={seed}")
    print()

    # 创建游戏
    game = GameEngine(
        num_civilizations=4,
        architecture_types=[
            ArchitectureType.STAR,
            ArchitectureType.TREE,
            ArchitectureType.MESH,
            ArchitectureType.TRIBAL
        ],
        agents_per_civilization=num_agents,
        total_rounds=num_rounds,
        seed=seed
    )

    # 运行模拟
    runner = SimulationRunner(game)
    results = runner.run()

    # 打印结果
    print("\n最终排名：")
    print("-" * 60)
    for civ in results["rankings"]:
        print(f"#{civ['rank']} {civ['civilization_id']} ({civ['architecture_type']})")
        print(f"   总产出: {civ['total_output']:.2f}")
        print(f"   最终向心力: {civ['final_cohesion']:.4f}")
        print(f"   最终保真度: {civ['final_fidelity']:.4f}")
        print(f"   内鬼数量: {civ['traitor_count']}")
        print()

    print(f"执行时间: {runner.execution_time:.2f}秒")

    return results


if __name__ == "__main__":
    quick_test()
