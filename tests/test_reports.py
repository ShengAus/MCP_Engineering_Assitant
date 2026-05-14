from elek_mcp_demo.domain.models import EngineeringReportInput, EvidenceItem
from elek_mcp_demo.domain.reports import generate_engineering_report


def test_report_contains_required_sections_and_limitation() -> None:
    report = generate_engineering_report(
        EngineeringReportInput(
            user_question="Estimate voltage drop.",
            inputs={"current_a": 80},
            assumptions=["Balanced three-phase load."],
            evidence=[
                EvidenceItem(
                    section_id="voltage_drop_assumptions:demo-voltage-drop-formula",
                    title="demo-voltage-drop-formula",
                    source_file="voltage_drop_assumptions.md",
                    snippet="Simplified formula.",
                    score=3,
                )
            ],
            calculation_result={
                "voltage_drop_percent": 0.8127,
                "threshold_percent": 5.0,
                "is_within_threshold": True,
            },
            limitations=["Demo calculation only."],
            suggested_next_checks=["Confirm catalogue data."],
            tool_trace=["calc_server.calculate_voltage_drop"],
        )
    )

    markdown = report.markdown
    assert "## Retrieved Evidence" in markdown
    assert "## Acceptance Check" in markdown
    assert "not certified electrical design software" in markdown
    assert "voltage_drop_assumptions.md" in markdown
