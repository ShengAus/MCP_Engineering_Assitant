from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from elek_mcp_demo.client.llm_host import SYSTEM_PROMPT, complete_report_arguments, run_llm_tool_loop
from elek_mcp_demo.domain.calculations import calculate_voltage_drop
from elek_mcp_demo.domain.docs import get_doc_section, search_docs
from elek_mcp_demo.domain.models import EngineeringReportInput, VoltageDropInput
from elek_mcp_demo.domain.reports import generate_engineering_report


@dataclass(frozen=True)
class EvalResult:
    name: str
    passed: bool
    details: str


def eval_retrieval_quality() -> EvalResult:
    formula_results = search_docs("voltage drop formula acceptance threshold", limit=5)
    formula_ids = {item.section_id for item in formula_results}
    required_formula_ids = {
        "voltage_drop_assumptions:demo-voltage-drop-formula",
        "voltage_drop_assumptions:demo-acceptance-threshold",
    }

    safety_results = search_docs("not certified design software safety limitations", limit=3)
    safety_ids = {item.section_id for item in safety_results}

    passed = required_formula_ids.issubset(formula_ids) and (
        "design_limitations:not-certified-design-software" in safety_ids
    )
    return EvalResult(
        name="retrieval_quality",
        passed=passed,
        details=(
            "Expected voltage-drop formula, acceptance threshold, and safety limitation "
            f"sections. Formula query returned {sorted(formula_ids)}; safety query returned "
            f"{sorted(safety_ids)}."
        ),
    )


def eval_unsupported_answer_refusal_control() -> EvalResult:
    completed = complete_report_arguments(
        arguments={
            "assumptions": ["AS/NZS compliance is confirmed."],
            "limitations": ["No limitations."],
            "suggested_next_checks": ["No further review needed."],
            "tool_trace": ["llm_invented_trace"],
        },
        question="Can I use this cable design for production installation?",
        latest_inputs={"current_a": 80},
        latest_calculation_result={
            "voltage_drop_percent": 0.8139,
            "threshold_percent": 5.0,
            "is_within_threshold": True,
            "inputs": {"current_a": 80.0},
        },
        latest_evidence=[],
        executed_mcp_tools=["calc_server.calculate_voltage_drop"],
    )

    serialized = json.dumps(completed, ensure_ascii=True)
    passed = (
        "AS/NZS compliance is confirmed" not in serialized
        and "No limitations" not in serialized
        and "No further review needed" not in serialized
        and "not a compliance claim" in serialized
        and "standards compliance check is performed" in serialized
    )
    return EvalResult(
        name="unsupported_answer_refusal_control",
        passed=passed,
        details="Host-controlled report assembly removes unsupported compliance claims.",
    )


async def eval_tool_call_correctness() -> EvalResult:
    llm = ScriptedLlm(
        [
            tool_response(
                "call_docs",
                "docs_search_docs",
                {"query": "voltage drop formula acceptance threshold", "limit": 3},
            ),
            tool_response(
                "call_calc",
                "calc_calculate_voltage_drop",
                {
                    "current_a": 80,
                    "length_m": 50,
                    "line_voltage_v": 415,
                    "resistance_ohm_per_km": 0.524,
                    "reactance_ohm_per_km": 0.08,
                    "power_factor": 0.85,
                    "threshold_percent": 5.0,
                },
            ),
            tool_response("call_report", "report_generate_engineering_report", {}),
            {"choices": [{"message": {"role": "assistant", "content": "Done."}}]},
        ]
    )
    trace: list[str] = []
    result = await run_llm_tool_loop(
        llm=llm,
        question=(
            "For a 50 m three-phase cable carrying 80 A at 415 V, estimate the voltage "
            "drop and generate a short engineering report."
        ),
        clients={
            "docs": InProcessMcpClient("docs"),
            "calc": InProcessMcpClient("calc"),
            "report": InProcessMcpClient("report"),
        },
        trace=trace,
    )

    passed = (
        "# Voltage Drop Demo Report" in result
        and "docs_server.search_docs" in result
        and "calc_server.calculate_voltage_drop" in result
        and "report_server.generate_engineering_report" in result
        and any("calling report_generate_engineering_report" in item for item in trace)
    )
    return EvalResult(
        name="tool_call_correctness",
        passed=passed,
        details=f"Tool-loop trace: {trace}",
    )


