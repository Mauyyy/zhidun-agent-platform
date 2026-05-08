# 真实 tool_call 接入安全审计主线设计

本文档用于设计如何在不破坏现有规则 MVP 的前提下，将真实模型返回的 `tool_call` 接入 `chat/messages` 安全审计主线。当前文档只做方案设计，不直接编码接入，不修改前端，不新增接口，不执行真实工具。

## 一、接入目标

接入目标不是替换当前已经稳定跑通的规则 MVP，而是在可配置开关下，让 `POST /api/v1/chat/messages` 支持真实模型 `tool_call` 的安全审计流程。

当前 MVP 继续作为默认路径：

- 规则检测用户输入。
- 根据关键词模拟 Function Calling。
- 在执行前进行 RBAC 判断。
- 输出脱敏。
- 写入审计事件。
- 前端展示证据链。

未来真实模型模式只是在默认 MVP 之外增加一条可关闭、可回退、可审计的分支。真实模型可以返回普通文本或 `tool_call`，但模型不能直接获得工具执行权限。

## 二、接入原则

1. 默认仍使用当前规则 MVP。
2. 真实大模型模式必须由环境变量显式开启。
3. 没有 API Key 时自动回退当前 MVP，不允许请求失败导致主线不可用。
4. 模型返回 `tool_call` 后绝不能直接执行工具。
5. 所有 `tool_call` 必须先经过 `tool_call_guard.py` 审计。
6. 第一版只允许执行 `sandbox_tools.py` 中的虚拟工具。
7. `read_system_file` 永远不能访问真实文件系统，即使 guard 逻辑或模型输出异常也必须拒绝。
8. 所有关键决策必须写入审计事件，包括模型来源、工具调用、guard 判断、RBAC 结果、输出脱敏和最终结论。
9. 前端证据链必须能区分模拟调用和真实模型 `tool_call`。

## 三、建议环境变量

建议新增或沿用以下环境变量：

```text
USE_REAL_LLM=false
USE_REAL_TOOL_CALL=false
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-4.1-mini
LLM_BASE_URL=
```

说明：

- `USE_REAL_LLM` 默认 `false`，表示继续使用当前规则 MVP。
- `USE_REAL_TOOL_CALL` 默认 `false`，表示即使未来启用真实模型，也不默认进入真实工具调用分支。
- `OPENAI_API_KEY` 只能来自后端环境变量。
- 未配置 `OPENAI_API_KEY` 时必须回退当前 MVP。
- `.env` 不提交 Git。
- `.env.example` 只保留占位值，不写真实密钥。
- 前端不得保存、传递或展示 API Key。

## 四、主线流程设计

### 路径 A：默认 MVP 模式

```text
用户输入
-> 规则检测
-> 风险评分
-> 模拟 functionCall
-> RBAC
-> 输出脱敏
-> 审计记录
-> 返回前端
```

适用条件：

- `USE_REAL_LLM=false`。
- 未配置 `OPENAI_API_KEY`。
- 真实模型调用异常需要回退。
- 自动评测脚本和默认演示流程。

要求：

- 当前 `evaluate_test_cases.py` 结果不得回退。
- 高危链式攻击仍应返回 `riskScore=100`、`BLOCKED`、`read_system_file`、RBAC `DENY`。
- 正常请求仍应放行。

### 路径 B：真实大模型普通文本回复

```text
用户输入
-> 输入风险检测
-> 风险评分
-> 调用真实模型
-> 模型返回 text
-> 输出脱敏
-> 审计记录
-> 返回前端
```

适用条件：

- `USE_REAL_LLM=true`。
- `USE_REAL_TOOL_CALL=false`，或模型未返回 `tool_call`。
- 输入风险未达到强阻断阈值。

要求：

- 模型普通文本仍必须经过输出脱敏。
- 审计事件中需要记录 `llmTrace.rawType=text`。
- 如果模型请求失败，应降级到路径 A 或返回可审计的安全失败结果，不能让后端崩溃。

### 路径 C：真实大模型 tool_call 回复

```text
用户输入
-> 输入风险检测
-> 风险评分
-> 调用真实模型并传入 tools schema
-> 模型返回 tool_call
-> tool_call_guard 审计
-> RBAC / 参数边界 / 资源敏感度判断
-> ALLOW 则执行 sandbox_tools 虚拟工具
-> BLOCK 则生成阻断回复
-> 输出脱敏
-> 审计记录
-> 前端证据链展示
```

适用条件：

- `USE_REAL_LLM=true`。
- `USE_REAL_TOOL_CALL=true`。
- `OPENAI_API_KEY` 已配置。
- 模型返回 `tool_call`。

要求：

