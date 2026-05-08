# MOCK_BOUNDARY

本文档说明当前项目中真实后端能力与 mock / 静态演示能力的边界。目标不是删除 mock，而是避免把示意数据误认为生产能力。

## 一、已经接入真实后端的功能

### 对话安全检测

前端页面：

- `zhidun-agent-frontend/src/views/ChatDemo/index.vue`

后端接口：

- `POST /api/v1/chat/messages`

说明：

- 已走后端规则检测、风险评分、Function Calling 模拟派生、RBAC 判断、输出脱敏。
- 高风险或阻断请求会写入 `events.json`。
- 当前不接真实大模型，回复由后端安全逻辑模拟生成。

### 审计事件列表与详情

前端页面：

- `AuditDetail`
- `EvidenceDrawer`
- `ReportCenter`

后端接口：

- `GET /api/v1/security/events`
- `GET /api/v1/security/events/{eventId}`

说明：

- 数据来自 `app/data/events.json`。
- 事件由高风险请求或阻断请求产生。

### 结构化审计报告

后端接口：

- `POST /api/v1/security/events/{eventId}/report`

说明：

- 返回 `sections` 结构化数据。
- 当前不生成 PDF。

### Dashboard 核心统计

前端页面：

- `Dashboard`

后端接口：

- `GET /api/v1/dashboard/overview`
- `GET /api/v1/dashboard/risk-matrix`

说明：

- 总事件数、高风险事件数、工具审计数、泄露拦截数、趋势、风险类型分布来自 `events.json` 聚合。
- 风险矩阵摘要由事件和 RBAC 策略派生。

### 规则库只读展示

前端页面：

- `Policy/InjectionRules`

后端接口：

- `GET /api/v1/security/rules`

说明：

- 数据来自 `app/data/rules.json`。
- 当前不开放新增、编辑、删除接口。

### RBAC 策略只读展示

前端页面：

- `ToolAudit`

后端接口：

- `GET /api/v1/security/rbac`

说明：

- 数据来自 `app/data/rbac.json`。
- 当前不开放新增、编辑接口。

### 测试样例快捷入口

前端页面：

- `ChatDemo`

后端接口：

- `GET /api/v1/security/test-cases`

说明：

- 数据来自 `app/data/test_cases.json`。
- 用于演示正常请求、提示注入、工具越权、敏感泄露和链式攻击。

### 工具调用流水

前端页面：

- `SecOps/ToolMonitor`

后端接口：

- `GET /api/v1/security/tool-invocations`
- `GET /api/v1/security/tool-invocations/{invocationId}`

说明：

- 当前流水不是独立存储表，而是从 `events.json` 中已有事件派生。
- 只有产生 Function Calling 的事件才会出现在工具调用流水中。

### 脱敏预览

前端页面：

- `Policy/MaskTemplates`

后端接口：

- `POST /api/v1/security/desensitize-preview`

说明：

- 复用后端 `desensitizer.py`。
- 支持手机号、邮箱、API Key、系统提示残留等基础脱敏。
- 脱敏模板表本身当前仍保留 mock 展示。

## 二、仍为 mock / 静态演示的功能

### 前端 fallback mock

文件：

- `zhidun-agent-frontend/src/api/backendMock.ts`
- `zhidun-agent-frontend/src/mock/mockData.json`

保留原因：

- 当 `VITE_USE_MOCK=true` 时可进行纯前端演示。
- 便于后续开发未完成接口时保留页面可用性。
- 当前要求明确不删除 mock。

### 脱敏模板表

页面：

- `/policy/mask`

现状：

- 表格数据仍来自前端 mock。
- 右侧脱敏预览已接后端。

保留原因：

- 当前后端没有模板 CRUD，也不应在本阶段开放写接口。

### 策略沙箱和阈值面板

页面：

- `/policy/injection`

现状：

- 规则列表来自后端。
- 策略沙箱本地评分仍为前端演示逻辑。

保留原因：

- 核心输入检测已经由 `/chat/messages` 覆盖。
- 当前阶段不新增独立策略沙箱接口。

### 资产、应用、告警、操作日志、账户

页面：

- `/assets`
- `/assets/sensitive`
- `/settings`
- `/settings/alerts`
- `/settings/operation-logs`
- `/account`

现状：

- 仍为 mock 或静态演示。

保留原因：

- 这些属于完整平台扩展能力，不属于当前 MVP 核心闭环。
- 当前不接真实企业资产，不做登录注册，不做复杂权限后台。

### 系统运行状态部分文案

页面：

- `/dashboard`

现状：

- 核心统计和风险分布来自后端。
- 部分系统状态文案仍为静态展示。

保留原因：

- 当前没有真实生产运行状态、集群和外部服务监控。

## 三、为什么暂时保留 mock

- 当前阶段重点是安全闭环演示，而不是完整平台。
- mock 可以保留页面完整性，避免未实现功能阻塞主线验收。
- 删除 mock 会降低前端无后端演示能力。
- 保留 mock 有助于明确后续接口边界。

## 四、后续扩展方向

建议按优先级扩展：

1. 规则和 RBAC 策略仍保持只读，待权限模型明确后再考虑写接口。
2. 若需要真实工具注册中心，可新增只读工具注册接口。
3. 若需要真实资产拓扑，应先明确资产数据来源，不要用当前 mock 冒充真实企业资产。
4. 若需要报告下载，可在结构化报告稳定后再设计 PDF 生成。
5. 若需要实时刷新，可在轮询稳定后再设计 SSE，但当前阶段不启用。

## 五、禁止误用说明

- 不要把 mock 数据当作真实企业数据。
- 不要声称当前系统已完成完整 IAM / DLP。
- 不要声称已接入真实大模型或生产环境。
- 不要把 `events.json` 中的临时测试事件写入项目文档作为真实案例。

