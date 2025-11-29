"""
SEC EDGAR Client (Phase 2)
==========================
CPU-friendly, compliant client with:
- Required User-Agent header with contact (from config)
- Global 10 req/sec rate limiter
- Simple on-disk caching (ETag/Last-Modified when available)

Notes
- Uses SEC's data endpoint for submissions JSON: https://data.sec.gov/submissions/CIK##########.json
- This module is safe to import when offline; network used only when methods are called.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from src.forensics.config_manager import get_config


@dataclass
class CachedResponse:
    url: str
    path: Path
    status: int
    from_cache: bool
    headers: Dict[str, str]


class RateLimiter:
    """Simple sliding-window limiter targeting ~10 req/sec overall.

    This is cooperative: it sleeps when more than N requests have occurred in the past 1 second.
    """

    def __init__(self, rps: int = 10) -> None:
        self.rps = rps
        self._timestamps: List[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            import time
            now = time.monotonic()
            # prune entries older than 1s
            self._timestamps = [t for t in self._timestamps if now - t < 1.0]
            if len(self._timestamps) >= self.rps:
                sleep_time = 1.0 - (now - self._timestamps[0])
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                now = time.monotonic()
                self._timestamps = [t for t in self._timestamps if now - t < 1.0]
            self._timestamps.append(now)


class SecClient:
    def __init__(self, cache_dir: Optional[str] = None, rps: int = 10) -> None:
        cfg = get_config().config
        self.user_agent = cfg.sec.user_agent
        self.rate_limiter = RateLimiter(rps=rps if rps > 0 else cfg.sec.requests_per_second)
        self.cache_dir = Path(cache_dir) if cache_dir else Path("forensic_storage") / "cache" / "edgar"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_key(self, url: str) -> Path:
        h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
        return self.cache_dir / f"{h}.dat"

    def _meta_path(self, data_path: Path) -> Path:
        return data_path.with_suffix(".meta.json")

    async def _get(self, session: aiohttp.ClientSession, url: str, as_text: bool = True) -> CachedResponse:
        await self.rate_limiter.acquire()
        data_path = self._cache_key(url)
        meta_path = self._meta_path(data_path)

        headers = {"User-Agent": self.user_agent}
        # Load ETag/Last-Modified if available
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
                if etag := meta.get("etag"):
                    headers["If-None-Match"] = etag
                if lm := meta.get("last_modified"):
                    headers["If-Modified-Since"] = lm
            except Exception:
                pass

        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 304 and data_path.exists():
                # Not modified; serve cached
                return CachedResponse(url=url, path=data_path, status=304, from_cache=True, headers={})

            content = await (resp.text() if as_text else resp.read())
            # Persist
            mode = "w" if as_text else "wb"
            with open(data_path, mode, encoding="utf-8" if as_text else None) as f:
                f.write(content)

            # Store metadata for caching
            try:
                meta = {
                    "url": url,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "status": resp.status,
                    "etag": resp.headers.get("ETag"),
                    "last_modified": resp.headers.get("Last-Modified"),
                    "content_type": resp.headers.get("Content-Type"),
                }
                meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
            except Exception:
                pass

            return CachedResponse(url=url, path=data_path, status=resp.status, from_cache=False, headers=dict(resp.headers))

    async def _ensure_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession()

    @staticmethod
    def _normalize_cik(cik: str) -> str:
        digits = "".join(ch for ch in cik if ch.isdigit())
        return digits.zfill(10)

    async def get_company_submissions(self, cik: str) -> Dict[str, Any]:
        """Fetch the SEC submissions JSON for a company CIK (cached)."""
        cik10 = self._normalize_cik(cik)
        url = f"https://data.sec.gov/submissions/CIK{cik10}.json"
        async with await self._ensure_session() as session:
            resp = await self._get(session, url, as_text=True)
            data = json.loads(resp.path.read_text(encoding="utf-8"))
            return data

    async def list_filings(self, cik: str, form_types: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Return recent filings filtered by form types.

        form_types example: ["10-K", "10-Q", "8-K", "4"]
        """
        data = await self.get_company_submissions(cik)
        filings = data.get("filings", {}).get("recent", {})
        # Build records
        records: List[Dict[str, Any]] = []
        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accession = filings.get("accessionNumber", [])
        urls = filings.get("primaryDocument", [])
        n = min(len(forms), len(dates), len(accession), len(urls))
        for i in range(n):
            rec = {
                "form": forms[i],
                "filing_date": dates[i],
                "accession": accession[i],
                "primary_document": urls[i],
            }
            if not form_types or rec["form"] in form_types:
                records.append(rec)
            if len(records) >= limit:
                break
        return records

    async def download_primary_document(self, cik: str, accession: str, primary_document: str) -> Path:
        """Download primary document for a filing into cache and return its path."""
        cik10 = self._normalize_cik(cik)
        acc_nodashes = accession.replace("-", "")
        # Construct URL per SEC convention
        # https://www.sec.gov/Archives/edgar/data/{CIK}/{ACCESSION_NO_DASHES}/{PRIMARY_DOCUMENT}
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik10)}/{acc_nodashes}/{primary_document}"
        async with await self._ensure_session() as session:
            resp = await self._get(session, url, as_text=True)
            return resp.path
