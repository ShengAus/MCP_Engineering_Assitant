from __future__ import annotations

from typing import Any

from elek_mcp_demo.domain.models import EngineeringReportInput, EngineeringReportResult


STANDARD_LIMITATION = (
    "This is a demonstration workflow only and is not certified electrical design software."
)


def generate_engineering_report(report_input: EngineeringReportInput) -> EngineeringReportResult:
    limitations = list(report_input.limitations)
    if STANDARD_LIMITATION not in limitations:
        limitations.insert(0, STANDARD_LIMITATION)

    lines: list[str] = [
        f"# {report_input.title}",
        "",
        "## User Question",
        "",
        report_input.user_question,
        "",
        "## Inputs",
        "",
        *format_mapping(report_input.inputs),
        "",
        "## Assumptions",
        "",
        *format_list(report_input.assumptions),
        "",
        "## Retrieved Evidence",
        "",
    ]

    if report_input.evidence:
        for item in report_input.evidence:
            lines.extend(
                [
                    f"- `{item.source_file}` / `{item.section_id}`: {item.snippet}",
                ]
            )
    else:
        lines.append("- No retrieved evidence was provided.")

    lines.extend(
        [
            "",
            "## Calculation Result",
            "",
            *format_mapping(report_input.calculation_result),
            "",
            "## Acceptance Check",
            "",
            acceptance_text(report_input.calculation_result),
            "",
            "## Limitations",
            "",
            *format_list(limitations),
            "",
            "## Suggested Next Checks",
            "",
            *format_list(report_input.suggested_next_checks),
            "",
            "## Tool Trace",
            "",
            *format_list(report_input.tool_trace),
            "",
        ]
    )

    return EngineeringReportResult(markdown="\n".join(lines))


def acceptance_text(result: dict[str, Any]) -> str:
    is_within = result.get("is_within_threshold")
    percent = result.get("voltage_drop_percent")
    threshold = result.get("threshold_percent")

    if is_within is True:
        return (
            f"The estimated voltage drop is {percent}%, which is within the "
            f"{threshold}% demo threshold."
        )
    if is_within is False:
        return (
            f"The estimated voltage drop is {percent}%, which exceeds the "
            f"{threshold}% demo threshold and requires engineering review."
        )
    return "No acceptance result was provided."


def format_mapping(values: dict[str, Any]) -> list[str]:
    if not values:
        return ["- None provided."]
    return [f"- `{key}`: {value}" for key, value in values.items()]


def format_list(values: list[str]) -> list[str]:
    if not values:
        return ["- None provided."]
    return [f"- {value}" for value in values]
