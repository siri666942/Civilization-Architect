# 通讯系统 API 接口文档

> 版本: 1.0
> 基础路径: `/api/v1`

---

## 概述

通讯系统API提供Agent间消息的存储、查询和展示功能，支持前端构建聊天界面、时间线视图、内鬼追踪等功能。

---

## 1. 消息列表接口

### GET `/messages`

获取文明的消息列表，支持分页和筛选。

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| civilization_id | string | ✅ | 文明ID |
| round_num | int | ❌ | 筛选回合号 |
| cycle_num | int | ❌ | 筛选循环号 |
| message_type | string | ❌ | 消息类型: report/chat/request/alert... |
| min_importance | float | ❌ | 最小重要性分数 (0-1) |
| limit | int | ❌ | 返回数量，默认50 |
| offset | int | ❌ | 分页偏移量，默认0 |

**响应示例**

```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "message_id": "abc123",
        "sender_name": "A1-领导者",
        "receiver_name": "A3-老实人",
        "message_type": "report",
        "preview": "这轮干得挺顺的，45个单位到手！感觉还不错~",
        "tone": "friendly",
        "timestamp": "2026-04-05T10:30:00",
        "importance": 0.5,
        "is_traitor": false
      }
    ],
    "total": 1,
    "has_more": false
  },
  "timestamp": "2026-04-05T10:30:00"
}
```

---

## 2. 对话详情接口

### GET `/conversations/{agent1_id}/{agent2_id}`

获取两个Agent之间的完整对话记录。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| agent1_id | string | Agent1 ID |
| agent2_id | string | Agent2 ID |

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| civilization_id | string | ✅ | 文明ID |
| limit | int | ❌ | 消息数量限制，默认100 |

**响应示例**

```json
{
  "success": true,
  "data": {
    "thread_id": "xyz789",
    "participants": [
      {"id": "A1", "name": "A1-领导者"},
      {"id": "A3", "name": "A3-老实人"}
    ],
    "messages": [
      {
        "message_id": "msg001",
        "sender_id": "A1",
        "sender_name": "A1-领导者",
        "receiver_id": "A3",
        "receiver_name": "A3-老实人",
        "message_type": "report",
        "cycle_num": 5,
        "natural_language": {
          "message": "这轮干得挺顺的，45个单位到手！",
          "tone": "friendly",
          "emotion_markers": ["不错", "棒"]
        }
      }
    ],
    "topic": "A1与A3的对话",
    "message_count": 12,
    "last_activity": "2026-04-05T10:35:00"
  }
}
```

---

## 3. 文明活动接口

### GET `/civilizations/{civilization_id}/activity`

获取文明的活动摘要，适合首页展示。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| civilization_id | string | 文明ID |

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| rounds | int | 统计最近几回合，默认3 |

**响应示例**

```json
{
  "success": true,
  "data": {
    "civilization_id": "CIV-001",
    "total_messages": 156,
    "active_agents": [
      {"id": "A1", "name": "领导者", "message_count": 45},
      {"id": "A3", "name": "老实人", "message_count": 38}
    ],
    "recent_important": [
      {
        "message_id": "msg999",
        "sender_name": "A5",
        "natural_language": {
          "message": "警报！有人行为异常！"
        }
      }
    ],
    "traitor_alerts": 3,
    "mood_distribution": {
      "friendly": 0.45,
      "neutral": 0.30,
      "hostile": 0.15,
      "urgent": 0.10
    }
  }
}
```

---

## 4. 内鬼消息接口

### GET `/civilizations/{civilization_id}/traitor-messages`

获取内鬼相关消息，用于内鬼追踪功能。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| civilization_id | string | 文明ID |

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| include_detected | bool | 是否包含已检测到的，默认false |

**响应示例**

```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "message_id": "tm001",
        "sender_name": "A7-野心家",
        "receiver_name": "A3-老实人",
        "message_type": "manipulate",
        "natural_language": {
          "message": "你付出这么多，他们真的在意吗？",
          "tone": "manipulative",
          "hidden_intent": "试图动摇对方"
        },
        "was_detected": false
      }
    ],
    "total": 5,
    "undetected_count": 3
  }
}
```

---

## 5. 时间线接口

### GET `/civilizations/{civilization_id}/timeline`

获取消息时间线，用于可视化展示。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| civilization_id | string | 文明ID |

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| round_num | int | 回合号，默认最近回合 |

**响应示例**

```json
{
  "success": true,
  "data": {
    "civilization_id": "CIV-001",
    "round_num": 5,
    "timeline": {
      "1": [
        {"message_id": "m1", "sender_name": "A1", "natural_language": {...}},
        {"message_id": "m2", "sender_name": "A2", "natural_language": {...}}
      ],
      "2": [
        {"message_id": "m3", "sender_name": "A3", "natural_language": {...}}
      ]
    },
    "total_messages": 25
  }
}
```

