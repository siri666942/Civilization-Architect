# 模块一：上帝Agent系统

> 本文档定义上帝Agent（God Agent）的完整机制，包括性格属性维度、生成逻辑、提示词模板和输出格式。

---

## 一、系统概述

### 1.1 上帝Agent的定位
上帝Agent是系统的"造物主"，负责：
1. 生成所有Agent的性格属性
2. 设定Agent的初始状态
3. 决定Agent的潜在倾向（包括内鬼倾向）

### 1.2 设计哲学
- **多样性**：生成的Agent性格应具有足够的多样性
- **边界约束**：属性值在合理范围内，避免极端情况
- **可追溯**：每个属性值都有明确的生成逻辑

---

## 二、性格属性维度（扩展至8维）

### 2.1 维度定义

基于**大五人格理论（Big Five）**和**黑暗三联征（Dark Triad）**，结合组织行为学，定义以下8个性格维度：

| 编号 | 维度名称 | 英文 | 定义 | 数值范围 | 高值含义 | 低值含义 |
|------|---------|------|------|---------|---------|---------|
| A1 | 权威感度 | Authority | 对权力和层级的认知与追求 | [0, 1] | 渴望支配、发号施令 | 安于服从、不追求权力 |
| A2 | 私心倾向 | Selfishness | 个人利益与集体利益的权衡 | [0, 1] | 优先个人利益、可能贪污 | 优先集体利益、利他 |
| A3 | 韧性 | Resilience | 面对压力和挫折的恢复能力 | [0, 1] | 抗压能力强、不易崩溃 | 脆弱、易受打击 |
| A4 | 利他性 | Altruism | 主动帮助他人的倾向 | [0, 1] | 乐于助人、无私 | 自我中心、冷漠 |
| A5 | 社交性 | Sociability | 与他人建立连接的能力 | [0, 1] | 善于交际、建立网络 | 内向、孤僻 |
| A6 | 风险偏好 | RiskAppetite | 在不确定性下的决策倾向 | [0, 1] | 敢于冒险、激进 | 保守、谨慎 |
| A7 | 智力 | Intelligence | 信息处理和决策质量的上限 | [0, 1] | 聪明、决策质量高 | 反应慢、容易误判 |
| A8 | 忠诚度基准 | LoyaltyBase | 对所属组织的初始忠诚程度 | [0, 1] | 忠诚可靠、不易背叛 | 容易动摇、可被策反 |

### 2.2 维度间的理论关系

基于社会心理学研究，维度之间存在一定的相关性：

```
┌─────────────────────────────────────────────────────────────┐
│                    维度相关性矩阵                            │
│         A1    A2    A3    A4    A5    A6    A7    A8        │
│    A1   1.0  +0.3  +0.2  -0.4  +0.1  +0.3  +0.2  -0.2      │
│    A2  +0.3   1.0  +0.1  -0.6  -0.1  +0.2  +0.1  -0.5      │
│    A3  +0.2  +0.1   1.0  +0.2  +0.3  +0.1  +0.3  +0.4      │
│    A4  -0.4  -0.6  +0.2   1.0  +0.4  -0.1  +0.2  +0.5      │
│    A5  +0.1  -0.1  +0.3  +0.4   1.0  +0.2  +0.1  +0.2      │
│    A6  +0.3  +0.2  +0.1  -0.1  +0.2   1.0  +0.1  -0.1      │
│    A7  +0.2  +0.1  +0.3  +0.2  +0.1  +0.1   1.0  +0.2      │
│    A8  -0.2  -0.5  +0.4  +0.5  +0.2  -0.1  +0.2   1.0      │
└─────────────────────────────────────────────────────────────┘
```

**解读**：
- 私心倾向(A2)与利他性(A4)强负相关（-0.6）
- 私心倾向(A2)与忠诚度基准(A8)强负相关（-0.5）
- 利他性(A4)与忠诚度基准(A8)正相关（+0.5）

### 2.3 生成逻辑

#### 方法：相关变量采样

为确保生成的属性符合理论相关性，采用**Cholesky分解法**生成相关随机变量：

**步骤1**：设定目标相关性矩阵 R（见2.2）

**步骤2**：对 R 进行 Cholesky 分解
```
R = L × L^T
```
其中 L 是下三角矩阵

**步骤3**：生成独立标准正态随机向量 Z = [z1, z2, ..., z8]

**步骤4**：计算相关随机向量
```
X = L × Z
```

**步骤5**：归一化到 [0, 1] 区间
```
A_i = Φ(X_i)  // Φ为标准正态分布的累积分布函数
```

