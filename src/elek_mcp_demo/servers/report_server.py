from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from elek_mcp_demo.domain.models import EngineeringReportInput, EvidenceItem
from elek_mcp_demo.domain.reports import generate_engineering_report as generate


mcp = FastMCP("engineering-reports")


@mcp.tool()
def generate_engineering_report(
    user_question: str,
    inputs: dict[str, Any],
    calculation_result: dict[str, Any],
    evidence: list[dict[str, Any]],
    assumptions: list[str],
    limitations: list[str],
    suggested_next_checks: list[str],
    tool_trace: list[str],
    title: str = "Engineering Calculation Report",
) -> dict:
    """Generate a deterministic Markdown engineering report."""
    report_input = EngineeringReportInput(
        title=title,
        user_question=user_question,
        inputs=inputs,
        assumptions=assumptions,
        evidence=[EvidenceItem(**item) for item in evidence],
        calculation_result=calculation_result,
        limitations=limitations,
        suggested_next_checks=suggested_next_checks,
        tool_trace=tool_trace,
    )
    return generate(report_input).model_dump()


if __name__ == "__main__":
    mcp.run()