---

## 6. 热门对话接口

### GET `/civilizations/{civilization_id}/hot-conversations`

获取最活跃的对话，用于展示推荐。

**路径参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| civilization_id | string | 文明ID |

**查询参数**

| 参数 | 类型 | 说明 |
|------|------|------|
| limit | int | 返回数量，默认5 |

**响应示例**

```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "participants": [
          {"id": "A1", "name": "领导者"},
          {"id": "A3", "name": "老实人"}
        ],
        "message_count": 28,
        "preview": "这轮干得挺顺的...",
        "last_activity": "2026-04-05T10:35:00"
      }
    ]
  }
}
```

---

## 消息类型说明

| 类型 | 说明 | 典型场景 |
|------|------|---------|
| report | 工作汇报 | Agent向上级汇报工作进展 |
| task | 任务分配 | 上级向下级分配任务 |
| request | 资源请求 | 请求帮助或资源 |
| status | 状态同步 | 同级之间同步状态 |
| chat | 日常聊天 | 社交对话 |
| persuade | 劝说 | 试图说服对方 |
| manipulate | 操纵 | 内鬼操纵行为 |
| alert | 警报 | 发现异常报警 |
| confession | 坦白 | 认错或揭露 |
| vote | 投票 | 集体决策 |

---

## 语气类型说明

| 语气 | Emoji | 说明 |
|------|-------|------|
| friendly | 😊 | 友好、积极 |
| neutral | 😐 | 中性、客观 |
| hostile | 😠 | 敌对、不满 |
| manipulative | 🎭 | 操纵性、有隐藏意图 |
| urgent | ⚠️ | 紧急、重要 |
| sarcastic | 😏 | 讽刺、阴阳怪气 |
| encouraging | 💪 | 鼓励、支持 |
| guilty | 😔 | 内疚、愧疚 |

---

## 错误响应

所有接口错误时返回统一格式：

```json
{
  "success": false,
  "data": null,
  "error": "错误描述信息",
  "timestamp": "2026-04-05T10:30:00"
}
```

---

## 前端集成示例

### React组件示例

```jsx
// 消息列表组件
function MessageList({ civilizationId }) {
  const [messages, setMessages] = useState([]);

  useEffect(() => {
    fetch(`/api/v1/messages?civilization_id=${civilizationId}`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setMessages(data.data.messages);
        }
      });
  }, [civilizationId]);

  return (
    <div className="message-list">
      {messages.map(msg => (
        <MessageCard key={msg.message_id} message={msg} />
      ))}
    </div>
  );
}

// 消息卡片
function MessageCard({ message }) {
  const toneEmoji = {
    friendly: '😊',
    neutral: '😐',
    hostile: '😠',
    urgent: '⚠️'
  }[message.tone] || '';

  return (
    <div className={`message-card ${message.tone}`}>
      <div className="header">
        <span className="sender">{message.sender_name}</span>
        <span className="tone">{toneEmoji}</span>
      </div>
      <div className="preview">{message.preview}</div>
      <div className="meta">
        <span className="type">{message.message_type}</span>
        <span className="time">{message.timestamp}</span>
      </div>
    </div>
  );
}
```

### Vue组件示例

```vue
<template>
  <div class="conversation-view">
    <div class="messages" ref="messagesContainer">
      <div
        v-for="msg in messages"
        :key="msg.message_id"
        :class="['message', msg.sender_id === currentAgent ? 'sent' : 'received']"
      >
        <div class="sender">{{ msg.sender_name }}</div>
        <div class="content">
          {{ msg.natural_language.message }}
          <div class="markers">
            <span v-for="marker in msg.natural_language.emotion_markers">
              {{ marker }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['agent1Id', 'agent2Id', 'civilizationId'],
  data() {
    return {
      messages: [],
      currentAgent: this.agent1Id
    }
  },
  mounted() {
    this.loadConversation();
  },
  methods: {
    async loadConversation() {
      const res = await fetch(
        `/api/v1/conversations/${this.agent1Id}/${this.agent2Id}?civilization_id=${this.civilizationId}`
      );
      const data = await res.json();
      if (data.success) {
        this.messages = data.data.messages;
      }
    }
  }
}
</script>
```

---

## 数据存储

消息存储在SQLite数据库中，路径：`data/messages.db`

### 表结构

```sql
CREATE TABLE messages (
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
);
```

---

## 使用流程

```
1. 模拟运行时，Agent产生消息 → 调用 MessageStore.save_message()
2. 前端请求消息列表 → 调用 CommunicationAPI.get_messages()
3. 前端展示对话详情 → 调用 CommunicationAPI.get_conversation()
4. 监控内鬼活动 → 调用 CommunicationAPI.get_traitor_messages()
5. 可视化时间线 → 调用 CommunicationAPI.get_timeline()
```

---

*API文档版本: 1.0*
*更新日期: 2026-04-05*