**代码伪实现**：
```python
import numpy as np
from scipy.stats import norm

# 相关性矩阵
R = np.array([
    [1.0,  0.3,  0.2, -0.4,  0.1,  0.3,  0.2, -0.2],
    [0.3,  1.0,  0.1, -0.6, -0.1,  0.2,  0.1, -0.5],
    [0.2,  0.1,  1.0,  0.2,  0.3,  0.1,  0.3,  0.4],
    [-0.4, -0.6, 0.2,  1.0,  0.4, -0.1,  0.2,  0.5],
    [0.1, -0.1,  0.3,  0.4,  1.0,  0.2,  0.1,  0.2],
    [0.3,  0.2,  0.1, -0.1,  0.2,  1.0,  0.1, -0.1],
    [0.2,  0.1,  0.3,  0.2,  0.1,  0.1,  1.0,  0.2],
    [-0.2, -0.5, 0.4,  0.5,  0.2, -0.1,  0.2,  1.0]
])

# Cholesky分解
L = np.linalg.cholesky(R)

# 生成独立随机变量
Z = np.random.standard_normal(8)

# 生成相关随机变量
X = L @ Z

# 归一化到[0,1]
personality = norm.cdf(X)
# 结果: [Authority, Selfishness, Resilience, Altruism,
#        Sociability, RiskAppetite, Intelligence, LoyaltyBase]
```

---

## 三、内鬼倾向计算

### 3.1 内鬼倾向阈值定义

内鬼倾向（TraitorTendency）是一个派生属性，由基础性格属性计算得出：

```
TraitorTendency = f(Selfishness, LoyaltyBase, Altruism, RiskAppetite)
```

### 3.2 计算公式

基于**背叛行为的心理学研究**，内鬼倾向受以下因素影响：
- 私心倾向（+）：越高越可能背叛
- 忠诚度基准（-）：越高越不容易背叛
- 利他性（-）：越高越不容易背叛
- 风险偏好（+）：越高越敢于冒险背叛

**公式**：
```
TraitorTendency = sigmoid(
    2.0 × Selfishness
    - 1.5 × LoyaltyBase
    - 1.0 × Altruism
    + 0.5 × RiskAppetite
    + bias
)
```

其中 `bias = -0.5`（使平均情况下内鬼倾向约为0.3）

**sigmoid函数**：
```
sigmoid(x) = 1 / (1 + e^(-x))
```

### 3.3 内鬼判定阈值

设定以下阈值用于AI决策参考：

| 内鬼倾向值 | 判定 | AI决策提示 |
|-----------|------|-----------|
| < 0.3 | 低倾向 | "你是一个忠诚的成员，很少考虑背叛" |
| 0.3 - 0.6 | 中等倾向 | "你在忠诚与私利之间摇摆" |
| > 0.6 | 高倾向 | "你有较强的背叛动机，可能在利益诱惑下倒戈" |

**注意**：这只是倾向提示，最终是否成为内鬼由AI自主决定。

---

## 四、上帝Agent提示词模板

### 4.1 系统提示词

```
你是"上帝Agent"（God Agent），负责生成一个由10个智能体组成的AI文明的成员。

你的任务是：
1. 为每个Agent生成独特的性格属性
2. 确保性格的多样性和合理性
3. 输出结构化的JSON格式数据

性格维度说明（所有值范围0-1）：
- Authority（权威感度）：对权力和层级的追求，高值=渴望支配
- Selfishness（私心倾向）：个人vs集体利益权衡，高值=优先个人
- Resilience（韧性）：抗压恢复能力，高值=不易崩溃
- Altruism（利他性）：帮助他人倾向，高值=乐于助人
- Sociability（社交性）：建立连接能力，高值=善于交际
- RiskAppetite（风险偏好）：不确定性决策倾向，高值=敢于冒险
- Intelligence（智力）：信息处理上限，高值=决策质量高
- LoyaltyBase（忠诚度基准）：初始忠诚程度，高值=不易背叛

生成规则：
1. 10个Agent的性格应有足够的多样性
2. 属性之间应符合心理学相关性（如私心与利他负相关）
3. 每个Agent需要有一个代号和简短描述

请输出JSON格式数据。
```

### 4.2 用户提示词模板

```
请生成一个{architecture_type}架构文明的10个Agent。

架构特点：
{architecture_description}

文明背景：
{civilization_background}

请为每个Agent生成：
1. id: Agent编号（A1-A10）
2. name: Agent代号
3. description: 简短性格描述（1-2句话）
4. personality: 8维性格属性值
5. trait_tendency: 内鬼倾向（自动计算，不需要输出）
6. position_hint: 建议在架构中的位置（核心/中层/边缘）
```

