# 智械星海：戴森球拓荒者

> **基于大语言模型的多智能体社会动力学博弈模拟器**
>
> Intelligence Star-Sea: Dyson Sphere Pioneers

---

## 项目简介

这是一个基于大语言模型（LLM）的多智能体博弈模拟系统，模拟多个AI文明在戴森球拓荒过程中的社会动力学交互。玩家作为文明缔造者，设计AI文明的组织架构（拓扑结构），观察不同架构在压力下的涌现行为。

**核心体验**：见证"一个完美的独裁者如何因为一个内鬼的提示词导致帝国崩塌"，探索"群体智慧"与"组织坍塌"的社会实验。

---

## 核心特性

### 八维性格系统
基于大五人格理论和黑暗三联征研究，每个Agent拥有8个性格维度：
- 权威感度、私心倾向、韧性、利他性
- 社交性、风险偏好、智力、忠诚度基准

### 四种组织架构
| 架构 | 结构特征 | 优势 | 劣势 |
|------|---------|------|------|
| **星形架构** | 单核心中心 | 指令传达快，决策效率高 | 核心受损则全盘崩溃 |
| **树形架构** | 层级分明 | 分工明确，管理有序 | 信息传递有损耗 |
| **全网状架构** | 所有节点互联 | 鲁棒性极强 | 信息过载，容易内耗 |
| **部落架构** | 多个隔离小组 | 多样性高 | 协作困难，资源分散 |

### 内鬼机制
- **涌现式**：AI自主决定是否成为内鬼
- **提示词注入**：内鬼通过通讯链路诱导其他Agent叛变
- **六种行为**：篡改、注入、怠工、挪用、煽动、泄露

### 神经网络式交互
- 神经元 ↔ Agent
- 突触权重 ↔ 信任度
- 前向传播 ↔ 信息传递
- 反向传播 ↔ 信任更新

---

## 技术栈

### 后端
- **Python 3.11**
- **FastAPI** - Web框架
- **NumPy / SciPy** - 数值计算
- **Pydantic** - 数据验证

### 前端
- **React 18 + TypeScript**
- **Tailwind CSS** - 赛博朋克主题
- **Framer Motion** - 动画
- **Zustand** - 状态管理
- **React Router** - 路由
- **@xyflow/react** - 架构图可视化
- **@dnd-kit** - 拖拽交互

---

## 项目结构

```
muti-agent-stimulation/
├── backend/                    # Python 后端
│   ├── api/                    # API 路由
│   │   ├── game_api.py         # 游戏控制API
│   │   ├── communication_api.py # 通讯系统API
│   │   └── communication_api_v2.py
│   ├── core/                   # 核心逻辑
│   │   ├── engine.py           # 游戏引擎
│   │   ├── god_agent.py        # 上帝Agent（性格生成）
│   │   ├── macro_variables.py  # 宏观变量计算
│   │   └── dialogue_generator.py # 对话生成
│   ├── models/                 # 数据模型
│   │   ├── agent.py            # Agent模型
│   │   ├── architecture.py     # 架构模型
│   │   ├── message.py          # 消息模型
│   │   └── psychology_v2.py    # 心理模型
│   ├── common/                 # 通用模块
│   │   ├── config.py           # 配置管理
│   │   └── param_levels.py     # 参数等级
│   └── tests/                  # 测试模块
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── pages/              # 页面组件
│   │   │   ├── StartPage.tsx   # 开始页面
│   │   │   ├── SelectPage.tsx  # 选择架构
│   │   │   ├── EditorPage.tsx  # 架构编辑
│   │   │   └── ResultPage.tsx  # 结算页面
│   │   ├── stores/             # 状态管理
│   │   ├── services/           # API服务
│   │   ├── types/              # TypeScript类型
│   │   └── styles/             # 全局样式
│   └── package.json
├── server.py                   # FastAPI 入口
└── 设计文档.md                  # 详细设计文档
```

---

## 快速开始

### 环境要求
- Python 3.11+
- Node.js 18+

### 1. 克隆项目

```bash
git clone <repository-url>
cd muti-agent-stimulation
```

### 2. 安装后端依赖

```bash
pip install fastapi uvicorn scipy numpy pydantic
```

### 3. 安装前端依赖

```bash
cd frontend
npm install
cd ..
```

### 4. 启动服务

**启动后端（端口 8000）：**
```bash
python server.py
```

**启动前端开发服务器（端口 3000）：**
```bash
cd frontend
npm run dev
```

**或使用启动脚本：**
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

### 5. 访问应用

