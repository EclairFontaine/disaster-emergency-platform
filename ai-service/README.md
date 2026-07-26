# AI Emergency Service

> 灾害应急 AI 方案生成微服务 — 独立于主后端运行，通过 HTTP REST + SSE 通信。

---

## 架构

```
主后端 (8000)  ──POST /api/v1/generate-plan──→  ai-service (8001)
   │  ① 从 PostgreSQL 查灾情工单                        │
   │  ② BM25/ILIKE 检索相关预案                         │  ③ 3级降级生成
   │  ③ Haversine 匹配历史地震                          │     - Dify RAG（优先）
   │  ④ 组装参数，HTTP 转发                             │     - DeepSeek（兜底）
   │  ⑤ 透传结果，保存 EmergencyPlan + 自动调度          │     - 模板引擎（最终）
   └───────────────────────────────────────────────────┘
```

## 启动方式

### 本地开发（无需 Docker）

```bash
cd ai-service
pip install -r requirements.txt
cp .env.example .env        # 填入 DEEPSEEK_API_KEY
uvicorn main:app --host 127.0.0.1 --port 8001
```

访问 Swagger: http://127.0.0.1:8001/docs

### Docker（队友演示）

```bash
# 在项目根目录
docker compose up -d --build
# ai-service 自动构建并启动在 8001 端口
# 后端通过 AI_SERVICE_URL=http://ai-service:8001 自动发现
```

## 环境变量

| 变量 | 必填 | 说明 |
|------|:--:|------|
| `DEEPSEEK_API_KEY` | 是 | DeepSeek Chat API Key |
| `DEEPSEEK_BASE_URL` | 否 | API 地址，默认 `https://api.deepseek.com` |
| `DIFY_API_URL` | 否 | Dify 自部署地址，默认 `http://localhost:5001/v1` |
| `DIFY_API_KEY` | 否 | Dify Chatflow App Key，不配则跳过 Dify 直接走 DeepSeek |
| `SERVICE_HOST` | 否 | 监听地址，默认 `127.0.0.1` |
| `SERVICE_PORT` | 否 | 监听端口，默认 `8001` |

## API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/health` | 健康检查 + AI 配置状态 |
| POST | `/api/v1/generate-plan` | 方案生成（阻塞，返回 JSON） |
| POST | `/api/v1/generate-plan/stream` | 方案生成（SSE 进度流） |
| POST | `/api/v1/extract` | 灾情信息提取 |
| POST | `/api/v1/review-plan` | 方案审查 |
| GET | `/api/v1/runs` | Agent 执行记录列表 |
| GET | `/api/v1/runs/{id}` | 单条执行详情（含引用来源） |

## 与主后端集成

主后端 `app/core/config.py` 中配置：

```python
AI_SERVICE_URL = "http://127.0.0.1:8001"  # 本地
# AI_SERVICE_URL = "http://ai-service:8001"  # Docker
```

- **不配置** (`""`)：后端使用本地模式，AI 生成在原进程中完成
- **配置后**：后端自动改为代理模式，组装上下文 → 转发到 ai-service → 保存结果

两种模式对前端接口完全透明，无需前端修改。

## 数据存储

使用 SQLite（文件: `data/ai_service.db`），不依赖 PostgreSQL 或外部数据库。

表结构：`agent_runs`（执行记录）+ `citations`（引用来源）。

## 3级降级策略

```
Dify Chatflow（RAG 知识库检索 + LLM 生成）
  ↓ 不可用（未配置 DIFY_API_KEY /网络不通）
DeepSeek Chat（直接调用 + 主后端传来的预案/历史数据作为上下文）
  ↓ 不可用（API Key 失效 / 超时）
本地模板引擎（根据灾情类型+严重程度组装标准方案结构）
```

降级过程对调用方完全无感，总能返回一份可用的应急方案。
