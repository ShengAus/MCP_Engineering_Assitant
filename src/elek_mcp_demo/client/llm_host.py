from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from elek_mcp_demo.client.mcp_tools import McpToolClient
from elek_mcp_demo.client.openai_compatible import OpenAICompatibleChatClient


@dataclass
class RegisteredTool:
    llm_name: str
    server_alias: str
    mcp_name: str
    client: McpToolClient


async def build_llm_tools(
    clients: dict[str, McpToolClient],
) -> tuple[list[dict[str, Any]], dict[str, RegisteredTool]]:
    llm_tools: list[dict[str, Any]] = []
    registry: dict[str, RegisteredTool] = {}

    for server_alias, client in clients.items():
        for tool in await client.list_tools():
            mcp_name = tool["name"]
            llm_name = sanitize_tool_name(f"{server_alias}_{mcp_name}")
            registry[llm_name] = RegisteredTool(
                llm_name=llm_name,
                server_alias=server_alias,
                mcp_name=mcp_name,
                client=client,
            )
            llm_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": llm_name,
                        "description": f"[{server_alias} MCP server] {tool.get('description') or mcp_name}",
                        "parameters": tool.get("inputSchema")
                        or {"type": "object", "properties": {}},
                    },
                }
            )

    return llm_tools, registry


async def run_llm_tool_loop(
    llm: OpenAICompatibleChatClient,
    question: str,
    clients: dict[str, McpToolClient],
    max_turns: int = 8,
    require_report: bool = True,
    trace: list[str] | None = None,
) -> str:
    tools, registry = await build_llm_tools(clients)
    tool_names = ", ".join(tool["function"]["name"] for tool in tools)
    messages: list[dict[str, Any]] = [
        {
            "role": "system",
            "content": f"{SYSTEM_PROMPT}\n\nAvailable tool names: {tool_names}",
        },
        {
            "role": "user",
            "content": question,
        },
    ]
    last_report_markdown: str | None = None
    latest_evidence: list[dict[str, Any]] = []
    latest_inputs: dict[str, Any] = {}
    latest_calculation_result: dict[str, Any] = {}
    executed_mcp_tools: list[str] = []

    for turn_index in range(max_turns):
        response = await llm.chat(messages=messages, tools=tools)
        message = response["choices"][0]["message"]
        messages.append(message)

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            if (
                require_report
                and "report_generate_engineering_report" in registry
                and not last_report_markdown
            ):
                add_trace(
                    trace,
                    f"turn {turn_index + 1}: model answered without report tool; requesting report tool call",
                )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "You have not called report_generate_engineering_report yet. "
                            "Call that tool now using the prior retrieved evidence, calculation "
                            "result, inputs, limitations, and tool trace. Do not provide the "
                            "final answer until the report tool has returned."
                        ),
                    }
                )
                continue
            if last_report_markdown:
                return last_report_markdown
            return message.get("content") or ""

        for tool_call in tool_calls:
            function = tool_call["function"]
            tool_name = function["name"]
            add_trace(trace, f"turn {turn_index + 1}: calling {tool_name}")
            registered_tool = registry.get(tool_name)
            if registered_tool is None:
                tool_result: Any = {"error": f"Unknown tool: {tool_name}"}
            else:
                try:
                    arguments = json.loads(function.get("arguments") or "{}")
                    if (
                        registered_tool.server_alias == "report"
                        and registered_tool.mcp_name == "generate_engineering_report"
                    ):
                        if "docs" in clients and not has_evidence_section(
                            latest_evidence,
                            "voltage_drop_assumptions:demo-voltage-drop-formula",
                        ):
                            formula_section = await clients["docs"].call_tool(
                                "get_doc_section",
                                {
                                    "section_id": "voltage_drop_assumptions:demo-voltage-drop-formula"
                                },
                            )
                            add_trace(
                                trace,
                                "host: fetched docs_get_doc_section for canonical report traceability",
                            )
                            if isinstance(formula_section, dict):
                                latest_evidence.append(formula_section)
                                executed_mcp_tools.append("docs_server.get_doc_section")
                        arguments = complete_report_arguments(
                            arguments=arguments,
                            question=question,
                            latest_inputs=latest_inputs,
                            latest_calculation_result=latest_calculation_result,
                            latest_evidence=latest_evidence,
                            executed_mcp_tools=[
                                *executed_mcp_tools,
                                "report_server.generate_engineering_report",
                            ],
                        )
                    add_trace(trace, f"arguments for {tool_name}: {json.dumps(arguments, ensure_ascii=True)}")
                    tool_result = await registered_tool.client.call_tool(
                        registered_tool.mcp_name,
                        arguments,
                    )
                    if (
                        registered_tool.server_alias == "docs"
                        and registered_tool.mcp_name == "search_docs"
                        and isinstance(tool_result, list)
                    ):
                        executed_mcp_tools.append("docs_server.search_docs")
                        latest_evidence = [
                            item for item in tool_result if isinstance(item, dict)
                        ]
                    elif (
                        registered_tool.server_alias == "docs"
                        and registered_tool.mcp_name == "get_doc_section"
                        and isinstance(tool_result, dict)
                    ):
                        executed_mcp_tools.append("docs_server.get_doc_section")
                        latest_evidence.append(tool_result)
                    elif (
                        registered_tool.server_alias == "calc"
                        and registered_tool.mcp_name == "calculate_voltage_drop"
                        and isinstance(tool_result, dict)
                    ):
                        executed_mcp_tools.append("calc_server.calculate_voltage_drop")
                        latest_inputs = dict(arguments)
                        latest_calculation_result = tool_result
                    if (
                        registered_tool.server_alias == "report"
                        and registered_tool.mcp_name == "generate_engineering_report"
                        and isinstance(tool_result, dict)
                        and isinstance(tool_result.get("markdown"), str)
                    ):
                        executed_mcp_tools.append("report_server.generate_engineering_report")
                        last_report_markdown = tool_result["markdown"]
                except Exception as exc:  # surface tool errors to the LLM host
                    tool_result = {"error": str(exc)}
                    add_trace(trace, f"error from {tool_name}: {exc}")

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": tool_name,
                    "content": json.dumps(tool_result, ensure_ascii=True),
                }
            )

    return (
        "The LLM host reached the maximum tool loop turns before producing a final "
        "answer. Try the deterministic MCP demo for the guaranteed workflow."
    )


