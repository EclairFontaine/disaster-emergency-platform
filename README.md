# 云南自然灾害应急协同决策平台

面向云南省自然灾害应急管理的协同决策平台，实现灾情上报 → 多源核验 → 风险研判 → RAG预案检索 → AI方案生成 → 人工审批 → 资源调度 → 事件归档的全流程闭环。

---

## 技术栈

| 层次 | 技术 | 版本 |
|------|------|------|
| 前端框架 | React + TypeScript | 18.3 |
| UI 组件库 | Ant Design | 5.20 |
| 地图服务 | 高德地图 (AMap) | 2.0 |
| 状态管理 | Zustand | 4.5 |
| 后端框架 | Python + FastAPI | 3.12 / 0.115 |
| ORM | SQLAlchemy (异步) | 2.0.35 |
| 关系数据库 | PostgreSQL + PostGIS | 15 |
| 向量数据库 | Milvus | 2.4.0 |
| 缓存 | Redis | 7 |
| 对象存储 | MinIO | 2023.03 |
| AI 模型 | DeepSeek Chat | - |
| 部署 | Docker Compose + Nginx | - |

---

## 快速启动

### 前置条件

- Docker & Docker Compose
- DeepSeek API Key（[获取地址](https://platform.deepseek.com)）

### 1. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：

```env
DEEPSEEK_API_KEY=sk-your-key-here
JWT_SECRET=your-secure-random-string
CORS_ORIGINS=["http://localhost:3000","http://localhost:80"]
POSTGRES_DB=disaster
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
```

### 2. 一键启动

```bash
docker compose up -d
```

### 3. 访问系统

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost |
| API 文档 (Swagger) | http://localhost:8000/docs |
| API 文档 (ReDoc) | http://localhost:8000/redoc |
| MinIO 控制台 | http://localhost:9001 |

### 4. 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 系统管理员 | admin | admin123 |
| 应急指挥人员 | commander1 | 123456 |
| 普通信息员 | reporter1 | 123456 |
| 资源管理员 | resource1 | 123456 |

---

## 本地开发（不使用 Docker）

### 方式一：Windows 一键启动（推荐）

双击项目根目录的 `START.bat`，自动启动所有服务并打开浏览器。

> 注意：START.bat 中的路径可能需要根据你的本地环境调整。

### 方式二：手动启动

### 后端

```bash
cd backend
pip install -r requirements.txt
# 需要本机安装并运行 PostgreSQL 15 + Redis
# 修改 app/core/config.py 中的连接地址
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
# Vite 代理已配置将 /api 转发至 http://localhost:8000
```

---

## 用户角色与权限

| 角色 | 标识 | 职责 |
|------|------|------|
| 系统管理员 | admin | 用户管理、知识库维护、数据源管理、系统审计 |
| 应急指挥人员 | emergency_commander | 灾情审核、AI方案生成与审批、资源调度 |
| 普通信息员 | info_reporter | 灾情信息上报（含文字、图片、坐标） |
| 资源管理员 | resource_manager | 救援资源登记、维护、库存管理 |

---

## 功能页面

| 路由 | 页面 | 可访问角色 |
|------|------|-----------|
| `/login` | 登录页 | 全部 |
| `/dashboard` | 态势总览 | 全部 |
| `/report` | 灾情上报 | admin, 信息员 |
| `/review` | 灾情审核 | admin, 指挥员 |
| `/plan-workbench` | 方案工作台 | admin, 指挥员 |
| `/resources` | 资源管理 | admin, 指挥员, 资源员 |
| `/knowledge` | 知识库管理 | admin |
| `/datasources` | 数据源管理 | admin |
| `/agent-audit` | Agent审计日志 | admin |
| `/users` | 用户管理 | admin |

---

## API 接口

| 模块 | 前缀 | 端点数 | 说明 |
|------|------|--------|------|
| 认证 | `/api/auth` | 2 | JWT登录、用户信息 |
| 灾情管理 | `/api/incidents` | 9 | CRUD、状态变更、上报、图片上传、附近查询 |
| 资源管理 | `/api/resources` | 7 | CRUD、锁定/释放 |
| 调度管理 | `/api/dispatch-orders` | 5 | 调度指令CRUD、状态变更 |
| 方案管理 | `/api/plans` | 9 | CRUD、搜索、AI生成、SSE流、审批 |
| AI Agent | `/api/agent` | 3 | 执行记录查询、重试 |
| 数据源 | `/api/datasources` | 5 | 外部数据源管理 |
| 用户管理 | `/api/users` | 5 | 用户CRUD |
| 实时推送 | `/api/ws` | 1 | WebSocket双向通信 |
| 审计日志 | `/api/audit` | 1 | 操作日志查询 |
| 统计 | `/api/statistics` | 1 | 态势数据聚合 |
| 数据采集 | `/api/collector` | 7 | 手动采集、缓存查询、状态 |
| 健康检查 | `/api/health` | 1 | 服务状态 |

---

## 核心业务流程

```
灾情上报 ──→ 审核确认 ──→ AI方案生成 ──→ 方案审批 ──→ 资源调度 ──→ 处置完成归档
   │            │            │            │            │
   │       FSM状态机    RAG+DeepSeek    人工修订    锁定+调度指令
   │       + 审计日志    SSE进度推送    + 审计日志   WebSocket广播
```

### 灾情状态流转

```
pending_review ──→ confirmed ──→ in_progress ──→ closed
  (待审核)          (已确认)       (处置中)        (已关闭)
                       │
                       └──→ closed (误报场景)
```

---

## 数据库

12 张核心业务表，使用 PostgreSQL 15 + PostGIS 地理扩展：

`users` · `roles` · `incidents` · `incident_reports` · `resources` · `dispatch_orders` · `emergency_plans` · `agent_runs` · `citations` · `audit_logs` · `resource_locks` · `data_sources`

系统启动时自动初始化 4 个角色、4 个演示用户、13 份应急预案、17 项应急资源、16 条示例灾情记录。

---

## AI 能力

| 能力 | 技术方案 | 说明 |
|------|---------|------|
| 信息抽取 | DeepSeek + Prompt | 从灾情描述中提取结构化信息 |
| 知识检索 | 本地RAG + Milvus双模式 | 从预案知识库检索匹配参考方案，支持本地向量降级 |
| 方案生成 | DeepSeek Chat | 生成六部分完整应急预案 |
| 进度推送 | SSE | 实时推送生成各阶段进度 |
| 降级策略 | 本地模板引擎 | AI不可用时自动切换，保证可用性 |
| 资源推荐 | 规则引擎 | 按灾种自动匹配推荐资源 |

---

## 外部数据源

| 数据源 | 类型 | 采集周期 | 说明 |
|------|------|---------|------|
| USGS | 地震 | 30分钟 | 美国地质调查局全球地震数据 |
| CENC | 地震 | 按需 | 中国地震台网 |
| QWeather | 气象 | 按需 | 和风天气实时数据 |
| OpenWeatherMap | 气象 | 按需 | 开放天气数据 |
| 12379 | 预警 | 按需 | 国家预警信息发布中心 |

---

## 项目结构

```
disaster-emergency-platform/
├── frontend/                     # React 18 + TypeScript 前端
│   ├── src/
│   │   ├── pages/               # 10个页面组件
│   │   ├── components/          # 通用组件 (Layout, MapView)
│   │   ├── store/               # Zustand 状态管理
│   │   ├── services/            # Axios API 调用层
│   │   └── hooks/               # 自定义 Hook (WebSocket, SSE)
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── backend/                      # Python FastAPI 后端
│   ├── app/
│   │   ├── api/                 # 12个路由模块
│   │   ├── core/                # 核心配置 (安全/数据库/Milvus)
│   │   ├── models/              # 12个ORM模型
│   │   ├── schemas/             # 25个Pydantic模型
│   │   ├── services/            # 业务服务层
│   │   │   └── collectors/      # 数据采集器 (地震/气象/预警)
│   │   └── tasks/               # 后台任务
│   ├── alembic/                 # 数据库迁移
│   ├── requirements.txt
│   └── Dockerfile
├── docs/                         # 项目文档
│   ├── 需求说明书.docx
│   └── 系统设计说明书.docx
├── deploy/                       # 部署配置
├── docker-compose.yml
├── START.bat                      # Windows 一键启动脚本
├── .env.example
└── README.md
```

---

## 文档

- [需求说明书](docs/需求说明书.docx)
- [系统设计说明书](docs/系统设计说明书.docx)
- 前后端接口文档：启动后访问 http://localhost:8000/docs

---

## 团队

| 姓名 | 角色 | 分工 |
|------|------|------|
| | | |
| | | |
| | | |
| | | |

---

## Git 协作规范

- `main` 分支为稳定版本
- 开发新功能时创建 `feature/功能名` 分支
- 完成后提交 Pull Request，队友 Review 后合并
- 每次提交前先 `git pull` 同步最新代码
