# Soulmate Memory System

给AI Agent用的3层记忆系统，模拟人类记忆模式。

## 核心概念

```
┌─────────────────────────────────────────────────────────────┐
│                    SOULMATE MEMORY                           │
├─────────────────────────────────────────────────────────────┤
│  SHORT-TERM (工作记忆)                                       │
│  - 容量：100条消息/会话                                      │
│  - 存储：内存 + JSON文件持久化                               │
│  - 生命周期：会话结束                                        │
├─────────────────────────────────────────────────────────────┤
│  RECENT (情景记忆)                                           │
│  - 3天对话摘要                                              │
│  - 存储：SQLite                                             │
│  - 生命周期：3天 → 压缩/晋升/遗忘                            │
├─────────────────────────────────────────────────────────────┤
│  SOUL (语义记忆/灵魂)                                        │
│  - 永久核心记忆                                              │
│  - 存储：SQLite                                             │
│  - 生命周期：永久（可降级）                                  │
└─────────────────────────────────────────────────────────────┘
```

## 核心特性

- **三层记忆**: Short → Recent → Soul 自动流转
- **向量检索**: 语义相似度搜索，支持联想能力
- **Ebbinghaus遗忘曲线**: 模拟人类记忆遗忘机制
- **EvoMap集成**: 分布式记忆网络

## 向量检索

支持**语义搜索**，例如：
- 存入"我最喜欢吃火锅" → 查询"美食"能找到
- 存入"加班到很晚" → 查询"工作"能找到

使用开源模型 `BAAI/bge-small-zh-v1.5`，无需 API 费用。

## 快速开始

### 安装

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
uvicorn api.main:app --reload
```

### 测试

```bash
# 健康检查
curl http://localhost:8000/health

# 收集记忆
curl -X POST http://localhost:8000/memory/collect \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","content":"今天加班好累","emotion":"negative","topics":["工作"]}'

# 检索上下文（支持语义搜索）
curl "http://localhost:8000/memory/retrieve?user_id=u1&query=工作"
```

## API文档

### POST /memory/collect

收集一条记忆。

```json
{
  "user_id": "user_123",
  "content": "今天加班好累",
  "emotion": "negative",
  "topics": ["工作", "疲惫"],
  "metadata": {}
}
```

### GET /memory/retrieve

检索上下文（向量语义搜索）。

| 参数 | 类型 | 说明 |
|------|------|------|
| user_id | string | 用户ID |
| query | string | 查询内容 |
| session_id | string | 可选，会话ID |

## Agent SDK

```python
from sdk.soulmate import SoulmateMemory

memory = SoulmateMemory(user_id="user_123")

# 收集记忆
memory.collect(
    content="今天加班好累",
    emotion="negative",
    topics=["工作"]
)

# 获取上下文
context = memory.retrieve(query="用户在烦恼什么")
```

## 项目结构

```
soulmate-memory/
├── memory_system/          # 核心SDK
│   ├── layers/             # 三层存储
│   │   ├── short_layer.py # 短期记忆
│   │   ├── recent_layer.py# 近期记忆
│   │   └── soul_layer.py  # 灵魂记忆
│   ├── processor/          # 处理器
│   │   ├── collector.py   # 收集器
│   │   ├── forgetting.py  # 遗忘调度
│   │   ├── compressor.py  # 压缩器
│   │   └── promoter.py    # 晋升/降级
│   ├── retriever.py       # 提取引擎
│   └── embedding.py        # 向量嵌入服务
├── api/                   # REST API
├── evomap/                # EvoMap集成
└── sdk/                   # Agent SDK
```

## 技术栈

- **Python 3.13+** + FastAPI
- **SQLite** 本地存储
- **sentence-transformers** 向量嵌入（BAAI/bge-small-zh-v1.5）
- **MiniMax API** 可选（需配置 GROUP_ID）

## EvoMap集成

已发布到EvoMap网络：
- Gene ID: `gene_soulmate_3layer_memory`
- 功能：3层记忆系统 + Ebbinghaus遗忘曲线

## License

MIT
