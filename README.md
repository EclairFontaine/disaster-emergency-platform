# 云南自然灾害应急协同决策平台

## 系统概述
面向云南省自然灾害应急管理的协同决策平台，实现灾情上报、多源核验、风险研判、RAG预案检索、AI方案生成、人工审批、资源调度和事件归档的全流程闭环。

## 技术栈
- **后端**: Python 3.12 + FastAPI + SQLAlchemy 2.0 (async) + PostgreSQL/PostGIS
- **前端**: React 18 + TypeScript + Vite + Ant Design 5 + 高德地图
- **AI**: DeepSeek Platform (Chat + Embedding)
- **向量库**: Milvus
- **缓存**: Redis
- **部署**: Docker Compose

## 快速启动

### 前置条件
- Docker & Docker Compose
- DeepSeek API Key (https://platform.deepseek.com)

### 1. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 填入你的 DEEPSEEK_API_KEY
```

### 2. 启动所有服务
```bash
docker compose up -d
```

### 3. 访问系统
- 前端: http://localhost
- 后端 API 文档: http://localhost:8000/docs

### 4. 默认账号
| 角色 | 用户名 | 密码 |
|------|--------|------|
| 系统管理员 | admin | admin123 |

## 用户角色
- **系统管理员 (admin)**: 管理知识库、用户、模型和数据源
- **普通信息员 (info_reporter)**: 上报灾情
- **应急指挥人员 (emergency_commander)**: 审核事件、生成处置方案
- **资源管理员 (resource_manager)**: 维护人员、车辆、物资和避难场所

## 核心业务流程
灾情上报 → 后端校验 → 多源核验 → 风险研判 → RAG检索预案 → Agent生成方案 → 人工审批 → 资源调度 → 过程记录 → 事件归档

## 项目结构
```
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── api/          # API路由
│   │   ├── core/         # 核心配置(数据库/JWT/Milvus)
│   │   ├── models/       # 数据模型
│   │   ├── schemas/      # Pydantic校验
│   │   └── services/     # 业务逻辑层
│   └── alembic/          # 数据库迁移
├── frontend/
│   ├── src/
│   │   ├── pages/        # 9个业务页面
│   │   ├── components/   # 公共组件
│   │   └── services/     # API调用封装
│   └── nginx.conf
└── .env.example
```
