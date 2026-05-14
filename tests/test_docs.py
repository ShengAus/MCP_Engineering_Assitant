from elek_mcp_demo.domain.docs import get_doc_section, search_docs


def test_search_docs_returns_source_metadata() -> None:
    results = search_docs("voltage drop acceptance threshold", limit=2)

    assert results
    assert results[0].source_file.endswith(".md")
    assert results[0].section_id
    assert results[0].snippet


def test_get_doc_section_returns_content() -> None:
    section = get_doc_section("voltage_drop_assumptions:demo-voltage-drop-formula")

    assert section.source_file == "voltage_drop_assumptions.md"
    assert "simplified balanced three-phase formula" in section.content
