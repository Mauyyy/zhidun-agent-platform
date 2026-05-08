# 智盾Agent Backend

FastAPI 最小后端原型，用 JSON 文件完成输入检测、风险评分、Function Calling 执行前审计、RBAC 越权判断、输出脱敏和审计事件记录。

## 启动

```powershell
cd d:\计算机\zhidun_agent\zhidun-agent-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 接口

- `GET /api/v1/health`
- `POST /api/v1/chat/messages`
- `GET /api/v1/security/events`
- `GET /api/v1/security/events/{eventId}`
- `POST /api/v1/security/events/{eventId}/report`

所有接口返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

## Function Calling 安全审计隔离验证

当前后端已提供虚拟 tools 与 `tool_call_guard` 隔离验证能力，用于验证真实模型 Function Calling 接入前的执行前审计骨架。

运行方式：

```powershell
cd d:\计算机\zhidun_agent\zhidun-agent-backend
python scripts/test_tool_call_guard.py
```

说明：

- 该脚本不调用 `POST /api/v1/chat/messages`。
- 该脚本不写入 `app/data/events.json`。
- 该脚本不执行真实工具，不访问真实文件系统。
- `read_system_file` 仅用于验证高敏工具调用会在执行前被阻断。

## 真实模型 tool_call 输出解析隔离验证（可选）

当前项目默认不依赖真实大模型。配置后端环境变量后，可以单独验证真实模型在给定 tools schema 时返回普通文本或 `tool_call` 的情况。

运行方式：

```powershell
cd d:\计算机\zhidun_agent\zhidun-agent-backend
python scripts/test_real_model_tool_call.py
```

说明：

- 未配置 `OPENAI_API_KEY` 时，脚本会友好跳过真实模型调用。
- 配置 API Key 后，脚本会调用真实模型并解析返回的 `tool_call`。
- 所有 `tool_call` 只会进入 `tool_call_guard` 审计，不会直接执行工具。
- 该脚本不调用 `POST /api/v1/chat/messages`，不写入 `app/data/events.json`。

## 真实大模型普通文本回复模式（可选）

当前 `POST /api/v1/chat/messages` 默认仍使用规则 MVP。只有显式开启 `USE_REAL_LLM=true` 且后端配置 `OPENAI_API_KEY` 时，低风险普通请求才会尝试调用真实大模型生成普通文本回复。

安全边界：

- 默认关闭，不影响当前 MVP。
- 本模式不接入真实 Function Calling 主线。
- 高危请求、已阻断请求、触发 `read_system_file` 或 RBAC deny 的请求不会调用真实模型。
- 真实模型回复仍会经过输出脱敏。
- 没有 API Key 或调用失败时会自动回退当前 MVP，不让接口报 500。
- API Key 只能放在后端环境变量，不允许写入前端或提交到 Git。

启动示例：

```powershell
cd d:\计算机\zhidun_agent\zhidun-agent-backend
$env:USE_REAL_LLM="true"
$env:OPENAI_API_KEY="your_api_key_here"
$env:LLM_MODEL="gpt-4.1-mini"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
