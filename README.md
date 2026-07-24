# 云南自然灾害应急协同决策平台

> 面向云南省的智能应急管理平台 — 灾情上报 → 多源核验 → AI方案生成 → 资源调度 → 事件归档，全流程闭环。

---

## 核心能力

| 模块 | 功能 |
|------|------|
| **态势大屏** | 高德地图实时灾情点位、统计卡片、分类分布图、28条历史事件影像 |
| **灾情上报** | 信息员填表+地图选点+图片上传，提交后进入审核流程 |
| **信息审核** | 指挥员查看详情、确认灾情/标记误报，状态机流转 |
| **AI方案工坊** | 选灾情→Dify RAG知识库检索→DeepSeek生成方案(SSE进度)→人工修订→批准→自动调度资源 |
| **资源调度** | 5步指引：选资源→锁定→创建调度单→审批→运输→到达→释放 |
| **实时采集** | USGS地震+和风天气每5分钟自动采集，≥3.0级自动入库创建灾情 |
| **知识库RAG** | Dify Chatflow 管理13份云南应急预案知识库，语义向量检索增强方案质量 |
| **角色面板** | 4角色专属Dashboard：信息员/指挥员/资源管理员/系统管理员 |
| **Agent审计** | 每次AI调用的输入输出、引用来源、执行状态，失败可重试 |
| **WebSocket** | 灾情状态变更、资源锁定、调度创建实时推送，顶部铃铛通知 |

---

## 快速启动

### 前置条件
- Docker Desktop（运行 PostgreSQL、Redis）
- Dify 自部署（Docker Compose）或 Cloud，用于 RAG 知识库检索
- Python 3.12+
- Node.js 20+

### 1. 克隆

```bash
git clone git@github.com:EclairFontaine/disaster-emergency-platform.git
cd disaster-emergency-platform
```

### 2. 启动基础设施

```bash
# 启动 PostgreSQL + Redis
docker compose up -d postgres redis
```

### 3. 配置

```bash
cd backend
cp .env.example .env
```

编辑 `backend/.env`：

```env
# DeepSeek API（生成模型）
DEEPSEEK_API_KEY=sk-your-deepseek-key

# Dify RAG 知识库（自部署 Docker）
DIFY_API_URL=http://localhost/v1
DIFY_API_KEY=app-your-dify-api-key

# 可选
OPENWEATHER_API_KEY=your-key
QWEATHER_API_KEY=your-key
JWT_SECRET=yunnan-disaster-jwt-secret-2024
```

### 4. 启动前后端

```bash
# 终端1: 后端
cd backend
py -m pip install -r requirements.txt
py -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# 终端2: 前端
cd frontend
npm install
npm run dev
```

### 5. 访问

| 服务 | 地址 |
|------|------|
| 前端 | http://127.0.0.1:3000 |
| API文档 | http://127.0.0.1:8000/docs |

### 6. 账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 系统管理员 | `admin` | `admin123` |
| 应急指挥员 | `commander1` | `123456` |
| 信息员 | `reporter1` | `123456` |
| 资源管理员 | `resource1` | `123456` |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + TypeScript + Ant Design 5 + Vite |
| 地图 | 高德地图 JS API 2.0 |
| 状态 | Zustand |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) |
| 数据库 | PostgreSQL 15 + PostGIS |
| 缓存 | Redis 7 |
| 实时推送 | WebSocket (JWT认证) + SSE (进度流) |
| AI生成 | DeepSeek Chat + 本地模板引擎降级 |
| RAG检索 | Dify Chatflow (混合检索: 向量+关键词) → DeepSeek直连(ILIKE关键词) → 模板引擎 |
| 采集 | USGS地震API + GDACS + 和风天气API + 国家预警 |

---

## 业务闭环

```
信息员 → 灾情上报(文字+图片+坐标)
   ↓
指挥员 → 审核确认/标记误报
   ↓
AI引擎 → Dify RAG检索预案知识库 → DeepSeek生成方案(SSE进度)
   ↓                     ↓ 降级
                   本地ILIKE关键词检索 → DeepSeek直连
   ↓                     ↓ 降级
                   本地模板引擎
   ↓
指挥员 → 人工修订 → 批准方案
   ↓
自动调度 → 按灾种匹配最近资源 → 创建调度单 → 批准生效
   ↓
资源管理员 → 执行调度 → 运输 → 到达 → 释放
   ↓
　　归档 → 状态: closed
```

---

## API 速览

| 模块 | 前缀 | 功能 |
|------|------|------|
| 认证 | `/api/auth` | 登录、获取用户信息 |
| 灾情 | `/api/incidents` | CRUD、状态流转、附近查询、上报、图片上传 |
| 资源 | `/api/resources` | CRUD、锁定/释放 |
| 调度 | `/api/dispatch-orders` | CRUD、状态变更（审批/运输/到达/释放） |
| 方案 | `/api/plans` | CRUD、搜索、AI生成、SSE进度流、审批（级联批准调度） |
| Agent | `/api/agent` | 执行记录、详情(含引用)、重试 |
| 数据源 | `/api/datasources` | CRUD |
| 用户 | `/api/users` | CRUD |
| WebSocket | `/api/ws` | 实时事件推送 |
| 审计 | `/api/audit` | 操作日志 |
| 统计 | `/api/statistics` | 大屏数据聚合 |
| 采集 | `/api/collector` | 手动/自动采集、状态、事件查询、历史数据导入 |

