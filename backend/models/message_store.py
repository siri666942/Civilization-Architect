"""
消息存储系统

支持消息的存储、查询和管理
使用SQLite作为本地数据库，可扩展为其他数据库
"""

import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass
import os

from backend.models.message import Message, MessageType, ConversationThread


class MessageStore:
    """
    消息存储管理器

    使用SQLite存储消息，支持：
    1. 按时间、发送者、接收者查询
    2. 按消息类型筛选
    3. 按重要性排序
    4. 生成对话线程
    """

    def __init__(self, db_path: str = None):
        """
        初始化消息存储

        Args:
            db_path: 数据库文件路径，默认在项目目录下
        """
        if db_path is None:
            # 默认存储路径
            db_path = os.path.join(
                os.path.dirname(__file__),
                "..", "..", "data", "messages.db"
            )
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                sender_name TEXT,
                receiver_id TEXT NOT NULL,
                receiver_name TEXT,
                message_type TEXT NOT NULL,
                civilization_id TEXT,
                round_num INTEGER,
                cycle_num INTEGER,
                timestamp TEXT,
                structured_json TEXT,
                natural_language_json TEXT,
                hop_count INTEGER,
                path_json TEXT,
                is_traitor_action INTEGER,
                was_detected INTEGER,
                importance_score REAL
            )
        """)

        # 索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sender
            ON messages(sender_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_receiver
            ON messages(receiver_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_civilization
            ON messages(civilization_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_time
            ON messages(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_round_cycle
            ON messages(civilization_id, round_num, cycle_num)
        """)

        conn.commit()
        conn.close()

    def save_message(self, message: Message) -> bool:
        """
        保存消息到数据库

        Args:
            message: 消息对象

        Returns:
            是否保存成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO messages VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
            """, (
                message.message_id,
                message.sender_id,
                message.sender_name,
                message.receiver_id,
                message.receiver_name,
                message.message_type.value,
                message.civilization_id,
                message.round_num,
                message.cycle_num,
                message.timestamp,
                json.dumps(message.structured.to_dict()) if message.structured else None,
                json.dumps(message.natural_language.to_dict()) if message.natural_language else None,
                message.hop_count,
                json.dumps(message.path),
                1 if message.is_traitor_action else 0,
                1 if message.was_detected else 0,
                message.importance_score
            ))

            conn.commit()
            return True
        except Exception as e:
            print(f"保存消息失败: {e}")
            return False
        finally:
            conn.close()

    def get_messages_by_civilization(
        self,
        civilization_id: str,
        round_num: int = None,
        cycle_num: int = None,
        message_type: MessageType = None,
        limit: int = 100
    ) -> List[Message]:
        """
        获取指定文明的消息

        Args:
            civilization_id: 文明ID
            round_num: 回合号（可选）
            cycle_num: 循环号（可选）
            message_type: 消息类型（可选）
            limit: 返回数量限制

        Returns:
            消息列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM messages WHERE civilization_id = ?"
        params = [civilization_id]

        if round_num is not None:
            query += " AND round_num = ?"
            params.append(round_num)

        if cycle_num is not None:
            query += " AND cycle_num = ?"
            params.append(cycle_num)

        if message_type is not None:
            query += " AND message_type = ?"
            params.append(message_type.value)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_message(row) for row in rows]

    def get_conversation(
        self,
        agent1_id: str,
        agent2_id: str,
        civilization_id: str = None,
        limit: int = 50
    ) -> List[Message]:
        """
        获取两个Agent之间的对话

        Args:
            agent1_id: Agent1 ID
            agent2_id: Agent2 ID
            civilization_id: 文明ID（可选）
            limit: 返回数量限制

        Returns:
            消息列表（按时间正序）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT * FROM messages
            WHERE ((sender_id = ? AND receiver_id = ?)
                   OR (sender_id = ? AND receiver_id = ?))
        """
        params = [agent1_id, agent2_id, agent2_id, agent1_id]

        if civilization_id:
            query += " AND civilization_id = ?"
            params.append(civilization_id)

        query += " ORDER BY timestamp ASC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_message(row) for row in rows]

    def get_traitor_messages(
        self,
        civilization_id: str,
        include_detected: bool = True
    ) -> List[Message]:
        """
        获取内鬼相关消息

        Args:
            civilization_id: 文明ID
            include_detected: 是否包含已检测到的

        Returns:
            内鬼消息列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = """
            SELECT * FROM messages
            WHERE civilization_id = ? AND is_traitor_action = 1
        """
        params = [civilization_id]

        if not include_detected:
            query += " AND was_detected = 0"

        query += " ORDER BY timestamp DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_message(row) for row in rows]

    def get_important_messages(
        self,
        civilization_id: str,
        min_importance: float = 0.7,
        limit: int = 20
    ) -> List[Message]:
        """
        获取重要消息（用于展示）

        Args:
            civilization_id: 文明ID
            min_importance: 最小重要性分数
            limit: 返回数量限制

        Returns:
            重要消息列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM messages
            WHERE civilization_id = ? AND importance_score >= ?
            ORDER BY importance_score DESC, timestamp DESC
            LIMIT ?
        """, (civilization_id, min_importance, limit))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_message(row) for row in rows]

    def get_thread(
        self,
        agent1_id: str,
        agent2_id: str,
        civilization_id: str
    ) -> ConversationThread:
        """
        获取两个Agent之间的对话线程

        Args:
            agent1_id: Agent1 ID
            agent2_id: Agent2 ID
            civilization_id: 文明ID

        Returns:
            对话线程
        """
        messages = self.get_conversation(agent1_id, agent2_id, civilization_id)

        thread = ConversationThread(
            civilization_id=civilization_id,
            participants=[agent1_id, agent2_id]
        )

        for msg in messages:
            thread.add_message(msg)

        return thread

    def get_recent_activity(
        self,
        civilization_id: str,
        rounds: int = 1
    ) -> Dict:
        """
        获取最近活动摘要（用于前端展示）

        Args:
            civilization_id: 文明ID
            rounds: 最近几个回合

        Returns:
            活动摘要
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取最近回合号
        cursor.execute("""
            SELECT MAX(round_num) FROM messages
            WHERE civilization_id = ?
        """, (civilization_id,))
        result = cursor.fetchone()
        max_round = result[0] if result[0] else 0

        start_round = max(0, max_round - rounds + 1)

        # 统计消息
        cursor.execute("""
            SELECT
                message_type,
                COUNT(*) as count,
                AVG(importance_score) as avg_importance
            FROM messages
            WHERE civilization_id = ? AND round_num >= ?
            GROUP BY message_type
        """, (civilization_id, start_round))

        type_stats = {}
        for row in cursor.fetchall():
            type_stats[row[0]] = {
                "count": row[1],
                "avg_importance": row[2]
            }

        # 获取最近重要消息
        important = self.get_important_messages(civilization_id, limit=5)

        # 获取活跃Agent
        cursor.execute("""
            SELECT sender_id, sender_name, COUNT(*) as msg_count
            FROM messages
            WHERE civilization_id = ? AND round_num >= ?
            GROUP BY sender_id
            ORDER BY msg_count DESC
            LIMIT 5
        """, (civilization_id, start_round))

        active_agents = [
            {"id": row[0], "name": row[1], "message_count": row[2]}
            for row in cursor.fetchall()
        ]

        conn.close()

        return {
            "civilization_id": civilization_id,
            "rounds_covered": rounds,
            "message_type_stats": type_stats,
            "important_messages": [m.to_dict() for m in important],
            "active_agents": active_agents
        }

    def clear_old_messages(self, keep_rounds: int = 10):
        """
        清理旧消息（只保留最近N回合）

        Args:
            keep_rounds: 保留的回合数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取最大回合号
        cursor.execute("SELECT MAX(round_num) FROM messages")
        result = cursor.fetchone()
        max_round = result[0] if result[0] else 0

        if max_round > keep_rounds:
            delete_before = max_round - keep_rounds
            cursor.execute(
                "DELETE FROM messages WHERE round_num < ?",
                (delete_before,)
            )
            conn.commit()

        conn.close()

    def _row_to_message(self, row) -> Message:
        """将数据库行转换为Message对象"""
        message = Message(
            message_id=row[0],
            sender_id=row[1],
            sender_name=row[2],
            receiver_id=row[3],
            receiver_name=row[4],
            message_type=MessageType(row[5]),
            civilization_id=row[6],
            round_num=row[7],
            cycle_num=row[8],
            timestamp=row[9],
            hop_count=row[12],
            path=json.loads(row[13]) if row[13] else [],
            is_traitor_action=bool(row[14]),
            was_detected=bool(row[15]),
            importance_score=row[16]
        )

        if row[10]:
            from backend.models.message import StructuredContent
            message.structured = StructuredContent(**json.loads(row[10]))

        if row[11]:
            from backend.models.message import NaturalLanguageContent, MessageTone
            nl_data = json.loads(row[11])
            message.natural_language = NaturalLanguageContent(
                message=nl_data.get("message", ""),
                tone=MessageTone(nl_data.get("tone", "neutral")),
                hidden_intent=nl_data.get("hidden_intent"),
                emotion_markers=nl_data.get("emotion_markers", []),
                original_message=nl_data.get("original_message"),
                distortion_applied=nl_data.get("distortion_applied", 1.0)
            )

        return message


# 全局消息存储实例
_message_store: Optional[MessageStore] = None


def get_message_store() -> MessageStore:
    """获取全局消息存储实例"""
    global _message_store
    if _message_store is None:
        _message_store = MessageStore()
    return _message_store