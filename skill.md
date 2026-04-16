# Soulmate Memory System - Claude Code Skills

## 项目概述

这是一个给AI Agent用的3层记忆系统，模拟人类记忆模式。

## 快速命令

```bash
# 启动API
uvicorn api.main:app --reload

# 测试收集
curl -X POST http://localhost:8000/memory/collect \
  -H "Content-Type: application/json" \
  -d '{"user_id":"u1","content":"测试","topics":["测试"]}'

# 测试检索（向量语义搜索）
curl "http://localhost:8000/memory/retrieve?user_id=u1&query=测试"
```

## 核心文件

| 文件 | 作用 |
|------|------|
| `memory_system/memory_system.py` | Facade入口 |
| `memory_system/layers/` | 三层存储实现 |
| `memory_system/processor/` | 处理器实现 |
| `memory_system/retriever.py` | 提取引擎 |
| `memory_system/embedding.py` | 向量嵌入服务 |
| `api/routes.py` | API路由 |
| `evomap/gep_adapter.py` | EvoMap适配器 |

## 常见任务

### 添加新的记忆层方法
在 `layers/` 下的相应文件添加方法，同步函数直接用 `def`，不需要 `async`。

### 修改EvoMap Gene
编辑 `evomap/gene_publisher.py` 中的 `SOULMATE_MEMORY_GENE`。

### 发布到EvoMap
```bash
python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')
from evomap.gep_adapter import GEPAdapter
from evomap.gene_publisher import GenePublisher

async def publish():
    adapter = GEPAdapter()
    adapter.node_id = 'node_soulmate_memory'
    adapter.node_secret = '你的secret'
    adapter.registered = True
    publisher = GenePublisher(adapter)
    result = await publisher.publish_memory_gene()
    print(result)
    await adapter.close()

asyncio.run(publish())
"
```

## 向量嵌入配置

### 使用 sentence-transformers（默认，免费）
- 模型：`BAAI/bge-small-zh-v1.5`
- 国内镜像：`HF_ENDPOINT=https://hf-mirror.com`

### 使用 MiniMax API（可选）
需要在 `.env` 中配置：
```
MINIMAX_API_KEY=your-api-key
MINIMAX_GROUP_ID=your-group-id
```

## 注意事项

1. **aiosqlite在Python 3.13有bug** - 使用同步sqlite3代替
2. **datetime.utcnow()已废弃** - 使用datetime.now()代替
3. **SQLite execute参数** - 需要用tuple形式 `execute(sql, (a, b, c))`
4. **EvoMap需要至少2个assets** - Gene + Capsule一起发
5. **HuggingFace镜像** - 国内需要设置 `HF_ENDPOINT`