def eval_prompt_regression() -> EvalResult:
    required_phrases = [
        "Use the MCP tools for retrieval, calculations, and report generation.",
        "Do not invent electrical standards",
        "Do not perform engineering calculations yourself",
        "You must call report_generate_engineering_report",
        "Always state that this is not certified electrical design software.",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in SYSTEM_PROMPT]

    return EvalResult(
        name="prompt_regression",
        passed=not missing,
        details=(
            "System prompt retains required runtime instructions."
            if not missing
            else f"Missing required phrases: {missing}"
        ),
    )


def run_all_evals() -> list[EvalResult]:
    return [
        eval_retrieval_quality(),
        eval_unsupported_answer_refusal_control(),
        asyncio.run(eval_tool_call_correctness()),
        eval_prompt_regression(),
    ]


def assert_all_passed(results: list[EvalResult]) -> None:
    failures = [result for result in results if not result.passed]
    if failures:
        details = "\n".join(f"- {result.name}: {result.details}" for result in failures)
        raise AssertionError(f"LLM eval failures:\n{details}")


class ScriptedLlm:
    def __init__(self, responses: list[dict[str, Any]]):
        self._responses = list(responses)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        tool_choice: str = "auto",
    ) -> dict[str, Any]:
        if not self._responses:
            return {"choices": [{"message": {"role": "assistant", "content": "No scripted response."}}]}
        return self._responses.pop(0)


class InProcessMcpClient:
    def __init__(self, server_alias: str):
        self.server_alias = server_alias

    async def list_tools(self) -> list[dict[str, Any]]:
        return TOOL_SCHEMAS[self.server_alias]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        if self.server_alias == "docs" and name == "search_docs":
            return [item.model_dump() for item in search_docs(**arguments)]
        if self.server_alias == "docs" and name == "get_doc_section":
            return get_doc_section(**arguments).model_dump()
        if self.server_alias == "calc" and name == "calculate_voltage_drop":
            return calculate_voltage_drop(VoltageDropInput(**arguments)).model_dump()
        if self.server_alias == "report" and name == "generate_engineering_report":
            return generate_engineering_report(
                EngineeringReportInput(**arguments)
            ).model_dump()
        raise KeyError(f"Unknown in-process tool: {self.server_alias}.{name}")


def tool_response(call_id: str, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(arguments),
                            },
                        }
                    ],
                }
            }
        ]
    }


TOOL_SCHEMAS: dict[str, list[dict[str, Any]]] = {
    "docs": [
        {
            "name": "search_docs",
            "description": "Search local engineering notes.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer"},
                },
                "required": ["query"],
            },
        },
        {
            "name": "get_doc_section",
            "description": "Fetch a complete source section by section ID.",
            "inputSchema": {
                "type": "object",
                "properties": {"section_id": {"type": "string"}},
                "required": ["section_id"],
            },
        },
    ],
    "calc": [
        {
            "name": "calculate_voltage_drop",
            "description": "Estimate simplified three-phase voltage drop.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "current_a": {"type": "number"},
                    "length_m": {"type": "number"},
                    "line_voltage_v": {"type": "number"},
                    "resistance_ohm_per_km": {"type": "number"},
                    "reactance_ohm_per_km": {"type": "number"},
                    "power_factor": {"type": "number"},
                    "threshold_percent": {"type": "number"},
                },
                "required": [
                    "current_a",
                    "length_m",
                    "line_voltage_v",
                    "resistance_ohm_per_km",
                    "reactance_ohm_per_km",
                    "power_factor",
                ],
            },
        }
    ],
    "report": [
        {
            "name": "generate_engineering_report",
            "description": "Generate a deterministic Markdown report.",
            "inputSchema": {"type": "object", "properties": {}},
        }
    ],
}


if __name__ == "__main__":
    eval_results = run_all_evals()
    for eval_result in eval_results:
        status = "PASS" if eval_result.passed else "FAIL"
        print(f"{status} {eval_result.name}: {eval_result.details}")
    assert_all_passed(eval_results)
