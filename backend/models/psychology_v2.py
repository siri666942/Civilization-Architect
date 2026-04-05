"""
Agent 心理状态系统 v2

三层模型：
1. Trait（特质层）- 稳定的性格倾向，缓慢变化
2. State（状态层）- 动态的心理状态，快速变化
3. Volition（意愿层）- Agent的主动决策空间

核心理念：Agent有"心"，能感受、能思考、能决定
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import numpy as np


# ============================================
# 第一层：特质层（Trait Layer）
# ============================================

@dataclass
class Trait:
    """
    特质层：相对稳定的性格倾向

    特质会变化，但很慢，通常是长期经历的结果
    比如：经历重大背叛后，信任基准可能永久降低
    """
    # 八维性格（保持原有）
    authority: float = 0.5        # 权威感度
    selfishness: float = 0.5       # 私心倾向
    resilience: float = 0.5        # 韧性
    altruism: float = 0.5          # 利他性
    sociability: float = 0.5       # 社交性
    risk_appetite: float = 0.5     # 风险偏好
    intelligence: float = 0.5      # 智力
    loyalty_base: float = 0.5      # 忠诚度基准

    # 特质变化率（控制变化速度）
    # 0.001 表示每千次事件才变化一点点
    trait_mutation_rate: float = 0.001

    def update_trait(self, trait_name: str, influence: float, intensity: float):
        """
        更新特质（缓慢变化）

        Args:
            trait_name: 特质名称
            influence: 影响方向 (+1正向, -1负向)
            intensity: 事件强度 (0-1)
        """
        if not hasattr(self, trait_name):
            return

        current = getattr(self, trait_name)

        # 特质变化：受变化率控制，越极端的特质越难改变（极值稳定性）
        distance_from_center = abs(current - 0.5)
        stability_factor = 1 - distance_from_center * 0.5  # 极值更稳定

        delta = influence * intensity * self.trait_mutation_rate * stability_factor
        new_value = current + delta

        # 边界约束
        setattr(self, trait_name, max(0.0, min(1.0, new_value)))


# ============================================
# 第二层：状态层（State Layer）
# ============================================

class EmotionType(Enum):
    """情绪类型"""
    JOY = "joy"            # 喜悦
    ANGER = "anger"        # 愤怒
    FEAR = "fear"          # 恐惧
    TRUST = "trust"        # 信任
    DISGUST = "disgust"    # 厌恶
    SURPRISE = "surprise"  # 惊讶
    SADNESS = "sadness"    # 悲伤
    ANTICIPATION = "anticipation"  # 期待


@dataclass
class EmotionalState:
    """
    情绪状态：Agent当前的"心情"

    情绪会快速变化，受近期事件影响大
    这是Agent"感受"世界的方式
    """
    # 基础情绪（8种，参考Plutchik情绪轮）
    joy: float = 0.5           # 喜悦程度
    anger: float = 0.0         # 愤怒程度
    fear: float = 0.0          # 恐惧程度
    trust: float = 0.5         # 信任感
    disgust: float = 0.0       # 厌恶感
    surprise: float = 0.0      # 惊讶度
    sadness: float = 0.0      # 悲伤度
    anticipation: float = 0.5  # 期待度

    # 情绪衰减率（负面情绪衰减更快）
    positive_decay: float = 0.95
    negative_decay: float = 0.85

    def decay(self):
        """情绪自然衰减"""
        # 正面情绪慢衰减
        self.joy *= self.positive_decay
        self.trust *= self.positive_decay
        self.anticipation = 0.5 + (self.anticipation - 0.5) * self.positive_decay

        # 负面情绪快衰减（人会从负面情绪中恢复）
        self.anger *= self.negative_decay
        self.fear *= self.negative_decay
        self.disgust *= self.negative_decay
        self.sadness *= self.negative_decay
        self.surprise *= self.negative_decay

    def add_emotion(self, emotion: EmotionType, intensity: float):
        """添加情绪刺激"""
        current = getattr(self, emotion.value)
        # 情绪叠加但有上限
        new_value = min(1.0, current + intensity)
        setattr(self, emotion.value, new_value)

    def get_mood_score(self) -> float:
        """获取整体心情分数 (-1到1)"""
        positive = self.joy + self.trust + self.anticipation
        negative = self.anger + self.fear + self.disgust + self.sadness + self.surprise
        return (positive - negative) / 4  # 归一化到[-1, 1]


@dataclass
class CognitiveState:
    """
    认知状态：Agent对环境的认知

    这些状态直接影响Agent的决策能力
    """
    energy: float = 100.0           # 体力
    cognitive_entropy: float = 0.1   # 认知熵（混乱度）
    stress: float = 0.0              # 压力水平
    focus: float = 0.8               # 专注度

    def calculate_mental_clarity(self) -> float:
        """计算心理清晰度"""
        return self.focus * (1 - self.cognitive_entropy) * (1 - self.stress * 0.5)


@dataclass
class SocialState:
    """
    社会状态：Agent的社会感知

    这些状态来自与他人的交互
    """
    loyalty: float = 0.5            # 当前忠诚度
    belonging: float = 0.5          # 归属感
    status_perception: float = 0.5  # 地位感知
    contribution: float = 0.0       # 累计贡献

    # 信任矩阵（保持原有）
    trust_matrix: Dict[str, float] = field(default_factory=dict)


@dataclass
class AgentStateV2:
    """
    完整状态：情绪+认知+社会的综合
    """
    emotional: EmotionalState = field(default_factory=EmotionalState)
    cognitive: CognitiveState = field(default_factory=CognitiveState)
    social: SocialState = field(default_factory=SocialState)

    def get_avg_trust(self, exclude_self: str = None) -> float:
        """计算平均信任"""
        trusts = [v for k, v in self.social.trust_matrix.items()
                  if k != exclude_self]
        return sum(trusts) / len(trusts) if trusts else 0.5


# ============================================
# 第三层：意愿层（Volition Layer）
# ============================================

class GoalType(Enum):
    """目标类型"""
    SURVIVAL = "survival"      # 生存目标：保持体力、避免压力
    SOCIAL = "social"          # 社交目标：建立关系、获得认可
    ACHIEVEMENT = "achievement" # 成就目标：贡献、晋升
    COMFORT = "comfort"        # 舒适目标：减少压力、增加愉悦
    POWER = "power"            # 权力目标：提升地位、控制他人
    REBELLION = "rebellion"    # 反叛目标：对抗组织


@dataclass
class Goal:
    """单个目标"""
    goal_type: GoalType
    priority: float          # 优先级 0-1
    intensity: float         # 强度 0-1
    target: Optional[str]    # 目标对象（如果有）
    deadline: int = -1       # 截止时间（-1表示持续目标）


@dataclass
class Volition:
    """
    意愿层：Agent的"心"

    这是Agent自主决策的核心
    Agent根据状态+特质，主动设定目标并采取行动
    """
    # 当前目标列表（按优先级排序）
    goals: List[Goal] = field(default_factory=list)

    # 行为倾向（动态调整）
    tendency_work: float = 0.5      # 工作倾向
    tendency_conflict: float = 0.2   # 冲突倾向
    tendency_comm: float = 0.3       # 社交倾向

    # 风险承受度（当前）
    current_risk_tolerance: float = 0.5

    def set_goal(self, goal: Goal):
        """设定目标"""
        # 检查是否已存在同类目标
        for i, g in enumerate(self.goals):
            if g.goal_type == goal.goal_type:
                self.goals[i] = goal
                self._sort_goals()
                return

        self.goals.append(goal)
        self._sort_goals()

    def _sort_goals(self):
        """按优先级排序目标"""
        self.goals.sort(key=lambda g: g.priority, reverse=True)

    def get_top_goal(self) -> Optional[Goal]:
        """获取最高优先级目标"""
        return self.goals[0] if self.goals else None

    def update_tendencies(self, state: AgentStateV2, trait: Trait):
        """
        根据状态和特质更新行为倾向

        这是Agent"自主决定"的核心：它根据自己的心情、性格来决定想做什么
        """
        # 基础倾向来自特质
        base_work = 0.3 + 0.2 * (1 - trait.selfishness) + 0.2 * trait.altruism
        base_conflict = 0.1 + 0.2 * trait.selfishness - 0.1 * trait.altruism
        base_comm = 0.2 + 0.2 * trait.sociability

        # 情绪对倾向的影响
        mood = state.emotional.get_mood_score()

        # 心情好 -> 更愿意工作和社交
        # 心情差 -> 更可能冲突或逃避
        if mood > 0:
            tendency_work = base_work + 0.1 * mood
            tendency_comm = base_comm + 0.1 * mood
            tendency_conflict = base_conflict - 0.1 * mood
        else:
            tendency_work = base_work + 0.1 * mood  # 心情差减少工作意愿
            tendency_comm = base_comm + 0.2 * mood  # 减少社交
            tendency_conflict = base_conflict - 0.3 * mood  # 增加冲突倾向

        # 认知状态对倾向的影响
        clarity = state.cognitive.calculate_mental_clarity()
        if clarity < 0.5:
            # 认知混乱时，行为更随机
            tendency_conflict += 0.1

        # 压力对倾向的影响
        if state.cognitive.stress > 0.7:
            # 高压下，人更容易"崩溃"，做出极端行为
            tendency_conflict += 0.2

        # 归一化并保存
        total = tendency_work + tendency_conflict + tendency_comm
        self.tendency_work = max(0.2, min(0.8, tendency_work / total if total > 0 else 0.5))
        self.tendency_conflict = max(0.0, min(0.4, tendency_conflict / total if total > 0 else 0.1))
        self.tendency_comm = max(0.05, min(0.3, tendency_comm / total if total > 0 else 0.2))

        # 更新风险承受度
        self.current_risk_tolerance = (
            trait.risk_appetite * 0.6 +
            state.emotional.joy * 0.2 +
            (1 - state.cognitive.stress) * 0.2
        )


# ============================================
# 完整的心理系统
# ============================================

@dataclass
class PsychologySystem:
    """
    完整心理系统：三层一体的Agent心智模型
    """
    trait: Trait                          # 特质层（慢变）
    state: AgentStateV2 = field(default_factory=AgentStateV2)  # 状态层（快变）
    volition: Volition = field(default_factory=Volition)       # 意愿层（自主）

    def process_event(self, event_type: str, intensity: float, source: str = None):
        """
        处理事件：事件流过三层心理系统

        这是Agent"感受世界"的核心流程
        """
        if event_type == "betrayed":
            # 被背叛
            self.state.emotional.add_emotion(EmotionType.ANGER, intensity * 0.8)
            self.state.emotional.add_emotion(EmotionType.SADNESS, intensity * 0.5)
            self.state.emotional.add_emotion(EmotionType.FEAR, intensity * 0.3)

            # 社会状态变化
            self.state.social.loyalty -= intensity * 0.3
            if source:
                self.state.social.trust_matrix[source] = max(0.0,
                    self.state.social.trust_matrix.get(source, 0.5) - intensity * 0.4)

            # 特质可能缓慢变化
            self.trait.update_trait("loyalty_base", -1, intensity * 0.5)
            self.trait.update_trait("trust", -1, intensity * 0.3)

            # 可能触发反叛目标
            if intensity > 0.7:
                self.volition.set_goal(Goal(
                    goal_type=GoalType.REBELLION,
                    priority=max(0.5, intensity),
                    intensity=intensity,
                    target=source
                ))

        elif event_type == "helped":
            # 被帮助
            self.state.emotional.add_emotion(EmotionType.JOY, intensity * 0.6)
            self.state.emotional.add_emotion(EmotionType.TRUST, intensity * 0.4)

            if source:
                self.state.social.trust_matrix[source] = min(1.0,
                    self.state.social.trust_matrix.get(source, 0.5) + intensity * 0.2)

        elif event_type == "praised":
            # 被表扬
            self.state.emotional.add_emotion(EmotionType.JOY, intensity * 0.5)
            self.state.social.status_perception = min(1.0,
                self.state.social.status_perception + intensity * 0.1)

        elif event_type == "stressed":
            # 压力事件
            self.state.emotional.add_emotion(EmotionType.FEAR, intensity * 0.4)
            self.state.cognitive.stress = min(1.0, self.state.cognitive.stress + intensity * 0.2)
            self.state.cognitive.focus = max(0.0, self.state.cognitive.focus - intensity * 0.1)

        elif event_type == "energy_depleted":
            # 精力耗尽
            self.state.cognitive.energy = max(0, self.state.cognitive.energy - intensity * 20)
            self.state.emotional.add_emotion(EmotionType.SADNESS, intensity * 0.3)

        # 更新意愿倾向
        self.volition.update_tendencies(self.state, self.trait)

    def decide_energy_allocation(self) -> Tuple[float, float, float]:
        """
        Agent自主决定能量分配

        Returns:
            (work, conflict, comm) 三元组
        """
        # 基于意愿层的倾向
        work = self.volition.tendency_work * 100
        conflict = self.volition.tendency_conflict * 100
        comm = self.volition.tendency_comm * 100

        # 归一化到100
        total = work + conflict + comm
        if total > 100:
            scale = 100 / total
            work *= scale
            conflict *= scale
            comm *= scale

        return work, conflict, comm

    def tick(self):
        """
        时间流逝：情绪衰减、目标检查
        每个循环调用一次
        """
        # 情绪衰减
        self.state.emotional.decay()

        # 认知状态恢复
        self.state.cognitive.stress *= 0.9
        self.state.cognitive.focus = min(1.0, self.state.cognitive.focus + 0.02)
        self.state.cognitive.energy = min(100, self.state.cognitive.energy + 5)

        # 更新意愿
        self.volition.update_tendencies(self.state, self.trait)

    def to_dict(self) -> dict:
        """导出状态"""
        return {
            "trait": {
                "authority": self.trait.authority,
                "selfishness": self.trait.selfishness,
                "resilience": self.trait.resilience,
                "altruism": self.trait.altruism,
                "sociability": self.trait.sociability,
                "risk_appetite": self.trait.risk_appetite,
                "intelligence": self.trait.intelligence,
                "loyalty_base": self.trait.loyalty_base
            },
            "emotional": {
                "mood_score": self.state.emotional.get_mood_score(),
                "joy": self.state.emotional.joy,
                "anger": self.state.emotional.anger,
                "fear": self.state.emotional.fear,
                "trust": self.state.emotional.trust
            },
            "cognitive": {
                "energy": self.state.cognitive.energy,
                "stress": self.state.cognitive.stress,
                "clarity": self.state.cognitive.calculate_mental_clarity()
            },
            "social": {
                "loyalty": self.state.social.loyalty,
                "belonging": self.state.social.belonging,
                "avg_trust": self.state.get_avg_trust()
            },
            "volition": {
                "work_tendency": self.volition.tendency_work,
                "conflict_tendency": self.volition.tendency_conflict,
                "comm_tendency": self.volition.tendency_comm,
                "top_goal": self.volition.get_top_goal().goal_type.value if self.volition.get_top_goal() else None
            }
        }


# ============================================
# 使用示例
# ============================================

def demo_psychology_system():
    """演示三层心理系统"""

    print("=" * 70)
    print("Agent 心理系统演示")
    print("=" * 70)

    # 创建一个Agent
    trait = Trait(
        selfishness=0.3,
        altruism=0.7,
        sociability=0.6,
        resilience=0.5,
        loyalty_base=0.7
    )

    psych = PsychologySystem(trait=trait)

    print("\n【初始状态】")
    print(f"  心情分数: {psych.state.emotional.get_mood_score():.2f}")
    print(f"  工作倾向: {psych.volition.tendency_work:.2f}")
    print(f"  冲突倾向: {psych.volition.tendency_conflict:.2f}")

    # 模拟事件序列
    print("\n" + "=" * 70)
    print("事件流：Agent经历一系列事件")
    print("=" * 70)

    events = [
        ("helped", 0.5, "A2", "被同事A2帮助"),
        ("praised", 0.3, "A1", "被领导A1表扬"),
        ("stressed", 0.6, None, "承担了困难任务"),
        ("betrayed", 0.8, "A3", "发现A3是内鬼"),
    ]

    for event_type, intensity, source, desc in events:
        print(f"\n事件: {desc} (强度: {intensity})")
        psych.process_event(event_type, intensity, source)

        mood = psych.state.emotional.get_mood_score()
        anger = psych.state.emotional.anger
        trust = psych.state.emotional.trust

        print(f"  → 心情: {mood:.2f}, 愤怒: {anger:.2f}, 信任: {trust:.2f}")
        print(f"  → 工作倾向: {psych.volition.tendency_work:.2f}")
        print(f"  → 冲突倾向: {psych.volition.tendency_conflict:.2f}")

        goal = psych.volition.get_top_goal()
        if goal:
            print(f"  → 当前目标: {goal.goal_type.value} (优先级: {goal.priority:.2f})")

    print("\n" + "=" * 70)
    print("时间流逝（情绪恢复）")
    print("=" * 70)

    for i in range(5):
        psych.tick()
        mood = psych.state.emotional.get_mood_score()
        anger = psych.state.emotional.anger
        print(f"  循环{i+1}: 心情={mood:.2f}, 愤怒={anger:.2f}")

    print("\n【最终状态】")
    print(f"  决策能量分配: {psych.decide_energy_allocation()}")


if __name__ == "__main__":
    demo_psychology_system()