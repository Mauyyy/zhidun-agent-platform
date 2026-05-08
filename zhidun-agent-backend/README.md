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
