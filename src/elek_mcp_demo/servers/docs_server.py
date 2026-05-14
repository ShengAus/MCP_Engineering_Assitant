from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from elek_mcp_demo.domain.docs import get_doc_section as get_section
from elek_mcp_demo.domain.docs import search_docs as search


mcp = FastMCP("engineering-docs")


@mcp.tool()
def search_docs(query: str, limit: int = 3) -> list[dict]:
    """Search local engineering notes and return sourceable snippets."""
    return [item.model_dump() for item in search(query=query, limit=limit)]


@mcp.tool()
def get_doc_section(section_id: str) -> dict:
    """Return a full engineering note section by section ID."""
    return get_section(section_id).model_dump()


if __name__ == "__main__":
    mcp.run()