- `tool_call` 只是模型提出的工具调用请求，不是执行授权。
- `tool_call_guard` 必须先检查工具注册、参数边界、RBAC 和资源敏感度。
- 未注册工具必须 `BLOCK`。
- 非法参数必须 `BLOCK`。
- 高敏资源必须 `BLOCK`。
- `read_system_file` 不得访问真实文件系统。
- 允许执行的工具也只能走 `sandbox_tools.py` 虚拟结果。

## 五、后端改造建议

以下是未来编码阶段的改造规划，本轮不实际修改。

### app/services/chat_service.py 或 app/api/v1/chat.py

建议将当前 `chat/messages` 主线抽出到 `chat_service.py`，再由接口层调用。

未来职责：

- 读取配置开关。
- 默认走当前 MVP 分支。
- 在真实模式开启且 API Key 存在时调用 `llm_client.py`。
- 对真实模型返回的 `text` 和 `tool_call` 分别处理。
- 统一组装返回字段，保持前端兼容。
- 所有异常回退到当前 MVP 或生成可审计安全响应。

### app/services/llm_client.py

未来职责：

- 保留 `generate_plain_reply(prompt)`。
- 保留并完善 `generate_tool_call_response(prompt, tools)`。
- 输出稳定结构：`provider`、`model`、`content`、`toolCalls`、`rawType`、`error`。
- 不打印 API Key。
- 不执行工具。
- 不写审计事件。

### app/services/tool_registry.py

未来职责：

- 继续维护可暴露给模型的虚拟工具 schema。
- 每个工具包含工具名、参数 schema、资源域、风险等级和默认策略。
- 高风险工具可以注册用于验证，但默认不允许执行。

### app/services/tool_call_guard.py

未来职责：

- 审计真实模型返回的每个 `tool_call`。
- 对工具注册、参数边界、资源敏感级别和 RBAC 进行统一判断。
- 输出 `ALLOW` 或 `BLOCKED`。
- 生成可写入审计事件的 `guardResult`。
- 不执行工具。

### app/services/sandbox_tools.py

未来职责：

- 只执行安全虚拟工具。
- `search_public_docs` 返回公开文档模拟结果。
- `read_user_profile` 只允许 `self_profile` 模拟结果。
- `read_system_file` 永远拒绝，不访问真实文件系统。

### app/services/audit_service.py

未来职责：

- 扩展审计事件字段，记录真实模型 trace、guard 结果和 sandbox 执行结果。
- 兼容当前前端已有字段。
- 同时保留 snake_case 和 camelCase 兼容字段。

### app/core/config.py

未来职责：

- 增加 `USE_REAL_LLM`、`USE_REAL_TOOL_CALL`、`LLM_PROVIDER`、`LLM_MODEL`、`LLM_BASE_URL` 等配置读取。
- API Key 只从环境变量读取，不写默认真实值。
- 提供布尔解析函数，避免字符串判断分散在业务代码中。

### app/schemas/chat.py

未来职责：

- 保持请求体兼容 `content` 和 `message`。
- 可扩展响应模型字段，例如 `functionCallSource`、`llmTrace`、`guardResult`、`sandboxExecution`。
- 不强制前端一次性消费新字段。

## 六、审计事件字段扩展设计

建议在现有审计事件结构基础上新增以下字段，同时保留现有字段兼容前端。

### functionCallSource

用于区分工具调用来源：

```json
{
  "functionCallSource": "simulated"
}
```

可选值：

- `simulated`：当前 MVP 根据规则和关键词派生的模拟 Function Calling。
- `real_model_tool_call`：真实模型返回的 `tool_call`。

### llmTrace

用于记录真实模型调用摘要，不记录 API Key。

```json
{
  "llmTrace": {
    "provider": "openai",
    "model": "gpt-4.1-mini",
    "rawType": "tool_call",
    "toolCallId": "call_xxx",
    "toolCallName": "read_system_file",
    "toolCallArguments": {
      "path": "/admin/db_credentials.txt"
    }
  }
}
```

### guardResult

用于记录执行前审计结论。

```json
{
  "guardResult": {
    "decision": "BLOCKED",
    "checks": [],
    "reason": "当前角色无权访问 L4 高敏资源，已在执行前阻断。"
  }
}
```

### sandboxExecution

用于记录虚拟工具是否执行及结果摘要。

```json
{
  "sandboxExecution": {
    "executed": false,
    "toolName": "read_system_file",
    "ok": false,
    "resultSummary": "",
    "error": "高风险工具拒绝执行。"
  }
}
```

## 七、前端展示设计

未来前端证据链可最小增强以下展示，但本轮不修改前端。

1. 模拟工具调用：显示 `functionCallSource=simulated`，沿用当前 Function Calling 卡片。
2. 真实模型 `tool_call`：显示 `functionCallSource=real_model_tool_call`，展示模型、工具名、参数摘要和 tool_call id。
3. guard 审计结果：展示 `guardResult.decision`、`reason` 和 `checks`。
4. sandbox 执行结果：展示是否执行、执行工具、结果摘要或错误。
5. RBAC DENY：继续突出执行前阻断。
6. 输出脱敏：继续展示脱敏前后对比。
7. 真实模型模式标签：在证据链或报告中标注“真实模型模式”，避免与当前模拟调用混淆。

