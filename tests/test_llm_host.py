from elek_mcp_demo.client.llm_host import complete_report_arguments, sanitize_tool_name
from elek_mcp_demo.client.openai_compatible import LlmSettings


def test_sanitize_tool_name_keeps_openai_compatible_characters() -> None:
    assert sanitize_tool_name("docs search.docs!") == "docs_search_docs_"


def test_llm_settings_from_env(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://example.test/v1/")
    monkeypatch.setenv("LLM_MODEL", "test-model")

    settings = LlmSettings.from_env()

    assert settings.api_key == "test-key"
    assert settings.base_url == "https://example.test/v1"
    assert settings.model == "test-model"


def test_complete_report_arguments_uses_host_controlled_report_fields() -> None:
    completed = complete_report_arguments(
        arguments={
            "title": "LLM invented title",
            "inputs": {"current_a": 1},
            "assumptions": ["LLM assumption"],
            "limitations": ["LLM limitation"],
            "suggested_next_checks": ["LLM next check"],
            "tool_trace": ["LLM trace"],
        },
        question="Question from the user",
        latest_inputs={"current_a": 80},
        latest_calculation_result={
            "voltage_drop_v": 3.3778,
            "inputs": {
                "current_a": 80.0,
                "length_m": 50.0,
                "line_voltage_v": 415.0,
                "resistance_ohm_per_km": 0.524,
                "reactance_ohm_per_km": 0.08,
                "power_factor": 0.85,
                "threshold_percent": 5.0,
            },
        },
        latest_evidence=[],
        executed_mcp_tools=[
            "docs_server.search_docs",
            "docs_server.get_doc_section",
            "calc_server.calculate_voltage_drop",
            "report_server.generate_engineering_report",
        ],
    )

    assert completed["title"] == "Voltage Drop Demo Report"
    assert completed["user_question"] == "Question from the user"
    assert completed["inputs"]["current_a"] == 80.0
    assert completed["assumptions"] == [
        "Balanced three-phase load.",
        "Cable impedance values are mock demo assumptions.",
        "The acceptance threshold is a demo threshold, not a compliance claim.",
        "Formula source: voltage_drop_assumptions.md / voltage_drop_assumptions:demo-voltage-drop-formula.",
    ]
    assert completed["limitations"] == [
        "No cable derating, thermal modelling, protection coordination, or standards compliance check is performed.",
        "The mock documentation is included for MCP orchestration demonstration only.",
    ]
    assert completed["tool_trace"] == [
        "docs_server.search_docs",
        "docs_server.get_doc_section",
        "calc_server.calculate_voltage_drop",
        "report_server.generate_engineering_report",
    ]
