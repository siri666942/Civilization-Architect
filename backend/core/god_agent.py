"""
上帝Agent系统

负责生成Agent的性格属性、计算内鬼倾向
"""

from typing import List, Dict, Optional
import numpy as np
from scipy.stats import norm
from scipy.special import expit as sigmoid

from backend.models.agent import Agent, Personality, AgentState
from backend.common.config import default_config


class GodAgent:
    """
    上帝Agent：生成所有Agent的性格属性

    使用Cholesky分解确保属性间的相关性
    """

    # 维度相关性矩阵
    CORRELATION_MATRIX = np.array([
        #    A_auth  A_self  A_resi  A_altr  A_soc   A_risk A_int   A_loyal
        [1.0,    0.3,   0.2,   -0.4,   0.1,    0.3,   0.2,   -0.2],   # A_auth
        [0.3,    1.0,   0.1,   -0.6,  -0.1,    0.2,   0.1,   -0.5],   # A_self
        [0.2,    0.1,   1.0,    0.2,   0.3,    0.1,   0.3,    0.4],   # A_resi
        [-0.4,  -0.6,   0.2,    1.0,   0.4,   -0.1,   0.2,    0.5],   # A_altr
        [0.1,   -0.1,   0.3,    0.4,   1.0,    0.2,   0.1,    0.2],   # A_soc
        [0.3,    0.2,   0.1,   -0.1,   0.2,    1.0,   0.1,   -0.1],   # A_risk
        [0.2,    0.1,   0.3,    0.2,   0.1,    0.1,    1.0,   0.2],   # A_int
        [-0.2,  -0.5,   0.4,    0.5,   0.2,   -0.1,   0.2,    1.0]    # A_loyal
    ])

    # 性格维度名称
    DIMENSION_NAMES = [
        "authority", "selfishness", "resilience", "altruism",
        "sociability", "risk_appetite", "intelligence", "loyalty_base"
    ]

    def __init__(self, seed: Optional[int] = None):
        """
        初始化上帝Agent

        Args:
            seed: 随机种子（用于可复现）
        """
        self.rng = np.random.default_rng(seed)

        # 预计算Cholesky分解
        self.cholesky_L = np.linalg.cholesky(self.CORRELATION_MATRIX)

    def generate_personality(self) -> Personality:
        """生成单个性格属性（带相关性）"""
        # 生成独立标准正态随机向量
        Z = self.rng.standard_normal(8)

        # 通过Cholesky变换生成相关随机向量
        X = self.cholesky_L @ Z

        # 归一化到[0,1]
        values = norm.cdf(X)

        return Personality(
            authority=values[0],
            selfishness=values[1],
            resilience=values[2],
            altruism=values[3],
            sociability=values[4],
            risk_appetite=values[5],
            intelligence=values[6],
            loyalty_base=values[7]
        )

    def generate_agents(self, n: int = 10,
                       civilization_id: str = "CIV-001") -> List[Agent]:
        """
        生成n个Agent

        Args:
            n: Agent数量
            civilization_id: 文明ID

        Returns:
            Agent列表
        """
        agents = []
        personalities = []

        # 先生成所有性格
        for i in range(n):
            personalities.append(self.generate_personality())

        # 检查多样性，必要时重新生成
        personalities = self._ensure_diversity(personalities, n)

        # 创建Agent
        for i, personality in enumerate(personalities):
            agent_id = f"A{i+1}"
            agent = Agent(
                id=agent_id,
                name=self._generate_name(i, personality),
                description=self._generate_description(personality),
                personality=personality
            )
            agents.append(agent)

        return agents

    def _ensure_diversity(self, personalities: List[Personality],
                         target_n: int) -> List[Personality]:
        """确保性格多样性（使用配置参数）"""
        personality_config = default_config.personality

        max_attempts = personality_config.diversity_max_attempts
        diversity_threshold = personality_config.diversity_threshold
        similarity_threshold = personality_config.similarity_threshold

        for attempt in range(max_attempts):
            # 计算多样性分数
            arrays = [p.to_array() for p in personalities]

            # 计算余弦相似度矩阵
            similarity_matrix = np.zeros((len(arrays), len(arrays)))
            for i in range(len(arrays)):
                for j in range(i+1, len(arrays)):
                    cos_sim = np.dot(arrays[i], arrays[j]) / (
                        np.linalg.norm(arrays[i]) * np.linalg.norm(arrays[j])
                    )
                    similarity_matrix[i, j] = cos_sim
                    similarity_matrix[j, i] = cos_sim

            # 计算多样性分数
            avg_similarity = np.mean(similarity_matrix[np.triu_indices(len(arrays), k=1)])
            diversity_score = 1 - avg_similarity

            if diversity_score >= diversity_threshold:
                # 检查是否有过于相似的
                max_sim = np.max(similarity_matrix[np.triu_indices(len(arrays), k=1)])
                if max_sim <= similarity_threshold:
                    return personalities

            # 重新生成过于相似的
            for i in range(len(arrays)):
                for j in range(i+1, len(arrays)):
                    if similarity_matrix[i, j] > similarity_threshold:
                        personalities[j] = self.generate_personality()

        return personalities

    def _generate_name(self, index: int, personality: Personality) -> str:
        """生成Agent名称"""
        # 基于性格特点生成名称
        traits = []

        if personality.authority > 0.7:
            traits.append("领袖")
        elif personality.altruism > 0.7:
            traits.append("奉献者")
        elif personality.intelligence > 0.7:
            traits.append("智者")
        elif personality.sociability > 0.7:
            traits.append("交际者")
        elif personality.selfishness > 0.7:
            traits.append("野心家")
        elif personality.resilience > 0.7:
            traits.append("坚韧者")
        else:
            traits.append("普通者")

        return f"Agent-{index+1}"

    def _generate_description(self, personality: Personality) -> str:
        """生成性格描述"""
        traits = []

        if personality.authority > 0.7:
            traits.append("渴望权力和支配")
        elif personality.authority < 0.3:
            traits.append("安于服从")

        if personality.selfishness > 0.7:
            traits.append("以个人利益为重")
        elif personality.altruism > 0.7:
            traits.append("乐于助人")

        if personality.intelligence > 0.7:
            traits.append("思维敏捷")
        elif personality.intelligence < 0.3:
            traits.append("反应较慢")

        if personality.sociability > 0.7:
            traits.append("善于交际")
        elif personality.sociability < 0.3:
            traits.append("内向孤僻")

        if personality.resilience > 0.7:
            traits.append("抗压能力强")

        if len(traits) == 0:
            traits.append("性格均衡")

        return "，".join(traits)

    def get_diversity_score(self, agents: List[Agent]) -> float:
        """计算Agent群体的多样性分数"""
        arrays = [a.personality.to_array() for a in agents]
        n = len(arrays)

        total_similarity = 0
        count = 0

        for i in range(n):
            for j in range(i+1, n):
                cos_sim = np.dot(arrays[i], arrays[j]) / (
                    np.linalg.norm(arrays[i]) * np.linalg.norm(arrays[j])
                )
                total_similarity += cos_sim
                count += 1

        avg_similarity = total_similarity / count if count > 0 else 0
        return 1 - avg_similarity


def initialize_agents(n: int = 10, seed: Optional[int] = None) -> List[Agent]:
    """
    快捷函数：初始化n个Agent

    Args:
        n: Agent数量
        seed: 随机种子

    Returns:
        Agent列表
    """
    god = GodAgent(seed=seed)
    return god.generate_agents(n)