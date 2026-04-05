# 文明架构师 - 完整网站

一个基于 React + FastAPI 的 Agent 文明模拟策略游戏。

## 技术栈

### 前端
- React 18 + TypeScript
- Tailwind CSS (赛博朋克主题)
- Framer Motion (动画)
- Zustand (状态管理)
- React Router (路由)

### 后端
- FastAPI (Python Web框架)
- WebSocket (实时通讯)
- NumPy (数值计算)

## 项目结构

```
muti-agent-stimulation/
├── backend/                    # Python 后端
│   ├── api/
│   │   ├── game_api.py            # 游戏控制API
│   │   ├── communication_api.py   # 通讯系统
│   │   └── communication_api_v2.py
│   ├── core/
│   │   ├── engine.py              # 游戏引擎
│   │   ├── dialogue_generator.py  # 对话生成
│   │   └── macro_variables.py     # 宏观变量计算
│   ├── models/
│   │   ├── agent.py               # Agent模型
│   │   └── architecture.py        # 架构模型
│   └── common/
│       └── config.py              # 配置管理
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── pages/                 # 页面组件
│   │   │   ├── StartPage.tsx      # 开始页面
│   │   │   ├── SelectPage.tsx     # 选择架构页面
│   │   │   ├── EditorPage.tsx     # 架构编辑页面
│   │   │   └── ResultPage.tsx     # 结算页面
│   │   ├── stores/                # 状态管理
│   │   ├── services/              # API服务
│   │   ├── types/                 # TypeScript类型
│   │   └── styles/                # 全局样式
│   └── package.json
└── server.py                   # FastAPI 入口
```

## 快速开始

### 1. 安装后端依赖

```bash
pip install fastapi uvicorn scipy numpy pydantic
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 启动后端服务

```bash
cd ..
python server.py
```

后端服务将运行在 http://localhost:8000

### 4. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

前端服务将运行在 http://localhost:3000

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

## 游戏流程

1. **开始页面**: 输入指挥官代号
2. **选择架构页面**: 阅读故事背景和Agent特点，选择组织架构
3. **架构编辑页面**: 拖拽Agent到架构位置，执行模拟，观察聊天和数值变化
4. **结算页面**: 查看最终星辰值、成就和分析报告

## 核心功能

### 架构类型
- **树形架构**: 层级分明，信息自上而下流动
- **星形架构**: 中心节点连接所有其他节点
- **网状架构**: 所有节点互相连接

### Agent 属性
- 八维性格: 权威感度、私心倾向、韧性、利他性、社交性、风险偏好、智力、忠诚度
- 动态状态: 体力、认知熵、忠诚度、贡献值

### 宏观变量
- 能级 (Energy Level)
- 凝聚力 (Cohesion)
- 信息保真度 (Fidelity)
- 社会资本 (Social Capital)

## 构建生产版本

```bash
cd frontend
npm run build
```

构建后的文件将输出到 `frontend/dist`，可直接通过后端服务提供静态文件服务。