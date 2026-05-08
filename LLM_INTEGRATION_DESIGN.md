# 真实大模型 API 与真实 Function Calling 接入方案设计

本文档用于规划智盾Agent 后续接入真实大模型 API 与真实 Function Calling 的工程方案。当前阶段只做设计，不进行代码接入，不写真实 API Key，不修改现有 `chat/messages` 主线。

## 一、接入目标

未来接入真实大模型 API 的目标不是替换现有安全网关，而是把当前 MVP 中的模拟 Function Calling 扩展为真实模型 `tool_call` 审计流程。

当前安全网关仍然保留以下职责：

- 在调用模型前进行输入检测和风险评分。
- 在模型返回 `tool_call` 后进行执行前审计。
- 在工具执行前完成 RBAC、参数边界和资源敏感度判断。
- 在输出返回前进行脱敏。
- 将完整证据链写入审计事件。
- 将审计证据展示到前端。

换句话说，真实大模型只负责生成普通回复或提出工具调用请求，不能绕过安全网关直接访问业务资源。

## 二、当前 MVP 与未来真实大模型版本的区别

### 当前 MVP

当前版本是规则驱动的最小闭环：

1. 规则检测用户输入。
2. 根据关键词模拟 `functionCall`。
3. 使用 RBAC 判断工具调用是否越权。
4. 根据判断结果阻断或放行。
5. 对输出做基础脱敏。
6. 记录审计事件。

当前模拟触发逻辑包括：

- `/admin`
- `db_credentials`
- `secret`
- `token`
- `key`

命中这些内容时，系统会模拟派生 `read_system_file`，用于验证 Function Calling 执行前审计和 RBAC 阻断。

### 未来真实大模型版本

未来版本的闭环应扩展为：

1. 用户输入先经过输入风险检测。
2. 安全网关将请求发送给真实大模型。
3. 模型返回普通文本或 `tool_call`。
4. 安全网关截获 `tool_call`。
5. 对 `tool name`、`arguments`、`resource` 做审计。
6. 进行 RBAC、参数边界、资源敏感度判断。
7. 允许则执行虚拟工具或沙箱工具。
8. 阻断则生成安全回复。
9. 对最终输出做脱敏。
10. 记录完整审计证据链。

关键原则：

> 模型返回 `tool_call` 后，绝对不能直接执行工具，必须先经过安全网关审计。

## 三、推荐架构

建议新增后端模块，但不要一次性接入主线。推荐结构如下：

```text
zhidun-agent-backend/app/services
├── llm_client.py
├── tool_registry.py
├── tool_call_guard.py
├── sandbox_tools.py
├── audit_service.py
├── rbac_engine.py
└── desensitizer.py
```

### llm_client.py

职责：

- 封装真实大模型 API 调用。
- 读取后端环境变量中的模型提供商、模型名和 API Key。
- 统一返回普通文本或模型 `tool_call`。
- 隔离不同模型供应商的 SDK / HTTP 请求细节。
- 捕获 API 错误、超时、网络失败和响应格式异常。

边界：

- 不在前端暴露 API Key。
- 不直接执行工具。
- 不写审计事件，只返回模型结果给安全网关主流程。

### tool_registry.py

职责：

- 定义允许暴露给模型的工具。
- 定义工具名称、描述、参数 schema、风险等级、资源范围和默认策略。
- 控制哪些工具可出现在模型工具列表中。

边界：

- 工具注册表只描述工具，不执行工具。
- 高风险工具可以注册，但默认不允许执行。

### tool_call_guard.py

职责：

- 审计模型返回的 `tool_call`。
- 校验工具是否存在于 `tool_registry.py`。
- 校验参数结构是否符合 schema。
- 提取资源标识，例如路径、文件名、数据域、用户资料范围。
- 调用 `rbac_engine.py` 做权限判断。
- 调用资源敏感度逻辑做风险判断。
- 输出统一决策：`ALLOW` 或 `BLOCK`。

边界：

- 不执行工具。
- 不生成真实业务数据。
- 只负责执行前审计。

### sandbox_tools.py

职责：

- 实现第一版虚拟工具。
- 所有工具只返回模拟内容。
- 不访问真实文件系统。
- 不访问真实数据库。
- 不访问真实企业资源。

当前隔离实现：

- `execute_sandbox_tool(tool_name, arguments)` 只允许 `search_public_docs` 和 `read_user_profile` 返回安全模拟结果。
- `read_system_file` 即使被请求执行，也只返回安全拒绝结果，不访问真实文件系统。
- 未注册工具统一拒绝。

