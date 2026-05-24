import httpx
from kyros.tools.base import Tool


class WebFetchTool(Tool):
    name = "web_fetch"
    description = "Fetch content from a URL"

    async def execute(self, url: str, format: str = "markdown", **kwargs) -> dict:
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                content = resp.text
                return {"success": True, "content": content, "url": url, "status_code": resp.status_code, "size": len(content)}
        except Exception as e:
            return {"success": False, "error": str(e), "url": url}


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web using DuckDuckGo"

    async def execute(self, query: str, num_results: int = 5, **kwargs) -> dict:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get("https://duckduckgo.com/html/", params={"q": query})
                resp.raise_for_status()
                return {"success": True, "query": query, "results": [{"title": "DuckDuckGo results", "snippet": resp.text[:500]}], "count": 1}
        except Exception as e:
            return {"success": False, "error": str(e), "query": query}