def sanitize_tool_name(name: str) -> str:
    sanitized = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    return sanitized[:64]


def add_trace(trace: list[str] | None, message: str) -> None:
    if trace is not None:
        trace.append(message)


def complete_report_arguments(
    arguments: dict[str, Any],
    question: str,
    latest_inputs: dict[str, Any],
    latest_calculation_result: dict[str, Any],
    latest_evidence: list[dict[str, Any]],
    executed_mcp_tools: list[str] | None = None,
) -> dict[str, Any]:
    # The model is allowed to decide *when* to request the report tool, but the
    # host owns the report payload so the saved artifact remains deterministic.
    completed = dict(arguments)
    completed["title"] = "Voltage Drop Demo Report"
    completed["user_question"] = question
    completed["inputs"] = canonical_report_inputs(
        latest_inputs=latest_inputs,
        latest_calculation_result=latest_calculation_result,
    )
    completed["calculation_result"] = latest_calculation_result
    completed["evidence"] = normalize_evidence_argument(None, latest_evidence)
    completed["assumptions"] = canonical_report_assumptions(completed["evidence"])
    completed["limitations"] = [
        "No cable derating, thermal modelling, protection coordination, or standards compliance check is performed.",
        "The mock documentation is included for MCP orchestration demonstration only.",
    ]
    completed["suggested_next_checks"] = [
        "Confirm cable catalogue impedance values.",
        "Check installation method and derating factors.",
        "Review protection coordination and applicable standards with a qualified engineer.",
    ]
    completed["tool_trace"] = canonical_tool_trace(executed_mcp_tools)
    return completed


def canonical_report_inputs(
    latest_inputs: dict[str, Any],
    latest_calculation_result: dict[str, Any],
) -> dict[str, Any]:
    result_inputs = latest_calculation_result.get("inputs")
    if isinstance(result_inputs, dict):
        return result_inputs
    return latest_inputs


def canonical_report_assumptions(evidence: list[dict[str, Any]]) -> list[str]:
    formula_source = next(
        (
            f"{item['source_file']} / {item['section_id']}"
            for item in evidence
            if isinstance(item, dict)
            and item.get("section_id") == "voltage_drop_assumptions:demo-voltage-drop-formula"
            and item.get("source_file")
        ),
        "voltage_drop_assumptions.md / voltage_drop_assumptions:demo-voltage-drop-formula",
    )
    return [
        "Balanced three-phase load.",
        "Cable impedance values are mock demo assumptions.",
        "The acceptance threshold is a demo threshold, not a compliance claim.",
        f"Formula source: {formula_source}.",
    ]


def canonical_tool_trace(executed_mcp_tools: list[str] | None) -> list[str]:
    ordered_names = [
        "docs_server.search_docs",
        "docs_server.get_doc_section",
        "calc_server.calculate_voltage_drop",
        "report_server.generate_engineering_report",
    ]
    executed = set(executed_mcp_tools or ordered_names)
    return [name for name in ordered_names if name in executed]


def has_evidence_section(evidence: list[dict[str, Any]], section_id: str) -> bool:
    return any(
        isinstance(item, dict) and item.get("section_id") == section_id
        for item in evidence
    )


def normalize_evidence_argument(
    evidence: Any,
    latest_evidence: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if evidence is None:
        return latest_evidence

    if not isinstance(evidence, list):
        evidence = [evidence]

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(evidence, start=1):
        if isinstance(item, dict) and all(
            key in item for key in ("section_id", "title", "source_file", "snippet")
        ):
            normalized.append(item)
            continue

        if latest_evidence:
            return latest_evidence

        normalized.append(
            {
                "section_id": f"llm-supplied-evidence-{index}",
                "title": "LLM supplied evidence",
                "source_file": "llm_host",
                "snippet": str(item),
                "score": 0,
            }
        )

    return normalized


SYSTEM_PROMPT = """You are a narrow engineering assistant host for an MCP demo.

Use the MCP tools for retrieval, calculations, and report generation.
Do not invent electrical standards, catalogue values, or compliance claims.
Do not perform engineering calculations yourself when a calculation tool is available.
You must call report_generate_engineering_report before producing the final answer.
The final answer should be the Markdown returned by report_generate_engineering_report.
Do not offer to prepare the report later.
For the voltage-drop workflow:
1. Search the engineering notes for formula assumptions, default values, thresholds, and limitations.
2. Retrieve any section needed for traceability.
3. Call the voltage-drop calculation tool with numeric inputs.
4. Call the report-generation tool to create the final report.
When calling report_generate_engineering_report, include:
- inputs: the numeric calculation inputs
- calculation_result: the exact calculation tool output
- evidence: source objects returned by docs_search_docs or docs_get_doc_section

Always state that this is not certified electrical design software.
"""