- 前端：http://localhost:3000
- 后端API：http://localhost:8000
- API文档：http://localhost:8000/docs

---

## 游戏流程

1. **开始页面**：输入指挥官代号
2. **选择架构**：阅读故事背景和Agent特点，选择组织架构
3. **架构编辑**：拖拽Agent到架构位置，执行模拟，观察聊天和数值变化
4. **结算页面**：查看最终星辰值、成就和分析报告

---

## API 接口

### 游戏控制

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/game/start` | POST | 开始新游戏 |
| `/api/v1/game/{game_id}/status` | GET | 获取游戏状态 |
| `/api/v1/game/{game_id}/update-architecture` | POST | 更新架构配置 |
| `/api/v1/game/{game_id}/run-round` | POST | 执行一轮模拟 |
| `/api/v1/game/{game_id}/end` | POST | 结束游戏 |

### 通讯系统

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/messages` | GET | 获取消息列表 |
| `/api/v1/conversations/{agent1}/{agent2}` | GET | 获取对话详情 |
| `/api/v1/civilizations/{id}/activity` | GET | 获取文明活动 |
| `/api/v1/civilizations/{id}/timeline` | GET | 获取时间线 |
| `/api/v1/civilizations/{id}/traitor-messages` | GET | 内鬼消息追踪 |

---

## 核心机制

### 宏观变量

| 变量 | 说明 | 计算公式 |
|------|------|----------|
| **能级** | 文明活跃程度 | 平均(体力 × 效率) |
| **向心力** | 组织凝聚力 | 平均忠诚度 × (1 - 忠诚度方差) |
| **信息保真度** | 信息传播质量 | 平均通讯准确性 |
| **社会资本** | 协作能力 | 平均信任 + 网络密度 |

### 最终产出公式

```
产出 = Σ(干活体力 × 转化率)
       × 能级系数
       × 向心力系数
       × 保真度系数
       × 社会资本系数
```

---

## 文档索引

| 文档 | 内容 |
|------|------|
| [游戏介绍.md](游戏介绍.md) | 游戏背景、玩法介绍 |
| [设计文档.md](设计文档.md) | 系统设计、核心机制 |
| [机制总览.md](机制总览.md) | 系统架构图、公式速查 |
| [参数定义总表.md](参数定义总表.md) | 所有参数的完整定义 |
| [架构文档.md](架构文档.md) | 后端架构详细说明 |
| [API接口文档.md](API接口文档.md) | 通讯系统API文档 |
| [UI设计规范文档.md](UI设计规范文档.md) | 前端设计规范 |

### 机制详解文档
- [机制详解_01_上帝Agent系统.md](机制详解_01_上帝Agent系统.md)
- [机制详解_02_Agent微观变量系统.md](机制详解_02_Agent微观变量系统.md)
- [机制详解_03_架构与通达度系统.md](机制详解_03_架构与通达度系统.md)
- [机制详解_04_通讯与信息传播系统.md](机制详解_04_通讯与信息传播系统.md)
- [机制详解_05_宏观变量与产出公式.md](机制详解_05_宏观变量与产出公式.md)
- [机制详解_06_神经网络式交互模型.md](机制详解_06_神经网络式交互模型.md)
- [机制详解_07_内鬼机制量化.md](机制详解_07_内鬼机制量化.md)

---

## 科学理论基础

本游戏的设计综合了以下理论：

- **大五人格理论**（Costa & McCrae, 1992）- 性格维度设计
- **黑暗三联征**（Paulhus & Williams, 2002）- 内鬼倾向设计
- **社会学习理论**（Bandura, 1977）- 信任更新机制
- **认知负荷理论**（Sweller, 1988）- 认知熵机制
- **认知失调理论**（Festinger, 1957）- 忠诚度变化
- **社会网络理论**（Granovetter, 1973）- 架构设计
- **图神经网络**（Scarselli et al., 2009）- 交互模型

---

## 构建生产版本

```bash
cd frontend
npm run build
```

构建后的文件将输出到 `frontend/dist`，可通过后端服务提供静态文件服务。

---

## 版本规划

| 版本 | 功能 |
|------|------|
| **MVP** | 3文明竞争、4架构、10Agent/文明、内鬼机制 |
| **V1.0** | 回合间架构调整、事件机制 |
| **V1.5** | 多文明交互（派内鬼、交易、结盟） |
| **V2.0** | 更多架构类型、扩展性格维度 |

---

## 许可证

MIT License

---

**准备好构建你的架构，开始这场星海拓荒了吗？**
