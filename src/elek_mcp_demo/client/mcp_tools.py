from __future__ import annotations

import json
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class McpToolClient:
    """Small MCP stdio client for one server module."""

    def __init__(self, module: str, project_root: Path):
        self.module = module
        self.project_root = project_root
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None

    async def __aenter__(self) -> "McpToolClient":
        env = dict(os.environ)
        src_path = str(self.project_root / "src")
        env["PYTHONPATH"] = (
            f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
            if env.get("PYTHONPATH")
            else src_path
        )
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", self.module],
            env=env,
        )
        read_stream, write_stream = await self._stack.enter_async_context(stdio_client(params))
        session = await self._stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()
        self._session = session
        return self

    async def __aexit__(self, exc_type: object, exc: object, tb: object) -> None:
        await self._stack.aclose()

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if self._session is None:
            raise RuntimeError("MCP session is not initialized.")
        result = await self._session.call_tool(name, arguments=arguments)
        # print(result, result.keys() if isinstance(result, dict) else "Not a dict")
        # exit()
        return normalize_tool_result(result)

    async def list_tools(self) -> list[dict[str, Any]]:
        if self._session is None:
            raise RuntimeError("MCP session is not initialized.")
        result = await self._session.list_tools()
        # print("here")
        # print(result.tools)
        return [tool.model_dump() for tool in result.tools]


def normalize_tool_result(result: Any) -> Any:
    if getattr(result, "isError", False):
        content = getattr(result, "content", None) or []
        message = "\n".join(getattr(item, "text", str(item)) for item in content)
        raise RuntimeError(message or "MCP tool call failed.")

    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return unwrap_result(structured)

    content = getattr(result, "content", None)
    if not content:
        return None

    if len(content) == 1 and hasattr(content[0], "text"):
        text = content[0].text
        try:
            return unwrap_result(json.loads(text))
        except json.JSONDecodeError:
            return text

    values: list[Any] = []
    for item in content:
        text = getattr(item, "text", None)
        if text is None:
            values.append(item)
            continue
        try:
            values.append(unwrap_result(json.loads(text)))
        except json.JSONDecodeError:
            values.append(text)
    return values


def unwrap_result(value: Any) -> Any:
    if isinstance(value, dict) and set(value.keys()) == {"result"}:
        return value["result"]
    return value
