"""Optional Crawl4AI smoke (experiments only — not used by production scan)."""

from __future__ import annotations

import asyncio
import sys


async def main(url: str) -> int:
    try:
        from crawl4ai import AsyncWebCrawler
    except ImportError:
        print("Install first: pip install crawl4ai && crawl4ai-setup", file=sys.stderr)
        return 1

    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=url)
    markdown = (result.markdown or "")[:500]
    print(markdown or "(empty markdown)")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    raise SystemExit(asyncio.run(main(target)))
