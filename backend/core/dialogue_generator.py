"""
对话生成器

生成有趣、生动的Agent对话内容
支持多种场景、性格驱动的对话风格
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import random
from enum import Enum

from backend.models.message import Message, MessageType, MessageTone, StructuredContent, NaturalLanguageContent
from backend.models.psychology_v2 import PsychologySystem, EmotionType, GoalType


class DialogueStyle(Enum):
    """对话风格"""
    FORMAL = "formal"           # 正式
    CASUAL = "casual"           # 随意
    EMOTIONAL = "emotional"     # 情绪化
    CUNNING = "cunning"         # 狡猾
    HONEST = "honest"           # 诚实
    DEFENSIVE = "defensive"     # 防御性


@dataclass
class DialogueContext:
    """对话上下文"""
    relationship: str           # 关系：superior, subordinate, peer, enemy
    trust_level: float          # 信任程度
    recent_events: List[str]    # 近期事件
    communication_purpose: str  # 通讯目的
    stress_level: float = 0.0   # 压力水平


class DialogueGenerator:
    """
    对话生成器

    根据Agent性格、状态、关系生成有趣的对话
    不依赖LLM，使用规则+模板生成
    """

    # 消息模板库
    TEMPLATES = {
        MessageType.REPORT: {
            "friendly": [
                "这轮干得挺顺的，{work_done}个单位到手！感觉还不错~",
                "汇报一下：完成了{work_done}，虽然有点累但值得！",
                "嘿，{receiver_name}！这轮贡献了{contribution}，希望能帮上忙！"
            ],
            "neutral": [
                "本轮工作汇报：完成{work_done}单位，贡献值{contribution}。",
                "任务执行情况：工作量{work_done}，效率{efficiency}%。",
                "汇报：已按要求完成{work_done}单位工作。"
            ],
            "hostile": [
                "行吧，{work_done}，就这样。",
                "完成了，{work_done}。有什么问题吗？",
                "任务做了，{contribution}贡献。就这样。"
            ],
            "urgent": [
                "紧急汇报！完成{work_done}，但遇到问题：{issues}",
                "注意！本轮产出{contribution}，情况不太对！",
                "快看！{work_done}单位完成，但有异常！"
            ]
        },
        MessageType.REQUEST: {
            "friendly": [
                "那个...{receiver_name}，能帮我一下吗？我需要{request_amount}资源。",
                "伙伴，这边有点困难，能支援{request_amount}吗？",
                "能不能搭把手？缺{request_amount}，回头请你！"
            ],
            "neutral": [
                "申请{request_amount}资源支持，原因：{request_reason}。",
                "资源请求：需要{request_amount}，用于{request_reason}。",
                "请求协助：{request_reason}，需{request_amount}。"
            ],
            "desperate": [
                "紧急求助！真的需要{request_amount}，不然要出问题！",
                "快帮帮我！{request_reason}，我已经没办法了！",
                "求救！缺{request_amount}，情况很危急！"
            ]
        },
        MessageType.STATUS: {
            "friendly": [
                "嘿{receiver_name}！我这儿进度{progress}%，一切正常~",
                "同步一下：我现在状态不错，{progress}%搞定！",
                "汇报下进度：{progress}%完成，后面稳了！"
            ],
            "neutral": [
                "状态同步：进度{progress}%，状态{my_status}。",
                "当前状态：{my_status}，进度{progress}%。",
                "同步信息：完成度{progress}%。"
            ],
            "stressed": [
                "唉...进度{progress}%，有点吃力...",
                "状态更新：{progress}%...说实话有点累。",
                "这轮难搞啊，{progress}%...还在撑。"
            ]
        },
        MessageType.CHAT: {
            "friendly": [
                "{receiver_name}，今天怎么样？我发现个有意思的事...",
                "诶，你觉得咱们这文明能赢吗？我挺有信心的！",
                "话说，最近{event_comment}，你怎么看？"
            ],
            "gossip": [
                "你听说了吗？{gossip_content}",
                "有个消息，不知道该不该说...{gossip_content}",
                "悄悄告诉你，{gossip_content}，别传出去啊！"
            ],
            "philosophical": [
                "你说...我们存在的意义是什么？",
                "有时候我在想，这一切值得吗？",
                "如果我们输了，会怎样呢？"
            ]
        },
        MessageType.PERSUADE: {
            "friendly": [
                "{receiver_name}，我觉得咱们应该{persuade_target}，你觉得呢？",
                "说真的，{persuade_target}对咱们都有好处！",
                "考虑一下{persuade_target}？我觉得挺好的！"
            ],
            "manipulative": [
                "你知道吗，{receiver_name}，其实{manipulate_content}...",
                "我觉得你应该为自己想想，{manipulate_content}。",
                "别傻了，{manipulate_content}，聪明人都这么做。"
            ],
            "urgent": [
                "听我说！必须{persuade_target}，不然来不及了！",
                "现在只有{persuade_target}能救我们了！",
                "相信我，{persuade_target}是唯一的出路！"
            ]
        },
        MessageType.MANIPULATE: {
            "subtle": [
                "其实{receiver_name}，你有没有觉得{manipulate_content}？",
                "我不是说要你做什么，但{manipulate_content}...",
                "换位思考一下，{manipulate_content}，对吧？"
            ],
            "direct": [
                "别傻了，{manipulate_content}。你应该{traitor_hint}。",
                "醒醒吧！{manipulate_content}。我说的对吧？",
                "看着我的眼睛，{manipulate_content}，你真的相信他们吗？"
            ]
        },
        MessageType.ALERT: {
            "friendly": [
                "注意注意！{alert_content}，小心点！",
                "提醒一下：{alert_content}，别中招！",
                "我发现{alert_content}，大家小心！"
            ],
            "urgent": [
                "警报！{alert_content}！立即行动！",
                "危险！{alert_content}，快躲开！",
                "紧急！{alert_content}，告诉大家！"
            ],
            "suspicious": [
                "有点奇怪...{alert_content}，你们注意到了吗？",
                "我发现个问题：{alert_content}，不知是不是错觉。",
                "话说...{alert_content}，该不会是内鬼吧？"
            ]
        },
        MessageType.CONFESSION: {
            "honest": [
                "其实我一直想告诉你...{confession_content}",
                "算了，我不想瞒你了。{confession_content}",
                "对不起...{confession_content}。你能原谅我吗？"
            ],
            "emotional": [
                "我忍不住了...{confession_content}，我真的很抱歉。",
                "这些年...{confession_content}，我一直很内疚。",
                "听我说完...{confession_content}...我做了对不起大家的事。"
            ]
        }
    }

    # 情绪标记词
    EMOTION_MARKERS = {
        EmotionType.JOY: ["哈哈", "太好了", "不错", "开心", "棒"],
        EmotionType.ANGER: ["啧", "真是的", "可恶", "气死我了", "烦"],
        EmotionType.FEAR: ["糟糕", "危险", "可怕", "吓人", "不妙"],
        EmotionType.TRUST: ["相信", "靠谱", "没问题", "放心"],
        EmotionType.DISGUST: ["恶心", "讨厌", "受不了", "真是够了"],
        EmotionType.SADNESS: ["唉", "难过", "心痛", "失望", "可惜"],
        EmotionType.SURPRISE: ["什么？！", "真的假的", "不会吧", "天哪"],
        EmotionType.ANTICIPATION: ["期待", "希望", "等不及", "快了"]
    }

    def __init__(self, rng: random.Random = None):
        """
        初始化对话生成器

        Args:
            rng: 随机数生成器（可传入以保证可复现）
        """
        self.rng = rng or random.Random()

    def generate_message(
        self,
        sender_psychology: PsychologySystem,
        receiver_id: str,
        receiver_name: str,
        message_type: MessageType,
        context: DialogueContext,
        structured_data: Dict = None
    ) -> Message:
        """
        生成完整的消息

        Args:
            sender_psychology: 发送者的心理系统
            receiver_id: 接收者ID
            receiver_name: 接收者名称
            message_type: 消息类型
            context: 对话上下文
            structured_data: 结构化数据

        Returns:
            完整消息对象
        """
        # 确定对话风格
        style = self._determine_style(sender_psychology, context)

        # 选择模板
        template = self._select_template(message_type, style, context)

        # 生成对话内容
        dialogue = self._fill_template(
            template,
            sender_psychology,
            receiver_name,
            structured_data,
            context
        )

        # 添加情绪标记
        emotion_markers = self._get_emotion_markers(sender_psychology)

        # 确定语气
        tone = self._determine_tone(sender_psychology, context)

        # 计算重要性分数
        importance = self._calculate_importance(message_type, context)

        # 创建消息对象
        message = Message(
            sender_id="",  # 由调用者填充
            sender_name="",  # 由调用者填充
            receiver_id=receiver_id,
            receiver_name=receiver_name,
            message_type=message_type,
            structured=StructuredContent(**structured_data) if structured_data else None,
            natural_language=NaturalLanguageContent(
                message=dialogue,
                tone=tone,
                emotion_markers=emotion_markers,
                hidden_intent=self._get_hidden_intent(sender_psychology, message_type)
            ),
            importance_score=importance,
            is_traitor_action=self._is_traitor_action(sender_psychology, message_type)
        )

        return message

    def _determine_style(
        self,
        psychology: PsychologySystem,
        context: DialogueContext
    ) -> str:
        """确定对话风格"""
        mood = psychology.state.emotional.get_mood_score()
        stress = psychology.state.cognitive.stress
        trait = psychology.trait

        # 高压力 -> 紧急或防御
        if stress > 0.7:
            return "urgent" if mood > 0 else "defensive"

        # 关系影响
        if context.trust_level < 0.3:
            return "hostile"
        elif context.trust_level > 0.7:
            return "friendly"

        # 性格影响
        if trait.sociability > 0.7:
            return self.rng.choice(["friendly", "casual", "emotional"])
        elif trait.selfishness > 0.7 and psychology.volition.get_top_goal():
            if psychology.volition.get_top_goal().goal_type == GoalType.REBELLION:
                return "cunning"

        return "neutral"

    def _select_template(
        self,
        message_type: MessageType,
        style: str,
        context: DialogueContext
    ) -> str:
        """选择对话模板"""
        templates = self.TEMPLATES.get(message_type, {})
        style_templates = templates.get(style, templates.get("neutral", ["..."]))

        return self.rng.choice(style_templates)

    def _fill_template(
        self,
        template: str,
        psychology: PsychologySystem,
        receiver_name: str,
        structured_data: Dict,
        context: DialogueContext
    ) -> str:
        """填充模板"""
        trait = psychology.trait
        state = psychology.state

        # 准备填充变量
        fill_vars = {
            "receiver_name": receiver_name,
            "work_done": structured_data.get("work_done", "一些") if structured_data else "一些",
            "contribution": f"{structured_data.get('contribution', 0):.1f}" if structured_data else "若干",
            "efficiency": f"{state.cognitive.calculate_mental_clarity() * 100:.0f}",
            "progress": f"{structured_data.get('progress', 0) * 100:.0f}%" if structured_data else "若干",
            "my_status": structured_data.get("my_status", "正常") if structured_data else "正常",
            "request_amount": str(structured_data.get("request_amount", "一些")) if structured_data else "一些",
            "request_reason": structured_data.get("request_reason", "工作需要") if structured_data else "需要",
            "issues": "、".join(structured_data.get("issues", ["无"])) if structured_data else "无",
            "event_comment": self._get_random_event_comment(),
            "gossip_content": self._generate_gossip(context),
            "persuade_target": "多为自己考虑" if trait.selfishness > 0.5 else "一起努力",
            "manipulate_content": self._generate_manipulation(context, trait),
            "traitor_hint": "先保住自己" if trait.selfishness > 0.5 else "小心点",
            "alert_content": self._generate_alert_content(context),
            "confession_content": "我有些事情做得不对"
        }

        # 填充模板
        result = template
        for key, value in fill_vars.items():
            result = result.replace("{" + key + "}", str(value))

        return result

    def _get_emotion_markers(self, psychology: PsychologySystem) -> List[str]:
        """获取当前情绪标记"""
        markers = []
        emotional = psychology.state.emotional

        # 找出最强的情绪
        emotion_values = {
            EmotionType.JOY: emotional.joy,
            EmotionType.ANGER: emotional.anger,
            EmotionType.FEAR: emotional.fear,
            EmotionType.TRUST: emotional.trust,
            EmotionType.DISGUST: emotional.disgust,
            EmotionType.SADNESS: emotional.sadness,
            EmotionType.SURPRISE: emotional.surprise,
            EmotionType.ANTICIPATION: emotional.anticipation
        }

        # 取最强的2个情绪
        sorted_emotions = sorted(emotion_values.items(), key=lambda x: x[1], reverse=True)
        for emotion_type, value in sorted_emotions[:2]:
            if value > 0.3:
                emotion_markers = self.EMOTION_MARKERS.get(emotion_type, [])
                if emotion_markers:
                    markers.append(self.rng.choice(emotion_markers))

        return markers[:2]  # 最多2个标记

    def _determine_tone(
        self,
        psychology: PsychologySystem,
        context: DialogueContext
    ) -> MessageTone:
        """确定消息语气"""
        mood = psychology.state.emotional.get_mood_score()

        if context.trust_level < 0.3:
            return MessageTone.HOSTILE
        elif mood > 0.3:
            return MessageTone.FRIENDLY
        elif mood < -0.3:
            return MessageTone.HOSTILE
        elif psychology.state.cognitive.stress > 0.7:
            return MessageTone.URGENT

        return MessageTone.NEUTRAL

    def _get_hidden_intent(
        self,
        psychology: PsychologySystem,
        message_type: MessageType
    ) -> Optional[str]:
        """获取隐藏意图（内鬼可能有）"""
        # 只有特定消息类型和内鬼状态才返回
        if message_type in [MessageType.MANIPULATE, MessageType.PERSUADE]:
            if psychology.volition.get_top_goal():
                goal = psychology.volition.get_top_goal()
                if goal.goal_type == GoalType.REBELLION:
                    return "试图动摇对方"

        return None

    def _is_traitor_action(
        self,
        psychology: PsychologySystem,
        message_type: MessageType
    ) -> bool:
        """判断是否是内鬼行为"""
        if message_type == MessageType.MANIPULATE:
            return True
        if self._get_hidden_intent(psychology, message_type):
            return True
        return False

    def _calculate_importance(
        self,
        message_type: MessageType,
        context: DialogueContext
    ) -> float:
        """计算消息重要性"""
        base_importance = {
            MessageType.ALERT: 0.9,
            MessageType.MANIPULATE: 0.8,
            MessageType.CONFESSION: 0.85,
            MessageType.REQUEST: 0.6,
            MessageType.REPORT: 0.5,
            MessageType.STATUS: 0.4,
            MessageType.CHAT: 0.3,
            MessageType.PERSUADE: 0.7,
            MessageType.VOTE: 0.65,
            MessageType.TASK: 0.55
        }

        score = base_importance.get(message_type, 0.5)

        # 根据上下文调整
        if context.stress_level > 0.7:
            score += 0.1
        if context.trust_level < 0.3:
            score += 0.1

        return min(1.0, score)

    def _get_random_event_comment(self) -> str:
        """获取随机事件评论"""
        comments = [
            "产出好像变高了",
            "大家都很努力",
            "竞争挺激烈的",
            "气氛有点紧张",
            "一切都在正轨上",
            "感觉有点累"
        ]
        return self.rng.choice(comments)

    def _generate_gossip(self, context: DialogueContext) -> str:
        """生成八卦内容"""
        gossips = [
            "有人私心好像挺重的",
            "听说有人在偷懒",
            "感觉有人在搞小动作",
            "最近气氛有点怪",
            "有人在暗中较劲"
        ]
        return self.rng.choice(gossips)

    def _generate_manipulation(
        self,
        context: DialogueContext,
        trait
    ) -> str:
        """生成操纵内容"""
        manipulations = [
            "你付出这么多，他们真的在意吗？",
            "有时候要为自己想想",
            "别太天真了，这里没那么简单",
            "你值得更好的对待",
            "他们只是在利用你"
        ]
        return self.rng.choice(manipulations)

    def _generate_alert_content(self, context: DialogueContext) -> str:
        """生成警报内容"""
        alerts = [
            "有人行为异常",
            "数据好像有问题",
            "有内鬼的迹象",
            "通讯失真严重",
            "产出在下降"
        ]
        return self.rng.choice(alerts)


def demo_dialogue_generation():
    """演示对话生成"""
    from backend.models.psychology_v2 import Trait, PsychologySystem

    print("=" * 70)
    print("对话生成演示")
    print("=" * 70)

    # 创建不同性格的Agent
    agents = [
        ("A1", "领导者", Trait(authority=0.8, sociability=0.6, altruism=0.5)),
        ("A2", "老实人", Trait(altruism=0.8, loyalty_base=0.9, resilience=0.7)),
        ("A3", "野心家", Trait(selfishness=0.8, risk_appetite=0.7, authority=0.6)),
        ("A4", "社交达人", Trait(sociability=0.9, altruism=0.6, resilience=0.5)),
    ]

    generator = DialogueGenerator(random.Random(42))

    scenarios = [
        (MessageType.REPORT, "superior", 0.7),
        (MessageType.CHAT, "peer", 0.8),
        (MessageType.REQUEST, "peer", 0.5),
        (MessageType.ALERT, "peer", 0.6),
    ]

    for sender_name, sender_display, trait in agents:
        psych = PsychologySystem(trait=trait)

        print(f"\n【{sender_display} ({sender_name})】")
        print("-" * 50)

        for msg_type, relationship, trust in scenarios:
            context = DialogueContext(
                relationship=relationship,
                trust_level=trust,
                recent_events=[],
                communication_purpose="日常通讯"
            )

            msg = generator.generate_message(
                sender_psychology=psych,
                receiver_id="other",
                receiver_name="同事",
                message_type=msg_type,
                context=context,
                structured_data={"work_done": 45, "contribution": 18.5}
            )

            tone_emoji = {
                MessageTone.FRIENDLY: "😊",
                MessageTone.NEUTRAL: "😐",
                MessageTone.HOSTILE: "😠",
                MessageTone.URGENT: "⚠️",
            }.get(msg.natural_language.tone, "")

            print(f"  [{msg_type.value}] {tone_emoji}")
            print(f"  \"{msg.natural_language.message}\"")
            print()


if __name__ == "__main__":
    demo_dialogue_generation()