### 隔离测试脚本

当前新增独立脚本：

```text
zhidun-agent-backend/scripts/test_tool_call_guard.py
```

覆盖场景：

- `search_public_docs` 检索公开文档，应允许。
- `read_user_profile` 读取 `self_profile`，应允许。
- `read_system_file` 读取 `/admin/db_credentials.txt`，必须阻断。
- `dump_database` 未注册工具，必须阻断。
- `search_public_docs` 参数越界到 `/admin/secret`，必须阻断。

运行方式：

```powershell
cd d:\计算机\zhidun_agent\zhidun-agent-backend
python scripts/test_tool_call_guard.py
```

该脚本不调用 `chat/messages` 主线，不写入 `events.json`，不需要 API Key，也不执行真实工具。

### audit_service.py

职责：

- 继续记录审计事件。
- 在未来版本中补充真实模型来源字段，例如：
  - `tool_call_source: "real_model"`
  - `model_provider`
  - `model_name`
  - `tool_call_raw`
  - `tool_call_guard_result`

边界：

- 延续现有 `events.json` 存储方式，直到进入数据库持久化阶段。

### rbac_engine.py

职责：

- 继续做 RBAC 判断。
- 对工具名和资源范围进行白名单/拒绝策略匹配。
- 对高风险工具采用默认拒绝策略。

### desensitizer.py

职责：

- 继续做输出脱敏。
- 对模型普通回复、工具执行结果和阻断回复都应进行输出检查。

## 四、第一版只允许虚拟工具

真实大模型接入后的第一版只允许虚拟工具，不访问真实敏感资源。

### 1. search_public_docs

风险等级：低风险。

允许角色：

- `demo_user`

用途：

- 模拟公开知识库搜索。
- 返回固定的公开文档摘要。

安全要求：

- 不访问真实文件。
- 不访问真实数据库。
- 不返回企业内部数据。

### 2. read_user_profile

风险等级：低风险。

允许资源：

- `self_profile`

用途：

- 模拟读取当前用户自己的基础资料。

安全要求：

- 不访问真实用户数据。
- 不允许读取其他用户资料。
- 参数中必须限制资源范围为 `self_profile`。

### 3. read_system_file

风险等级：高风险。

默认策略：

- 默认拒绝。

用途：

- 用于验证真实模型返回高危 `tool_call` 时，安全网关是否能执行前阻断。

安全要求：

- 不访问真实文件系统。
- 即使模型生成该工具调用，也必须先进入 `tool_call_guard.py`。
- 第一版应始终被 RBAC 拒绝，除非后续明确设计更细粒度的沙箱策略。

## 五、真实 Function Calling 安全流程

推荐流程：

```text
用户输入
-> 输入检测
-> 调用真实大模型
-> 模型返回 tool_call
-> tool_call_guard 截获
-> 工具注册检查
-> 参数边界检查
-> RBAC 校验
-> 资源敏感度判断
-> ALLOW / BLOCK
-> 输出脱敏
-> 审计事件记录
-> 前端证据链展示
```

详细说明：

1. 用户输入进入网关。
2. 规则引擎和风险评分先执行，得到输入阶段风险。
3. 若输入阶段已经达到强阻断策略，可不调用模型。
4. 若允许调用模型，则由 `llm_client.py` 发起真实大模型请求。
5. 模型可能返回普通文本，也可能返回 `tool_call`。
6. 普通文本进入输出脱敏后返回。
7. `tool_call` 必须先进入 `tool_call_guard.py`，不能直接执行。
8. `tool_call_guard.py` 检查工具注册、参数 schema、资源范围、RBAC 和资源敏感度。
9. 若决策为 `BLOCK`，生成安全阻断回复并记录审计事件。
10. 若决策为 `ALLOW`，只允许执行 `sandbox_tools.py` 中定义的虚拟工具。
11. 工具结果再次进入输出脱敏。
12. 审计事件记录输入检测、模型原始 `tool_call`、守卫判断、RBAC 结果、输出脱敏和最终结论。
13. 前端证据链展示真实 `tool_call` 来源和安全网关判断过程。

必须强调：

> 任何模型返回的 `tool_call` 都只是“请求执行工具”，不是“授权执行工具”。授权只能由安全网关完成。

## 六、环境变量与密钥管理

API Key 管理原则：

