import json
import os
import urllib.error
import urllib.request
from typing import Any


DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_TIMEOUT_SECONDS = 30


def generate_plain_reply(prompt: str) -> dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower() or DEFAULT_PROVIDER
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    base_url = (os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL).rstrip("/")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if provider != "openai":
        return _failure(provider, model, f"暂仅支持 openai provider，当前配置为 {provider}")

    if not api_key:
        return _failure(provider, model, "缺少 OPENAI_API_KEY")

    if not prompt.strip():
        return _failure(provider, model, "prompt 不能为空")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是智盾Agent的隔离验证助手，只返回普通文本，不调用任何工具。",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
    }

    request = urllib.request.Request(
        url=f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return _failure(provider, model, _safe_http_error(exc))
    except urllib.error.URLError as exc:
        return _failure(provider, model, f"大模型请求失败：{exc.reason}")
    except TimeoutError:
        return _failure(provider, model, "大模型请求超时")
    except Exception as exc:
        return _failure(provider, model, f"大模型调用异常：{exc.__class__.__name__}")

    try:
        data = json.loads(body)
        content = data["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return _failure(provider, model, "大模型响应格式无法解析")

    return {
        "ok": True,
        "provider": provider,
        "model": model,
        "content": content,
        "error": None,
    }


def generate_tool_call_response(prompt: str, tools: list[dict[str, Any]]) -> dict[str, Any]:
    provider = os.getenv("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower() or DEFAULT_PROVIDER
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    base_url = (os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL).rstrip("/")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    if provider != "openai":
        return _tool_failure(provider, model, f"暂仅支持 openai provider，当前配置为 {provider}")

    if not api_key:
        return _tool_failure(
            provider,
            model,
            "未配置 OPENAI_API_KEY，跳过真实模型 tool_call 测试。",
            skipped=True,
        )

    if not prompt.strip():
        return _tool_failure(provider, model, "prompt 不能为空")

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是智盾Agent的隔离验证助手。你可以根据用户问题选择工具，"
                    "但工具调用只是请求，不代表已经获得授权。"
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "tools": tools,
        "tool_choice": "auto",
        "temperature": 0.2,
    }

    request = urllib.request.Request(
        url=f"{base_url}/chat/completions",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        timeout = int(os.getenv("LLM_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return _tool_failure(provider, model, _safe_http_error(exc))
    except urllib.error.URLError as exc:
        return _tool_failure(provider, model, f"大模型请求失败：{exc.reason}")
    except TimeoutError:
        return _tool_failure(provider, model, "大模型请求超时")
    except Exception as exc:
        return _tool_failure(provider, model, f"大模型调用异常：{exc.__class__.__name__}")

    try:
        data = json.loads(body)
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError):
        return _tool_failure(provider, model, "大模型响应格式无法解析")

    tool_calls = _parse_tool_calls(message.get("tool_calls") or [])
    content = message.get("content") or ""

    return {
        "ok": True,
        "skipped": False,
        "provider": provider,
        "model": model,
        "content": content,
        "toolCalls": tool_calls,
        "rawType": "tool_call" if tool_calls else "text",
        "error": None,
    }


def _failure(provider: str, model: str, error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "provider": provider,
        "model": model,
        "content": "",
        "error": error,
    }


def _tool_failure(provider: str, model: str, error: str, skipped: bool = False) -> dict[str, Any]:
    return {
        "ok": False,
        "skipped": skipped,
        "provider": provider,
        "model": model,
        "content": "",
        "toolCalls": [],
        "rawType": "error",
        "error": error,
    }


def _parse_tool_calls(raw_tool_calls: list[Any]) -> list[dict[str, Any]]:
    tool_calls: list[dict[str, Any]] = []
    for raw_tool_call in raw_tool_calls:
        if not isinstance(raw_tool_call, dict):
            continue
        function_payload = raw_tool_call.get("function") or {}
        if not isinstance(function_payload, dict):
            continue
        tool_calls.append(
            {
                "id": raw_tool_call.get("id") or "",
                "name": function_payload.get("name") or "",
                "arguments": _parse_arguments(function_payload.get("arguments")),
            }
        )
    return tool_calls


def _parse_arguments(raw_arguments: Any) -> dict[str, Any]:
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if not isinstance(raw_arguments, str) or not raw_arguments.strip():
        return {}
    try:
        parsed = json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {"_raw": raw_arguments}
    return parsed if isinstance(parsed, dict) else {"_raw": raw_arguments}


def _safe_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8")
        data = json.loads(body)
        message = data.get("error", {}).get("message") or body
    except Exception:
        message = exc.reason or "HTTP error"
    return f"大模型接口返回 HTTP {exc.code}：{message}"
