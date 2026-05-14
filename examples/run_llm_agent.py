from __future__ import annotations

import argparse
import asyncio
import os
import sys
from contextlib import AsyncExitStack
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from elek_mcp_demo.client.llm_host import run_llm_tool_loop
from elek_mcp_demo.client.mcp_tools import McpToolClient
from elek_mcp_demo.client.openai_compatible import (
    LlmSettings,
    OpenAICompatibleChatClient,
)


DEFAULT_QUESTION = (
    "For a 50 m three-phase cable carrying 80 A at 415 V, estimate the "
    "voltage drop using the available assumptions, check it against the "
    "demo acceptance threshold, and generate a short engineering report."
)
OUTPUT_PATH = PROJECT_ROOT / "examples" / "outputs" / "llm_agent_report.md"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Run the optional LLM MCP host demo.")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    parser.add_argument(
        "--output",
        default=str(OUTPUT_PATH),
        help="Markdown output path for the LLM-host response.",
    )
    parser.add_argument(
        "--trace",
        action="store_true",
        help="Print the LLM tool-call trace after the response.",
    )
    args = parser.parse_args()

    load_dotenv_file(PROJECT_ROOT / ".env")

    try:
        settings = LlmSettings.from_env()
    except RuntimeError as exc:
        print(exc)
        print("\nExample:")
        print("  cp .env.example .env")
        print("  # edit OPENAI_API_KEY and optionally LLM_MODEL")
        print("  .venv/bin/python examples/run_llm_agent.py")
        return

    llm = OpenAICompatibleChatClient(settings)

    async with AsyncExitStack() as stack:
        clients = {
            "docs": await stack.enter_async_context(
                McpToolClient("elek_mcp_demo.servers.docs_server", PROJECT_ROOT)
            ),
            "calc": await stack.enter_async_context(
                McpToolClient("elek_mcp_demo.servers.calc_server", PROJECT_ROOT)
            ),
            "report": await stack.enter_async_context(
                McpToolClient("elek_mcp_demo.servers.report_server", PROJECT_ROOT)
            ),
        }
        trace: list[str] = []
        answer = await run_llm_tool_loop(
            llm=llm,
            question=args.question,
            clients=clients,
            trace=trace,
        )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(answer, encoding="utf-8")
    print(answer)
    if args.trace:
        print("\nTool-call trace:")
        for item in trace:
            print(f"- {item}")
    print(f"\nSaved LLM-host response to {output_path}")


def load_dotenv_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


if __name__ == "__main__":
    asyncio.run(main())
