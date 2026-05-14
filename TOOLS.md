# MCP Tools

## Document Retrieval Server

### `search_docs`

Search local engineering notes.

Inputs:

- `query`: search text
- `limit`: maximum number of sections to return

Returns section IDs, titles, filenames, snippets, and simple relevance scores.

### `get_doc_section`

Fetch a complete source section by section ID.

## Engineering Calculation Server

### `calculate_voltage_drop`

Estimate simplified three-phase voltage drop.

Formula:

```text
V_drop = sqrt(3) * I * L_km * (R cos(phi) + X sin(phi))
V_drop_percent = V_drop / V_line * 100
```

This is a demonstration calculation only.

## Report Generation Server

### `generate_engineering_report`

Generate a deterministic Markdown report from a user question, inputs, evidence, calculation results, limitations, and tool trace.

## LLM Tool Names

The optional LLM host prefixes MCP tool names by server so tools remain unambiguous:

- `docs_search_docs`
- `docs_get_doc_section`
- `calc_calculate_voltage_drop`
- `report_generate_engineering_report`
