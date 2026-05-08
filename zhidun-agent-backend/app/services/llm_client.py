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


def _failure(provider: str, model: str, error: str) -> dict[str, Any]:
    return {
        "ok": False,
        "provider": provider,
        "model": model,
        "content": "",
        "error": error,
    }


def _safe_http_error(exc: urllib.error.HTTPError) -> str:
    try:
        body = exc.read().decode("utf-8")
        data = json.loads(body)
        message = data.get("error", {}).get("message") or body
    except Exception:
        message = exc.reason or "HTTP error"
    return f"大模型接口返回 HTTP {exc.code}：{message}"
