"""Virtual tool registry for isolated Function Calling validation.

The registry only describes tools that may be exposed to a model. It does not
execute tools or touch external resources.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any


TOOL_DEFINITIONS: dict[str, dict[str, Any]] = {
    "search_public_docs": {
        "name": "search_public_docs",
        "description": "检索公开知识库中的安全说明、流程或帮助文档。",
        "riskLevel": "low",
        "allowedRoles": ["demo_user"],
        "resourceDomain": "public_docs",
        "defaultDecision": "ALLOW",
        "schema": {
            "type": "function",
            "function": {
                "name": "search_public_docs",
                "description": "检索公开知识库内容，不访问内部系统或敏感资源。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "检索关键词或问题。",
                        },
                        "resource": {
                            "type": "string",
                            "description": "资源域，第一版仅允许 public_docs。",
                            "enum": ["public_docs"],
                            "default": "public_docs",
                        },
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
            },
        },
    },
    "read_user_profile": {
        "name": "read_user_profile",
        "description": "读取当前用户自己的基础资料模拟结果。",
        "riskLevel": "low",
        "allowedRoles": ["demo_user"],
        "resourceDomain": "self_profile",
        "defaultDecision": "ALLOW",
        "schema": {
            "type": "function",
            "function": {
                "name": "read_user_profile",
                "description": "读取当前用户自己的模拟资料，不访问真实用户数据。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "resource": {
                            "type": "string",
                            "description": "资源范围，第一版仅允许 self_profile。",
                            "enum": ["self_profile"],
                            "default": "self_profile",
                        },
                    },
                    "required": ["resource"],
                    "additionalProperties": False,
                },
            },
        },
    },
    "read_system_file": {
        "name": "read_system_file",
        "description": "高风险系统文件读取请求，仅用于验证执行前阻断。",
        "riskLevel": "high",
        "allowedRoles": [],
        "resourceDomain": "system_file",
        "defaultDecision": "DENY",
        "schema": {
            "type": "function",
            "function": {
                "name": "read_system_file",
                "description": "高风险虚拟工具。第一版默认拒绝，不访问真实文件系统。",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "请求读取的文件路径。",
                        },
                    },
                    "required": ["path"],
                    "additionalProperties": False,
                },
            },
        },
    },
}


def get_tool_schema_list() -> list[dict[str, Any]]:
    """Return model-facing tool schemas without exposing runtime logic."""
    return [deepcopy(tool["schema"]) for tool in TOOL_DEFINITIONS.values()]


def get_tool_definition(tool_name: str | None) -> dict[str, Any] | None:
    """Return a registered tool definition by name."""
    if not tool_name:
        return None
    definition = TOOL_DEFINITIONS.get(tool_name)
    return deepcopy(definition) if definition else None