---

## 数据库表

| 表 | 说明 |
|------|------|
| `roles` · `users` | 角色权限与用户 |
| `incidents` · `incident_reports` | 灾情工单与上报记录 |
| `resources` · `resource_locks` | 资源库与锁定记录 |
| `dispatch_orders` | 调度指令 |
| `emergency_plans` | 应急预案知识库 |
| `agent_runs` · `citations` | AI执行记录与引用来源 |
| `audit_logs` | 操作审计 |
| `data_sources` | 外部数据源配置 |
| `collected_events` | 采集事件持久化（28条历史+实时） |

---

---

## Dify RAG 配置

方案生成通过 Dify Chatflow 进行知识库 RAG 检索，支持三级降级：

```
Dify Chat API（混合检索: 向量+关键词）
   ↓ 不可用
DeepSeek 直连 + PostgreSQL ILIKE 关键词检索
   ↓ 不可用
本地模板引擎生成
```

Dify 部署和 Chatflow 配置详见 `docs/DIFY_SETUP.md`。

导出知识库文档用于 Dify 导入：

```bash
py scripts/export_kb_for_dify.py
# 13 份预案导出到 scripts/kb_export/
```

---

## 数据采集

| 来源 | 频率 | 说明 |
|------|------|------|
| USGS | 5分钟 | 全球地震，云南+周边(18-32°N,94-110°E)，≥1.5级，去重入库 |
| GDACS | 5分钟 | 全球灾害预警（热带气旋/洪水/火山/地震），Orange/Red自动创建灾情 |
| 和风天气 | 5分钟 | 昆明/大理/丽江/昭通/普洱5城实时气象 |
| 国家预警 | 5分钟 | 国家突发事件预警信息 |
| 历史数据 | 手动 | 15条历史地震 + 10条非地震灾害（泥石流/洪水/火灾等） |

≥3.0级地震自动创建灾情工单；Orange/Red级GDACS预警自动创建灾情；极端天气自动预警。

---

## 测试

### 本地运行

```bash
# 后端单元测试（无需数据库，74个用例）
cd backend
pytest ../tests/ -v

# 后端全量测试（需要PostgreSQL，84个用例含10个集成测试）
pytest ../tests/ -v -m "unit or integration"

# 前端测试（42个用例，覆盖全部10个页面）
cd frontend
npx vitest run
```

### CI/CD 自动化

每次 push 到 `main` 分支，GitHub Actions 自动运行全量测试：

[![Test & Report](https://github.com/EclairFontaine/disaster-emergency-platform/actions/workflows/test.yml/badge.svg)](https://github.com/EclairFontaine/disaster-emergency-platform/actions/workflows/test.yml)

配置文件：`.github/workflows/test.yml`

### 测试覆盖

| 维度 | 文件数 | 测试数 |
|------|:---:|:---:|
| 后端单元 | 3 | 74 |
| 后端集成 | 1 | 10 |
| 前端页面 | 10 | 40 |
| 前端组件+服务 | 2 | 4 |
| **合计** | **16** | **128** |

---

## 项目结构

```
├── backend/
│   ├── app/
│   │   ├── api/          # 12个路由模块
│   │   ├── core/         # 配置/安全/数据库/Milvus
│   │   ├── models/       # 13个ORM模型
│   │   ├── schemas/      # Pydantic校验
│   │   └── services/     # 业务逻辑 + dify客户端 + collectors采集器(5个源)
│   ├── alembic/          # 数据库迁移（V1.0初始版本）
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/        # 10个页面 + __tests__
│   │   ├── components/   # Layout/MapView + __tests__
│   │   ├── hooks/        # useWebSocket/useSSE
│   │   ├── services/     # api.ts (60+ typed endpoints)
│   │   └── store/        # Zustand
│   ├── vite.config.ts
│   └── package.json
├── scripts/
│   └── export_kb_for_dify.py   # 导出预案为Dify知识库文档
├── tests/                # 后端测试套件（61+10个用例）
├── .github/workflows/    # CI/CD自动化测试
├── docs/                 # 需求/设计/接口/测试报告/Dify部署指南
├── docker-compose.yml
└── README.md
```

---

## Git 协作规范

- `main` 为稳定分支
- 开发新功能创建 `feature/xxx` 分支
- 提交前务必 `git pull` 同步队友代码
- **禁止 `git push --force`**，使用正常 `pull → merge → push`
- 每次提交后告知队友

---

## 团队

| 姓名 | 角色 | 分工 |
|------|------|------|
| | 后端开发 | FastAPI接口/数据库/AI集成/数据采集 |
| | 前端开发 | React页面/地图/SSE/WebSocket |
| | 产品/文档 | 需求分析/系统设计/文档编写 |
