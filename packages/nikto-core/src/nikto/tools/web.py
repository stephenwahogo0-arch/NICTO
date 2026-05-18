import asyncio
from typing import Optional

from nikto.tools.base import Tool


async def tool_web_fetch(url: str, format: Optional[str] = "markdown") -> str:
    try:
        import httpx
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            resp.raise_for_status()
            content = resp.text

        if format == "text":
            import re
            content = re.sub(r'<[^>]+>', '', content)
            content = re.sub(r'\s+', ' ', content).strip()

        if len(content) > 50000:
            content = content[:50000] + "\n... (truncated at 50K chars)"

        return content

    except Exception as e:
        return f"Error fetching URL: {str(e)}"


async def tool_web_search(query: str, num_results: int = 8) -> str:
    try:
        import httpx
        url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()

        import re
        results = []
        for match in re.finditer(
            r'<a rel="nofollow" class="result__a" href="([^"]+)".*?>(.*?)</a>.*?'
            r'<a class="result__snippet"[^>]*>(.*?)</a>',
            resp.text, re.DOTALL
        ):
            href = match.group(1)
            title = re.sub(r'<[^>]+>', '', match.group(2)).strip()
            snippet = re.sub(r'<[^>]+>', '', match.group(3)).strip()
            results.append(f"{title}\n  URL: {href}\n  {snippet}")

        if not results:
            return "No search results found."

        return "\n\n".join(results[:num_results])

    except Exception as e:
        return f"Error searching: {str(e)}"


WebFetchTool = Tool(
    name="web_fetch",
    description="Fetch and extract content from a URL. Returns the page content as markdown or text.",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
            "format": {"type": "string", "enum": ["markdown", "text"], "description": "Output format"},
        },
        "required": ["url"],
    },
    async_function=tool_web_fetch,
)

WebSearchTool = Tool(
    name="web_search",
    description="Search the web for current information. Returns ranked results with titles and snippets.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "num_results": {"type": "integer", "description": "Number of results (1-20)"},
        },
        "required": ["query"],
    },
    async_function=tool_web_search,
)
