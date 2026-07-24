# Dify RAG 部署与配置指南

## 架构概述

```
┌──────────────┐     Dify Chat API      ┌────────────────────────────┐
│   Backend    │ ───────────────────────▶ │  Dify Chatflow App        │
│  (FastAPI)   │ ◀─────────────────────── │  ┌─────────────────────┐  │
│              │    (SSE / JSON)          │  │ Knowledge Retrieval │  │
│  ai_engine   │                         │  │   (向量 + 关键词)    │──┼──▶ 知识库
│  agent_runner│                         │  └─────────┬───────────┘  │  │  (13份预案)
│              │                         │            ▼              │  │
└──────────────┘                         │  ┌─────────────────────┐  │
                                         │  │   DeepSeek LLM      │  │
                                         │  │   方案生成           │  │
                                         │  └─────────────────────┘  │
                                         └────────────────────────────┘
```

## 一、部署 Dify (Docker Compose)

### 1.1 克隆 Dify 仓库

```bash
git clone https://github.com/langgenius/dify.git
cd dify/docker
```

### 1.2 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env`，按需修改：
```ini
# Dify 对外端口（nginx），默认 80
EXPOSE_NGINX_PORT=80

# 数据库密码 (生产环境请修改)
DB_PASSWORD=difyai123456
```

> **注意**：如果 `EXPOSE_NGINX_PORT=80`，则 Dify API 地址为 `http://localhost/v1`；如果改为 `5001`，则为 `http://localhost:5001/v1`。

### 1.3 启动

```bash
docker compose up -d
```

访问 `http://localhost:5001`，创建管理员账号。

---

## 二、配置 DeepSeek 模型供应商

1. 进入 Dify 控制台 → 右上角头像 → **设置**
2. 左侧菜单 → **模型供应商**
3. 找到 **DeepSeek** → 点击 **设置**
4. 填入你的 API Key，保存

---

## 三、创建知识库

### 3.1 导入应急预案文档

1. Dify 顶部导航 → **知识库** → **创建知识库**
2. 填写：
   - 名称: `云南应急管理预案库`
   - 权限: 团队可见
3. 上传文档：使用我们导出的文件（位于 `scripts/kb_export/` 目录下的 13 个 `.txt` 文件）

   如果还没导出，运行：
   ```bash
   cd disaster-emergency-platform
   py scripts/export_kb_for_dify.py
   ```

4. 分段设置：选择 **自定义分段**
   - 分段标识符: `###` (三个#号，匹配预案的小节标题)
   - 分段最大长度: 500 tokens
   - 分段重叠长度: 50 tokens
   - 预处理规则: 保持默认

5. 索引方式：**高质量** (使用 Dify 内置默认 embedding 模型)
6. 检索设置：**混合检索** (向量 + 关键词)

### 3.2 等待索引完成

文档上传后 Dify 会自动进行分段、向量化处理。等待状态变为"已完成"即可。

---

## 四、创建 Chatflow 应用

### 4.1 创建应用

1. 顶部导航 → **工作室** → **创建空白应用**
2. 选择类型：**Chatflow** → 填写名称 `应急方案生成`
3. 进入编排页面

### 4.2 配置节点

Chatflow 画布中依次拖入并配置以下节点：

#### (1) 开始节点 (Start)

添加输入变量：

| 变量名 | 类型 | 标签 |
|--------|------|------|
| `incident_title` | Text | 灾情标题 |
| `incident_category` | Text | 灾害类型 |
| `incident_severity` | Text | 严重程度 |
| `incident_description` | Text | 灾情描述 |
| `incident_latitude` | Text | 纬度 |
| `incident_longitude` | Text | 经度 |
| `affected_count` | Text | 影响人数 |

#### (2) 知识检索节点 (Knowledge Retrieval)

- **查询内容**:
  ```
  {{#start.incident_title#}} {{#start.incident_description#}} {{#start.incident_category#}}
  ```
- **知识库**: 选择「云南应急管理预案库」
- **召回模式**: 混合检索
- **TopK**: 5
- **Score阈值**: 0.3

#### (3) LLM 节点 (LLM)

- **模型**: DeepSeek → deepseek-chat
- **上下文**: `{{#173xxxxxxx.result#}}` (选择知识检索节点的 result 输出)
- **系统提示词**:
  ```
  你是一个应急管理专家。根据灾情信息和参考预案，生成一份详细的应急处置方案。
  方案需包含：
  一、灾情概述
  二、应急响应等级
  三、组织机构与职责
  四、处置措施（分阶段：0-24h、24-72h、72h-14天、恢复重建）
  五、资源调配方案
  六、注意事项
  请使用专业、规范的表述，内容详实、可操作。
  ```
- **用户提示词**:
  ```
  灾情信息：
  标题：{{#start.incident_title#}}
  类型：{{#start.incident_category#}}
  严重程度：{{#start.incident_severity#}}
  描述：{{#start.incident_description#}}
  影响人数：{{#start.affected_count#}}
  位置：({{#start.incident_latitude#}}, {{#start.incident_longitude#}})

  请根据上述灾情信息和参考预案知识库，生成一份详细的应急处置方案。
  ```
- **记忆**: 关闭 (每次独立生成)

#### (4) 直接回复节点 (Answer)

- 输出: `{{#llm.text#}}`

### 4.3 测试与发布

1. 点击右侧 **预览** 测试
2. 输入测试数据，确认生成结果正确
3. 点击右上角 **发布**

---

## 五、获取 API Key

1. 应用页面 → 左侧 **API 访问**
2. 点击 **API 秘钥** → **创建秘钥**
3. 复制生成的 key（格式: `app-xxxxxxxxxxxxx`）

---

## 六、配置本项目

### 6.1 修改 `.env` 文件

在项目的 `.env` 中添加：

```ini
# 如果 Dify nginx 在 80 端口（默认）
DIFY_API_URL=http://localhost/v1
# 如果 Dify 暴露在 5001 端口
DIFY_API_URL=http://localhost:5001/v1
DIFY_API_KEY=app-你的秘钥
```

### 6.2 验证连通性

启动后端后，在 PlanWorkbench 页面选择一个灾情，点击"AI生成方案"即可测试。

---

## 七、降级策略

当前 RAG 管道为三级降级：

```
Dify Chat API (知识库 RAG + DeepSeek)
    │ 失败 ↓
DeepSeek 直连 + PostgreSQL ILIKE 关键词检索
    │ 失败 ↓
本地模板引擎 (Markdown 拼接)
```

当 Dify 不可用时，系统自动降级到原有的关键词检索+DeepSeek 路径。当 DeepSeek 也不可用时，使用本地模板引擎兜底，保证系统始终可用。

---

## 八、常见问题

### Q: Dify 怎么用其他 embedding 模型？

默认使用 Dify 内置的 `text-embedding-2` 系列，效果已足够好。如需更换：
- 设置 → 模型供应商 → 添加对应供应商（如 OpenAI）
- 知识库设置中切换索引方式

### Q: 知识库文档更新后需要重新索引吗？

Dify 支持增量索引。上传新文档或修改分段后，只需对变更部分重新索引。

### Q: 如何监控 Dify 调用？

- Dify 控制台 → 日志与标注
- 后端 `AgentRun` 表记录每次调用的 `input_data.provider`: `"dify"`