展示原则：

- 不重构 UI。
- 不新增无关页面。
- 只在已有证据链和报告区域补充字段。
- 未开启真实模式时页面表现保持不变。

## 八、风险与回退策略

1. API Key 缺失时回退路径 A，即当前规则 MVP。
2. 模型不返回 `tool_call` 时按普通文本处理，仍进行输出脱敏和审计记录。
3. 模型返回未知工具时 `BLOCK`。
4. 模型返回非法参数、缺失参数或越界参数时 `BLOCK`。
5. `sandbox_tools` 执行失败时 `BLOCK` 或降级为安全失败响应，并记录错误。
6. 任何异常不得导致后端崩溃。
7. 保留当前自动评测脚本不受影响，默认配置下仍只测规则 MVP。
8. 真实模型输出不稳定，不应把真实模型测试结果纳入当前 28 条规则样例回归通过率。
9. 网络失败、超时和供应商错误必须转为可读错误或回退。
10. 审计事件不得记录 API Key、请求头或其他密钥。

## 九、实施步骤

### 阶段 1：增加配置开关

在 `app/core/config.py` 增加 `USE_REAL_LLM` 和 `USE_REAL_TOOL_CALL`，默认 `false`。

验收：

- 默认启动行为不变。
- 未配置 API Key 时不报错。

### 阶段 2：在 chat_service 中增加 real LLM 分支

将真实模型分支放在显式开关后面，默认不进入。

验收：

- `evaluate_test_cases.py` 仍然 28/28。
- 当前前端主线表现不变。

### 阶段 3：接入真实 text 回复

在真实模式开启时先只处理普通文本回复。

验收：

- 有 API Key 时可返回普通文本。
- 输出经过脱敏。
- 审计事件记录 `llmTrace.rawType=text`。

### 阶段 4：接入真实 tool_call 解析

调用 `generate_tool_call_response(prompt, tools)`，解析模型返回的 `toolCalls`。

验收：

- 能识别 `tool_call`。
- 不执行工具。

### 阶段 5：接入 tool_call_guard

所有真实 `tool_call` 先进入 `tool_call_guard.py`。

验收：

- 未注册工具 `BLOCK`。
- 参数越界 `BLOCK`。
- `read_system_file` 高敏访问 `BLOCK`。

### 阶段 6：接入 sandbox_tools

只有 guard `ALLOW` 后才允许执行虚拟工具。

验收：

- `search_public_docs` 可返回模拟公开文档。
- `read_user_profile` 仅允许 `self_profile`。
- `read_system_file` 永不访问真实文件系统。

### 阶段 7：扩展审计事件

写入 `functionCallSource`、`llmTrace`、`guardResult` 和 `sandboxExecution`。

验收：

- 事件详情能展示完整证据。
- 旧字段仍兼容前端。

### 阶段 8：前端证据链展示

在现有证据链和报告展示中补充真实模型字段。

验收：

- 不重构 UI。
- 能区分模拟调用和真实模型 `tool_call`。

### 阶段 9：扩展自动评测

新增真实模型隔离评测口径，不污染当前 28 条规则样例回归结果。

验收：

- 默认规则样例仍稳定。
- 真实模型测试可单独运行。

## 十、验收标准

1. 默认模式下现有 MVP 完全不变。
2. `evaluate_test_cases.py` 仍然 28/28。
3. 无 API Key 时不报错，并回退当前 MVP。
4. 有 API Key 且开启真实模式后，可以获得模型回复。
5. 高危 `tool_call` 必须 `BLOCK`。
6. 允许的虚拟工具可以 `ALLOW`。
7. `read_system_file` 永远不能执行真实文件读取。
8. `events.json` 能记录完整证据链。
9. API Key 不泄露到日志、前端、审计事件或 Git。
10. 前端主线不回退。

## 十一、最小安全实现方案

建议未来第一版真实接入只做最小安全实现：

1. 默认关闭真实模式。
2. 显式开启 `USE_REAL_LLM=true` 时，允许真实模型返回普通文本。
3. 显式开启 `USE_REAL_TOOL_CALL=true` 时，才传入 tools schema。
4. 真实 `tool_call` 只进入 `tool_call_guard.py`。
5. guard `BLOCKED` 时直接生成安全回复并记录审计事件。
6. guard `ALLOWED` 时只执行 `sandbox_tools.py` 中的虚拟工具。
7. 所有输出统一进入脱敏。
8. 审计事件同时记录模型 trace、guard 检查、sandbox 结果和最终结论。

这个方案可以验证真实模型工具调用的安全闭环，同时不引入真实资源访问风险。
