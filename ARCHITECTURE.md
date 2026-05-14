# Architecture

```text
User Query
   |
   v
Deterministic MCP Orchestrator
   |
   v
Multiple MCP Servers
   |-- Document Retrieval Server
   |-- Engineering Calculation Server
   |-- Report Generation Server
   |
   v
Structured Engineering Report
```

The LLM-agent-ready design principle is:

> The host interprets intent and chooses tools, while deterministic MCP tools handle retrieval, calculations, and structured reporting.

For the first demo, the host is deterministic so the workflow is reproducible. An optional LLM host can connect to the same MCP servers.

## Host Modes

### Deterministic MCP Orchestrator

`examples/run_mcp_demo.py` launches the three MCP servers and calls their tools in a fixed sequence. This is the main reliable demo path.

### Optional LLM Host

`examples/run_llm_agent.py` launches the same MCP servers, exposes their tool schemas to an OpenAI-compatible chat model, executes model-requested tool calls through MCP, and returns the final answer.

The LLM host is intentionally narrow. It should use tools for retrieval, calculation, and reporting, and it should not invent standards or perform safety-critical calculations itself.

## Evaluation Methodology

`evals/llm_eval.py` is an offline evaluation harness for the optional LLM host. It uses scripted model responses and in-process tool adapters so the runtime controls can be tested without an API key.

The current eval set covers:

- retrieval quality for source assumptions and safety limitations
- unsupported-answer refusal by checking that host-controlled report assembly removes invented compliance claims
- tool-call correctness for the expected retrieval, calculation, and report-generation sequence
- prompt regression checks for required safety and tool-use instructions

These evals complement unit tests by checking agent behaviour at the orchestration boundary, where prompt instructions, tool calls, evidence, and deterministic runtime controls meet.

## Server Boundaries

- `docs_server`: searches and retrieves local Markdown engineering notes.
- `calc_server`: exposes validated, deterministic engineering calculations.
- `report_server`: creates repeatable Markdown reports from structured inputs.

The servers do not call each other. The host/client coordinates the workflow.

## Deployment Extension

The calculation logic lives in a transport-independent domain module. This allows it to be exposed through MCP locally and later wrapped as an AWS Lambda/API Gateway function or hosted service.
