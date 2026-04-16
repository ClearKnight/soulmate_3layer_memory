# Soulmate Memory System

## 项目原则

**若无必要勿增实体**

## 产品定位

给Agent用的记忆SDK，让Agent记住用户、越来越懂用户。

## 核心架构

三层记忆 + 处理器 + 提取引擎

```
记忆收集 → Processor → 三层存储
                      ↓
              Short(内存/会话)
              Recent(SQLite/3天)
              Soul(SQLite/永久)

Agent调用：collect() / retrieve()
```

## 技术栈

- Python + FastAPI
- SQLite（本地开发）
- MiniMax API（可选，用于摘要生成）

## 项目结构

```
memory_system/
├── layers/           # 三层存储
│   ├── short_layer.py    # 短期记忆（内存+文件持久化）
│   ├── recent_layer.py   # 近期记忆（SQLite）
│   └── soul_layer.py     # 灵魂记忆（SQLite）
├── processor/        # 处理器
│   ├── collector.py      # 收集器
│   ├── forgetting.py     # 遗忘调度（Ebbinghaus曲线）
│   ├── compressor.py     # 压缩器
│   └── promoter.py       # 晋升/降级
├── retriever.py     # 提取引擎
└── memory_system.py # Facade入口

api/                 # REST API
evomap/              # EvoMap集成
sdk/                 # Agent SDK
tests/               # 测试
```

## 启动方式

```bash
# 安装依赖
pip install -r requirements.txt

# 启动API
uvicorn api.main:app --reload

# 测试
curl http://localhost:8000/health
```

## API接口

- `POST /memory/collect` - 收集记忆
- `GET /memory/retrieve?user_id=xxx&query=yyy` - 检索上下文
- `GET /health` - 健康检查