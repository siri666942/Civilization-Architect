"""
通讯消息模型

定义Agent间的通讯消息格式，支持JSON结构化数据 + 自然语言对话
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import json
import uuid


class MessageType(Enum):
    """消息类型"""
    REPORT = "report"           # 工作汇报
    TASK = "task"               # 任务分配
    REQUEST = "request"         # 资源请求
    STATUS = "status"           # 状态同步
    VOTE = "vote"               # 投票表决
    CHAT = "chat"               # 日常聊天
    PERSUADE = "persuade"       # 劝说
    MANIPULATE = "manipulate"   # 操纵（内鬼）
    ALERT = "alert"             # 警报
    CONFESSION = "confession"   # 告白/坦白


class MessageTone(Enum):
    """消息语气"""
    FRIENDLY = "friendly"       # 友好
    NEUTRAL = "neutral"         # 中性
    HOSTILE = "hostile"         # 敌对
    MANIPULATIVE = "manipulative"  # 操纵性
    URGENT = "urgent"           # 紧急
    SARCASTIC = "sarcastic"     # 讽刺
    ENCOURAGING = "encouraging" # 鼓励
    GUILTY = "guilty"           # 内疚


@dataclass
class StructuredContent:
    """结构化内容（JSON部分）"""
    # 通用字段
    work_done: Optional[float] = None
    contribution: Optional[float] = None
    energy_remaining: Optional[float] = None
    issues: List[str] = field(default_factory=list)
    sentiment: Optional[float] = None

    # 任务相关
    target_contribution: Optional[float] = None
    priority: Optional[str] = None
    resources_allocated: Optional[float] = None
    deadline: Optional[str] = None

    # 请求相关
    request_type: Optional[str] = None
    request_amount: Optional[float] = None
    request_reason: Optional[str] = None

    # 状态同步
    my_status: Optional[str] = None
    progress: Optional[float] = None
    need_help: Optional[bool] = None
    trust_offer: Optional[float] = None

    # 投票
    vote_target: Optional[str] = None
    vote_decision: Optional[bool] = None
    vote_reason: Optional[str] = None

    # 警报
    alert_type: Optional[str] = None
    alert_target: Optional[str] = None
    alert_severity: Optional[float] = None

    def to_dict(self) -> dict:
        """转换为字典，过滤None值"""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class NaturalLanguageContent:
    """自然语言内容（对话部分）"""
    message: str                          # 消息正文
    tone: MessageTone = MessageTone.NEUTRAL
    hidden_intent: Optional[str] = None   # 隐藏意图（内鬼可能有）
    emotion_markers: List[str] = field(default_factory=list)  # 情绪标记

    # 失真相关
    original_message: Optional[str] = None  # 原始消息（转发时）
    distortion_applied: float = 1.0         # 失真系数

    def to_dict(self) -> dict:
        return {
            "message": self.message,
            "tone": self.tone.value,
            "hidden_intent": self.hidden_intent,
            "emotion_markers": self.emotion_markers,
            "original_message": self.original_message,
            "distortion_applied": self.distortion_applied
        }


@dataclass
class Message:
    """
    完整消息

    一条消息包含：
    1. 元数据（发送者、接收者、时间戳等）
    2. 结构化内容（JSON）
    3. 自然语言内容（对话）
    """
    # 元数据
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    sender_id: str = ""
    sender_name: str = ""
    receiver_id: str = ""
    receiver_name: str = ""
    message_type: MessageType = MessageType.CHAT

    # 上下文
    civilization_id: str = ""
    round_num: int = 0
    cycle_num: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # 内容
    structured: Optional[StructuredContent] = None
    natural_language: Optional[NaturalLanguageContent] = None

    # 传播信息
    hop_count: int = 0                    # 经过了几跳
    path: List[str] = field(default_factory=list)  # 传播路径

    # 标记
    is_traitor_action: bool = False       # 是否是内鬼行为
    was_detected: bool = False            # 是否被检测到
    importance_score: float = 0.5         # 重要性分数（用于排序展示）

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "receiver_id": self.receiver_id,
            "receiver_name": self.receiver_name,
            "message_type": self.message_type.value,
            "civilization_id": self.civilization_id,
            "round_num": self.round_num,
            "cycle_num": self.cycle_num,
            "timestamp": self.timestamp,
            "structured": self.structured.to_dict() if self.structured else None,
            "natural_language": self.natural_language.to_dict() if self.natural_language else None,
            "hop_count": self.hop_count,
            "path": self.path,
            "is_traitor_action": self.is_traitor_action,
            "was_detected": self.was_detected,
            "importance_score": self.importance_score
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> 'Message':
        """从字典创建"""
        msg = cls(
            message_id=data.get("message_id", str(uuid.uuid4())[:8]),
            sender_id=data.get("sender_id", ""),
            sender_name=data.get("sender_name", ""),
            receiver_id=data.get("receiver_id", ""),
            receiver_name=data.get("receiver_name", ""),
            message_type=MessageType(data.get("message_type", "chat")),
            civilization_id=data.get("civilization_id", ""),
            round_num=data.get("round_num", 0),
            cycle_num=data.get("cycle_num", 0),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
            hop_count=data.get("hop_count", 0),
            path=data.get("path", []),
            is_traitor_action=data.get("is_traitor_action", False),
            was_detected=data.get("was_detected", False),
            importance_score=data.get("importance_score", 0.5)
        )

        if data.get("structured"):
            msg.structured = StructuredContent(**data["structured"])

        if data.get("natural_language"):
            nl_data = data["natural_language"]
            msg.natural_language = NaturalLanguageContent(
                message=nl_data.get("message", ""),
                tone=MessageTone(nl_data.get("tone", "neutral")),
                hidden_intent=nl_data.get("hidden_intent"),
                emotion_markers=nl_data.get("emotion_markers", []),
                original_message=nl_data.get("original_message"),
                distortion_applied=nl_data.get("distortion_applied", 1.0)
            )

        return msg


@dataclass
class ConversationThread:
    """
    对话线程

    将相关的消息组织成对话线程，便于前端展示
    """
    thread_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    civilization_id: str = ""
    participants: List[str] = field(default_factory=list)
    messages: List[Message] = field(default_factory=list)
    topic: str = ""
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_activity: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_message(self, message: Message):
        """添加消息到线程"""
        self.messages.append(message)
        self.last_activity = datetime.now().isoformat()

        # 确保参与者列表包含发送者和接收者
        if message.sender_id not in self.participants:
            self.participants.append(message.sender_id)
        if message.receiver_id not in self.participants:
            self.participants.append(message.receiver_id)

    def get_preview(self, max_length: int = 100) -> str:
        """获取对话预览"""
        if not self.messages:
            return "（空对话）"

        last_msg = self.messages[-1]
        if last_msg.natural_language:
            msg_text = last_msg.natural_language.message
            if len(msg_text) > max_length:
                return msg_text[:max_length] + "..."
            return msg_text
        return "（结构化消息）"

    def to_dict(self) -> dict:
        return {
            "thread_id": self.thread_id,
            "civilization_id": self.civilization_id,
            "participants": self.participants,
            "messages": [m.to_dict() for m in self.messages],
            "topic": self.topic,
            "started_at": self.started_at,
            "last_activity": self.last_activity,
            "preview": self.get_preview(),
            "message_count": len(self.messages)
        }