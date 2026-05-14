from __future__ import annotations

import asyncio
import sys
from contextlib import AsyncExitStack
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from elek_mcp_demo.client.mcp_tools import McpToolClient

OUTPUT_PATH = PROJECT_ROOT / "examples" / "outputs" / "voltage_drop_report.md"


async def main() -> None:
    question = (
        "For a 50 m three-phase cable carrying 80 A at 415 V, estimate the "
        "voltage drop using the available assumptions, check it against the "
        "demo acceptance threshold, and generate a short engineering report."
    )

    async with AsyncExitStack() as stack:
        docs = await stack.enter_async_context(
            McpToolClient("elek_mcp_demo.servers.docs_server", PROJECT_ROOT)
        )
        calc = await stack.enter_async_context(
            McpToolClient("elek_mcp_demo.servers.calc_server", PROJECT_ROOT)
        )
        reports = await stack.enter_async_context(
            McpToolClient("elek_mcp_demo.servers.report_server", PROJECT_ROOT)
        )

        evidence = await docs.call_tool(
            "search_docs",
            {"query": "voltage drop default cable values acceptance threshold", "limit": 3},
        )
        formula_section = await docs.call_tool(
            "get_doc_section",
            {"section_id": "voltage_drop_assumptions:demo-voltage-drop-formula"},
        )

        calculation = await calc.call_tool(
            "calculate_voltage_drop",
            {
                "current_a": 80,
                "length_m": 50,
                "line_voltage_v": 415,
                "resistance_ohm_per_km": 0.524,
                "reactance_ohm_per_km": 0.08,
                "power_factor": 0.85,
                "threshold_percent": 5.0,
            },
        )

        report = await reports.call_tool(
            "generate_engineering_report",
            {
                "title": "Voltage Drop Demo Report",
                "user_question": question,
                "inputs": {
                    "current_a": 80,
                    "length_m": 50,
                    "line_voltage_v": 415,
                    "resistance_ohm_per_km": 0.524,
                    "reactance_ohm_per_km": 0.08,
                    "power_factor": 0.85,
                    "threshold_percent": 5.0,
                },
                "assumptions": [
                    "Balanced three-phase load.",
                    "Cable impedance values are mock demo assumptions.",
                    "The acceptance threshold is a demo threshold, not a compliance claim.",
                    f"Formula source: {formula_section['source_file']} / {formula_section['section_id']}.",
                ],
                "evidence": evidence,
                "calculation_result": calculation,
                "limitations": [
                    "No cable derating, thermal modelling, protection coordination, or standards compliance check is performed.",
                    "The mock documentation is included for MCP orchestration demonstration only.",
                ],
                "suggested_next_checks": [
                    "Confirm cable catalogue impedance values.",
                    "Check installation method and derating factors.",
                    "Review protection coordination and applicable standards with a qualified engineer.",
                ],
                "tool_trace": [
                    "docs_server.search_docs",
                    "docs_server.get_doc_section",
                    "calc_server.calculate_voltage_drop",
                    "report_server.generate_engineering_report",
                ],
            },
        )

    markdown = report["markdown"] if isinstance(report, dict) else str(report)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(markdown, encoding="utf-8")
    print(markdown)
    print(f"\nSaved report to {OUTPUT_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