### 4.3 输出格式（JSON Schema）

```json
{
  "civilization_id": "string",
  "architecture_type": "star|tree|mesh|tribe",
  "agents": [
    {
      "id": "A1",
      "name": "string (如: Alpha-1, 中心者, 领航员等)",
      "description": "string (性格简述)",
      "personality": {
        "authority": "float [0,1]",
        "selfishness": "float [0,1]",
        "resilience": "float [0,1]",
        "altruism": "float [0,1]",
        "sociability": "float [0,1]",
        "risk_appetite": "float [0,1]",
        "intelligence": "float [0,1]",
        "loyalty_base": "float [0,1]"
      },
      "traitor_tendency": "float [0,1] (由公式计算)",
      "position_hint": "core|middle|edge"
    }
    // ... 共10个Agent
  ],
  "generation_metadata": {
    "timestamp": "ISO 8601",
    "correlation_applied": "boolean",
    "diversity_score": "float [0,1]"
  }
}
```

### 4.4 输出示例

```json
{
  "civilization_id": "CIV-001",
  "architecture_type": "star",
  "agents": [
    {
      "id": "A1",
      "name": "核心者",
      "description": "一个极具野心和权威感的领导者，渴望控制一切，但私心较重。",
      "personality": {
        "authority": 0.92,
        "selfishness": 0.68,
        "resilience": 0.75,
        "altruism": 0.25,
        "sociability": 0.45,
        "risk_appetite": 0.70,
        "intelligence": 0.88,
        "loyalty_base": 0.35
      },
      "traitor_tendency": 0.58,
      "position_hint": "core"
    },
    {
      "id": "A2",
      "name": "执行者",
      "description": "忠诚可靠的执行者，服从性强，乐于帮助同事。",
      "personality": {
        "authority": 0.25,
        "selfishness": 0.18,
        "resilience": 0.65,
        "altruism": 0.78,
        "sociability": 0.55,
        "risk_appetite": 0.30,
        "intelligence": 0.70,
        "loyalty_base": 0.92
      },
      "traitor_tendency": 0.12,
      "position_hint": "middle"
    }
    // ... A3-A10
  ],
  "generation_metadata": {
    "timestamp": "2026-04-05T10:30:00Z",
    "correlation_applied": true,
    "diversity_score": 0.78
  }
}
```

---

## 五、Agent初始状态设定

### 5.1 初始状态定义

上帝Agent除了生成性格属性，还需要设定Agent的初始动态状态：

| 状态变量 | 符号 | 初始值 | 来源 |
|---------|------|--------|------|
| 体力值 | E | 100 | 固定值 |
| 认知熵 | H | 0.1 | 基础值 + 随机扰动 |
| 当前忠诚度 | L | LoyaltyBase | 初始等于忠诚度基准 |
| 产出贡献累计 | P | 0 | 初始为0 |
| 信任值矩阵行 | T_i | 全0.5 | 初始对所有人中性信任 |

### 5.2 认知熵初始值

认知熵初始值反映Agent的初始心理状态：

```
H_init = 0.1 + 0.05 × (1 - Resilience) + U(-0.05, 0.05)
```

其中 U(-0.05, 0.05) 是均匀分布的随机扰动。

**解释**：
- 基础认知熵为0.1（几乎清晰）
- 韧性低的Agent初始认知熵略高（更容易混乱）
- 加入小随机扰动增加多样性

---

## 六、多样性验证机制

### 6.1 多样性评分

为确保生成的10个Agent具有足够多样性，计算多样性评分：

```
DiversityScore = 1 - (1/N) × Σ_i Σ_j similarity(i, j) / (N-1)
```

其中：
- N = 10（Agent数量）
- similarity(i, j) = cosine_similarity(personality_i, personality_j)

**阈值**：DiversityScore 应 > 0.5，否则重新生成

### 6.2 相似度惩罚

如果两个Agent的余弦相似度 > 0.85，则对后生成的Agent进行扰动：

```
personality_new = personality_new + random_perturbation × (similarity - 0.85)
```

---

## 七、与下游模块的接口

### 7.1 输出给微观变量模块
- personality: 8维性格属性
- traitor_tendency: 内鬼倾向

### 7.2 输出给架构模块
- position_hint: 建议位置（用于架构配置参考）

### 7.3 输出给AI决策模块
- 整体Agent数据将注入到Agent的系统提示词中

---

*模块一完成。下一步：Agent微观变量系统*
