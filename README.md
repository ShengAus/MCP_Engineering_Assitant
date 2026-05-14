# MCP Engineering Assistant Demo

A Python sample showing multiple MCP servers as tools for an engineering-style LLM agent workflow.

The demo uses simplified electrical engineering calculations to show architecture, not certified design capability. It separates natural-language planning from deterministic backend tools for retrieval, calculation, and report generation.

## What It Demonstrates

- Three separate MCP server modules:
  - document retrieval
  - engineering calculation
  - report generation
- Deterministic tool behavior with Pydantic validation
- A reproducible MCP demo runner
- Source traceability from local engineering notes
- Safety limitations suitable for engineering software discussions

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev]"
```

This project uses `pyproject.toml` for packaging. If editable installation fails, check that the active virtual environment is using a modern pip:

```bash
python -m pip --version
```

## Run The Demo

```bash
python examples/run_mcp_demo.py
```

The demo asks:

> For a 50 m three-phase cable carrying 80 A at 415 V, estimate the voltage drop using the available assumptions, check it against the demo acceptance threshold, and generate a short engineering report.

## Optional LLM Host

The repository also includes a narrow OpenAI-compatible LLM host. It discovers the MCP tools, gives their schemas to the model, executes requested tool calls through the MCP servers, and asks the model for the final answer.

```bash
cp .env.example .env
# edit OPENAI_API_KEY and optionally LLM_MODEL
python examples/run_llm_agent.py
```

This path requires an API key. The deterministic MCP demo remains the guaranteed offline demo.

## Run Tests

```bash
pytest
```

## Safety Note

This project is a demonstration of MCP tool orchestration for engineering-style workflows. It is not certified electrical design software and must not be used for real design decisions without qualified engineering review.
