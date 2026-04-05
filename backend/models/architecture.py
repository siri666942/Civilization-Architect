"""
架构与通达度系统

定义四种组织架构、通达度计算、循环数映射
支持任意数量Agent的动态架构生成
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from enum import Enum
from functools import lru_cache
import numpy as np

from backend.models.agent import ArchitectureType, Agent
from backend.common.config import default_config


@dataclass
class ArchitectureConfig:
    """架构配置"""
    architecture_type: ArchitectureType
    adjacency_matrix: np.ndarray
    agent_ids: List[str]

    # 架构参数
    structure_coefficient: float = 1.0
    robustness_coefficient: float = 0.5
    base_fidelity: float = 0.8
    efficiency_coefficient: float = 1.0

    # 计算得出的指标
    average_path_length: float = 0.0
    reachability: float = 0.0
    cycles_per_round: int = 5
    diameter: int = 1
    edge_density: float = 0.0

    # 缓存的最短路径矩阵
    _distance_matrix: Optional[np.ndarray] = field(default=None, repr=False)

    def get_distance_matrix(self) -> np.ndarray:
        """获取缓存的最短路径矩阵"""
        if self._distance_matrix is None:
            self._distance_matrix = ArchitectureAnalyzer.compute_shortest_paths(
                self.adjacency_matrix
            )
        return self._distance_matrix


class ArchitectureFactory:
    """架构工厂：创建不同类型的架构（支持动态数量Agent）"""

    @staticmethod
    def create_star_architecture(agent_ids: List[str]) -> ArchitectureConfig:
        """
        创建星形架构
        中心节点：第一个Agent
        支持任意数量的Agent
        """
        n = len(agent_ids)
        adj = np.zeros((n, n))

        # 中心节点连接所有其他节点
        for i in range(1, n):
            adj[0, i] = 1  # 中心向边缘
            adj[i, 0] = 1  # 边缘向中心

        config = ArchitectureConfig(
            architecture_type=ArchitectureType.STAR,
            adjacency_matrix=adj,
            agent_ids=agent_ids,
            structure_coefficient=default_config.architecture.star_structure_coefficient,
            robustness_coefficient=default_config.architecture.star_robustness_coefficient,
            base_fidelity=default_config.architecture.star_base_fidelity,
            efficiency_coefficient=default_config.architecture.star_efficiency_coefficient
        )

        return config

    @staticmethod
    def create_tree_architecture(agent_ids: List[str]) -> ArchitectureConfig:
        """
        创建树形架构（动态生成）
        结构：根节点 -> 中层节点 -> 叶子节点
        支持任意数量的Agent

        算法：
        - 根节点：1个
        - 中层节点：约 sqrt(n-1) 个
        - 叶子节点：剩余节点平均分配给中层
        """
        n = len(agent_ids)

        if n == 0:
            raise ValueError("Agent数量不能为0")

        if n == 1:
            # 单节点：自环
            adj = np.zeros((1, 1))
        elif n == 2:
            # 双节点：直接连接
            adj = np.zeros((n, n))
            adj[0, 1] = 1
            adj[1, 0] = 1
        else:
            adj = np.zeros((n, n))

            # 计算中层节点数量（约sqrt(n-1)，至少1个，最多(n-1)/2个）
            import math
            num_middle = max(1, min(int(math.sqrt(n - 1)), (n - 1) // 2))

            # 根节点（索引0）连接所有中层节点（索引1到num_middle）
            for i in range(1, num_middle + 1):
                adj[0, i] = 1
                adj[i, 0] = 1

            # 叶子节点（索引num_middle+1到n-1）分配给中层节点
            leaf_start = num_middle + 1
            num_leaves = n - leaf_start

            if num_leaves > 0:
                # 平均分配叶子节点给各中层节点
                leaves_per_middle = num_leaves / num_middle

                for leaf_idx in range(num_leaves):
                    leaf_node = leaf_start + leaf_idx
                    # 计算该叶子节点应该连接到哪个中层节点
                    middle_node = 1 + int(leaf_idx // max(1, leaves_per_middle))
                    middle_node = min(middle_node, num_middle)  # 边界检查

                    adj[middle_node, leaf_node] = 1
                    adj[leaf_node, middle_node] = 1

            # 如果叶子节点不足，确保所有中层节点都至少连接到根节点
            # （已在上面的循环中完成）

        config = ArchitectureConfig(
            architecture_type=ArchitectureType.TREE,
            adjacency_matrix=adj,
            agent_ids=agent_ids,
            structure_coefficient=default_config.architecture.tree_structure_coefficient,
            robustness_coefficient=default_config.architecture.tree_robustness_coefficient,
            base_fidelity=default_config.architecture.tree_base_fidelity,
            efficiency_coefficient=default_config.architecture.tree_efficiency_coefficient
        )

        return config

    @staticmethod
    def create_mesh_architecture(agent_ids: List[str]) -> ArchitectureConfig:
        """
        创建全网状架构
        所有节点互相连接
        支持任意数量的Agent
        """
        n = len(agent_ids)
        adj = np.ones((n, n))
        np.fill_diagonal(adj, 0)  # 对角线为0

        config = ArchitectureConfig(
            architecture_type=ArchitectureType.MESH,
            adjacency_matrix=adj,
            agent_ids=agent_ids,
            structure_coefficient=default_config.architecture.mesh_structure_coefficient,
            robustness_coefficient=default_config.architecture.mesh_robustness_coefficient,
            base_fidelity=default_config.architecture.mesh_base_fidelity,
            efficiency_coefficient=default_config.architecture.mesh_efficiency_coefficient
        )

        return config

    @staticmethod
    def create_tribal_architecture(agent_ids: List[str]) -> ArchitectureConfig:
        """
        创建部落架构（动态生成）
        部落内全网状，部落间弱连接
        支持任意数量的Agent

        算法：
        - 将Agent平均分成3-4个部落
        - 每个部落内部全连接
        - 相邻部落之间有弱连接
        """
        n = len(agent_ids)

        if n == 0:
            raise ValueError("Agent数量不能为0")

        adj = np.zeros((n, n))

        if n == 1:
            # 单节点
            pass
        elif n == 2:
            # 双节点：直接连接
            adj[0, 1] = 1
            adj[1, 0] = 1
        else:
            # 确定部落数量（3-4个，根据总人数调整）
            import math
            num_tribes = min(4, max(2, n // 3))

            # 计算每个部落的大小
            tribe_sizes = []
            base_size = n // num_tribes
            remainder = n % num_tribes

            for i in range(num_tribes):
                size = base_size + (1 if i < remainder else 0)
                tribe_sizes.append(size)

            # 为每个部落建立内部连接
            current_idx = 0
            tribe_starts = []

            for tribe_idx, size in enumerate(tribe_sizes):
                tribe_starts.append(current_idx)
                tribe_end = current_idx + size

                # 部落内全网状
                for i in range(current_idx, tribe_end):
                    for j in range(current_idx, tribe_end):
                        if i != j:
                            adj[i, j] = 1

                current_idx = tribe_end

            # 部落间弱连接（相邻部落之间）
            num_inter_connections = default_config.architecture.tribal_inter_connections

            for i in range(num_tribes - 1):
                # 从部落i的末尾连接到部落i+1的开头
                tribe_i_end = tribe_starts[i] + tribe_sizes[i] - 1
                tribe_i1_start = tribe_starts[i + 1]

                adj[tribe_i_end, tribe_i1_start] = 1
                adj[tribe_i1_start, tribe_i_end] = 1

                # 添加额外的连接（如果部落够大）
                if tribe_sizes[i] > 1 and num_inter_connections > 1:
                    extra_from = tribe_starts[i]
                    adj[extra_from, tribe_i1_start] = 1
                    adj[tribe_i1_start, extra_from] = 1

        config = ArchitectureConfig(
            architecture_type=ArchitectureType.TRIBAL,
            adjacency_matrix=adj,
            agent_ids=agent_ids,
            structure_coefficient=default_config.architecture.tribal_structure_coefficient,
            robustness_coefficient=default_config.architecture.tribal_robustness_coefficient,
            base_fidelity=default_config.architecture.tribal_base_fidelity,
            efficiency_coefficient=default_config.architecture.tribal_efficiency_coefficient
        )

        return config

    @classmethod
    def create_architecture(cls, arch_type: ArchitectureType,
                           agent_ids: List[str]) -> ArchitectureConfig:
        """根据类型创建架构"""
        creators = {
            ArchitectureType.STAR: cls.create_star_architecture,
            ArchitectureType.TREE: cls.create_tree_architecture,
            ArchitectureType.MESH: cls.create_mesh_architecture,
            ArchitectureType.TRIBAL: cls.create_tribal_architecture
        }

        return creators[arch_type](agent_ids)


class ArchitectureAnalyzer:
    """架构分析器：计算通达度、循环数等（带缓存优化）"""

    @staticmethod
    def compute_shortest_paths(adj: np.ndarray) -> np.ndarray:
        """
        使用优化的Floyd-Warshall算法计算所有节点对之间的最短路径
        对于无权图，也可以使用BFS（对于大型网络更高效）
        """
        n = adj.shape[0]

        if n <= 50:
            # 小型网络：使用Floyd-Warshall
            return ArchitectureAnalyzer._floyd_warshall(adj)
        else:
            # 大型网络：使用BFS（每个节点BFS一次）
            return ArchitectureAnalyzer._bfs_all_pairs(adj)

    @staticmethod
    def _floyd_warshall(adj: np.ndarray) -> np.ndarray:
        """Floyd-Warshall算法实现"""
        n = adj.shape[0]
        # 初始化距离矩阵
        dist = np.full((n, n), np.inf)
        np.fill_diagonal(dist, 0)

        # 直接连接的距离为1
        for i in range(n):
            for j in range(n):
                if adj[i, j] > 0:
                    dist[i, j] = 1

        # Floyd-Warshall
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    if dist[i, k] + dist[k, j] < dist[i, j]:
                        dist[i, j] = dist[i, k] + dist[k, j]

        return dist

    @staticmethod
    def _bfs_all_pairs(adj: np.ndarray) -> np.ndarray:
        """BFS算法计算所有节点对的最短路径（对大型网络更高效）"""
        n = adj.shape[0]
        dist = np.full((n, n), np.inf)
        np.fill_diagonal(dist, 0)

        for start in range(n):
            # 从start节点开始BFS
            visited = {start}
            queue = [(start, 0)]

            while queue:
                node, d = queue.pop(0)
                dist[start, node] = d

                for neighbor in range(n):
                    if adj[node, neighbor] > 0 and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, d + 1))

        return dist

    @staticmethod
    def compute_average_path_length(dist: np.ndarray) -> float:
        """计算平均路径长度"""
        # 只计算可达的路径
        finite_distances = dist[np.isfinite(dist) & (dist > 0)]
        if len(finite_distances) == 0:
            return 1.0
        return float(np.mean(finite_distances))

    @staticmethod
    def compute_diameter(dist: np.ndarray) -> int:
        """计算网络直径（最长最短路径）"""
        finite_distances = dist[np.isfinite(dist)]
        if len(finite_distances) == 0:
            return 1
        return int(np.max(finite_distances))

    @staticmethod
    def compute_edge_density(adj: np.ndarray) -> float:
        """计算边密度"""
        n = adj.shape[0]
        max_edges = n * (n - 1)
        actual_edges = np.sum(adj > 0)
        return actual_edges / max_edges if max_edges > 0 else 0.0

    @staticmethod
    def compute_centrality(adj: np.ndarray, dist: np.ndarray = None) -> np.ndarray:
        """
        计算每个节点的中心度
        Centrality = Σ (1/d(node, j))
        """
        if dist is None:
            dist = ArchitectureAnalyzer.compute_shortest_paths(adj)

        n = adj.shape[0]
        centrality = np.zeros(n)

        for i in range(n):
            for j in range(n):
                if i != j and np.isfinite(dist[i, j]) and dist[i, j] > 0:
                    centrality[i] += 1.0 / dist[i, j]

        # 归一化
        max_cen = np.max(centrality)
        if max_cen > 0:
            centrality = centrality / max_cen

        return centrality

    @classmethod
    def analyze_architecture(cls, config: ArchitectureConfig) -> ArchitectureConfig:
        """完整分析架构"""
        adj = config.adjacency_matrix
        n = adj.shape[0]

        # 计算最短路径并缓存
        dist = cls.compute_shortest_paths(adj)
        config._distance_matrix = dist

        # 计算各项指标
        config.average_path_length = cls.compute_average_path_length(dist)
        config.diameter = cls.compute_diameter(dist)
        config.edge_density = cls.compute_edge_density(adj)

        # 计算通达度
        # R = (1/平均路径) × 架构系数 × 边密度
        if config.average_path_length > 0:
            config.reachability = (
                (1 / config.average_path_length) *
                config.structure_coefficient *
                config.edge_density
            )
        else:
            config.reachability = 1.0

        # 计算循环数
        # CyclesPerRound = 5 + floor(5 × R_normalized)
        # R_normalized = R / R_max (网状架构的通达度作为R_max=1.0)
        r_normalized = config.reachability  # 因为网状R=1.0
        config.cycles_per_round = 5 + int(5 * r_normalized)

        return config

    @classmethod
    def assign_agent_positions(cls, config: ArchitectureConfig,
                               agents: List[Agent]) -> List[Agent]:
        """为Agent分配位置信息"""
        adj = config.adjacency_matrix

        # 使用缓存的最短路径矩阵
        dist = config.get_distance_matrix()
        centrality = cls.compute_centrality(adj, dist)

        for i, agent in enumerate(agents):
            # 设置中心度
            agent.centrality = centrality[i]

            # 根据中心度分配位置
            if centrality[i] > 0.8:
                agent.position = "core"
            elif centrality[i] > 0.3:
                agent.position = "middle"
            else:
                agent.position = "edge"

            # 计算层级（到最近核心节点的距离）
            if config.architecture_type == ArchitectureType.TREE:
                agent.level = int(dist[0, i])  # 以根节点为基准

        return agents


def create_architecture(arch_type: ArchitectureType,
                       agent_ids: List[str]) -> ArchitectureConfig:
    """创建并分析架构"""
    config = ArchitectureFactory.create_architecture(arch_type, agent_ids)
    config = ArchitectureAnalyzer.analyze_architecture(config)
    return config
