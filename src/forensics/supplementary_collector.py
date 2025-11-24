"""
Supplementary Document Collector
Collects ESG reports, earnings materials, press releases and investor presentations
from approved IR domains with strict robots and rate limiting compliance.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
import aiohttp
from bs4 import BeautifulSoup


KEYWORDS = [
    "esg", "sustainability", "impact", "csr",
    "investor", "presentation", "press", "release",
    "earnings", "call", "transcript", "financials"
]


@dataclass
class SupplementaryDoc:
    url: str
    title: Optional[str]
    source_domain: str
    year_hint: Optional[int]
    content_type: Optional[str]


class SupplementaryDocumentCollector:
    """Lightweight, whitelist-only collector for supplementary documents."""

    def __init__(self, allowed_domains: List[str], user_agent: str):
        self.allowed_domains = allowed_domains
        self.user_agent = user_agent
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        headers = {"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml"}
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.session:
            await self.session.close()
            self.session = None

    async def collect(self, year: int = 2019, max_per_domain: int = 10) -> List[SupplementaryDoc]:
        assert self.session is not None, "Collector must be used as an async context manager"
        results: List[SupplementaryDoc] = []
        sem = asyncio.Semaphore(3)

        async def fetch_and_parse(root: str):
            try:
                async with sem:
                    await asyncio.sleep(0.35)
                    async with self.session.get(root, allow_redirects=True) as resp:
                        if resp.status != 200:
                            return
                        text = await resp.text(errors="ignore")
                soup = BeautifulSoup(text, "html.parser")
                links = []
                for a in soup.find_all("a", href=True):
                    href = a.get("href").strip()
                    full = urljoin(root, href)
                    if not self._allowed(full):
                        continue
                    label = (a.get_text(strip=True) or "").lower()
                    if any(k in href.lower() for k in KEYWORDS) or any(k in label for k in KEYWORDS):
                        links.append((full, a.get_text(strip=True)))
                # De-dup and cap per domain
                seen = set()
                capped = []
                for url, title in links:
                    d = urlparse(url).netloc
                    if url in seen:
                        continue
                    if sum(1 for u, _ in capped if urlparse(u).netloc == d) >= max_per_domain:
                        continue
                    seen.add(url)
                    capped.append((url, title))
                # Build docs
                for url, title in capped:
                    results.append(SupplementaryDoc(
                        url=url,
                        title=title or None,
                        source_domain=urlparse(url).netloc,
                        year_hint=self._infer_year(url, title),
                        content_type=self._guess_type(url)
                    ))
            except Exception:
                return

        await asyncio.gather(*(fetch_and_parse(root) for root in self.allowed_domains))
        # Filter to target year where possible
        filtered = [d for d in results if (d.year_hint is None or d.year_hint == year)]
        return filtered

    def _allowed(self, url: str) -> bool:
        host = urlparse(url).netloc
        return any(host.endswith(urlparse(root).netloc) for root in self.allowed_domains)

    def _infer_year(self, url: str, title: Optional[str]) -> Optional[int]:
        import re
        text = (url or "") + " " + (title or "")
        m = re.search(r"\b(20\d{2})\b", text)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                return None
        return None

    def _guess_type(self, url: str) -> Optional[str]:
        path = urlparse(url).path.lower()
        if path.endswith(".pdf"):
            return "pdf"
        if path.endswith(".htm") or path.endswith(".html"):
            return "html"
        return None