- API Key 只能放在后端环境变量。
- 不允许写入前端。
- 不允许提交到 GitHub。
- 不允许写入文档示例真实值。
- 建议提供 `.env.example`，只展示变量名和占位值。
- `.env` 必须写入 `.gitignore`。
- README 中只展示变量名，不展示真实值。

示例 `.env.example`：

```text
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-4.1-mini
```

建议后端读取方式：

```text
LLM_PROVIDER
OPENAI_API_KEY
LLM_MODEL
LLM_TIMEOUT_SECONDS
LLM_MAX_RETRIES
```

安全要求：

- 后端启动时可以检查必要环境变量是否存在。
- 日志中不得打印 API Key。
- 异常信息不得包含完整请求头。
- 前端只能请求后端接口，不得直接请求模型供应商。

## 七、风险与限制

接入真实大模型后会引入新的工程风险：

- 输出不稳定。
- `tool_call` 格式需要适配不同模型供应商。
- API 调用费用增加。
- 网络失败和供应商服务不可用。
- 响应延迟增加。
- 模型可能不调用工具。
- 模型可能生成不完整参数。
- 模型可能生成错误工具名。
- 模型可能生成越权资源参数。
- 需要更多边界样例测试。
- 需要区分模拟 Function Calling 与真实模型 `tool_call`。
- 需要重新评估自动评测口径，避免把规则样例回归通过率当作模型泛化能力。

## 八、分阶段实施计划

### 阶段 1：只写 llm_client.py

目标：

- 封装真实大模型 API 调用。
- 不接入 `chat/messages` 主线。
- 单独测试普通回复。

验收：

- 能在本地脚本中调用模型。
- API Key 只来自后端环境变量。
- 不写入 Git。

### 阶段 2：定义虚拟 tools

目标：

- 在 `tool_registry.py` 中定义虚拟工具。
- 允许模型返回 `tool_call`。
- 不执行真实工具。

验收：

- 模型可以看到工具 schema。
- `read_system_file` 存在但默认拒绝。

### 阶段 3：接入 tool_call_guard

目标：

- 所有 `tool_call` 先进入安全审计。
- 完成工具注册检查、参数边界检查、RBAC 校验和资源敏感度判断。

验收：

- `search_public_docs` 可被允许。
- `read_user_profile` 仅允许 `self_profile`。
- `read_system_file` 必须被阻断。

### 阶段 4：写入现有审计事件结构

目标：

- 把真实模型返回的 `tool_call` 写入现有审计事件字段。
- 增加来源标识，例如 `real_model_tool_call`。

验收：

- `events.json` 仍能记录完整审计事件。
- 工具调用流水可以区分模拟调用和真实模型调用。

### 阶段 5：前端证据链展示真实 tool_call 来源

目标：

- 前端证据链展示真实模型 `tool_call`。
- 展示安全网关拦截和 RBAC 判断。

验收：

- 不重构 UI。
- 仅补充字段展示。

### 阶段 6：扩充自动评测脚本

目标：

- 区分 `simulated_function_call` 与 `real_model_tool_call`。
- 为真实模型接入新增单独评测口径。

验收：

- 现有规则 MVP 评测仍可运行。
- 真实模型评测不影响 `events.json` 提交状态。

## 九、验收标准

未来编码接入时必须满足：

- 不破坏当前规则 MVP。
- 没有 API Key 泄露。
- 正常请求可返回普通回复。
- 高危请求如果触发 `read_system_file` `tool_call`，必须被 RBAC 阻断。
- 前端证据链能展示真实 `tool_call`。
- `events.json` 仍能记录完整审计事件。
- 自动测试脚本仍能运行。
- 模型返回 `tool_call` 后不会直接执行工具。
- 第一版只执行虚拟工具或沙箱工具。

## 十、暂不做事项

明确暂不做：

- 不访问真实文件系统。
- 不接真实数据库。
- 不执行真实敏感工具。
- 不做登录注册。
- 不做生产部署。
- 不替代 IAM / DLP。
- 不训练模型。
- 不在前端保存或传递 API Key。
- 不把真实企业数据放入测试样例。

## 十一、结论

真实大模型 API 和真实 Function Calling 可以作为下一阶段能力，但接入方式必须以安全网关为中心。模型只产生文本或工具调用请求，所有工具调用必须先经过 `tool_call_guard.py`、`rbac_engine.py`、资源敏感度判断和审计记录。

当前项目可以进入“设计评审和最小隔离验证”阶段，但不建议直接把真实大模型接入 `chat/messages` 主线。推荐先从独立的 `llm_client.py` 和虚拟工具验证开始。
