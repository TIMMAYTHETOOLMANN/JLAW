"""
Configuration Lock Utility
Ensures backend configuration and performance-critical parameters remain stable
across repeated runs. Produces a signed snapshot that is verified on startup.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigLock:
    """
    Creates and verifies a locked configuration snapshot to stabilize
    backend behavior (UA, strict gating, rate limits, retry policy,
    whitelists, and analysis modes).
    """

    DEFAULT_LOCK_PATH = Path("forensic_storage") / "config.lock.json"

    @classmethod
    def _hash(cls, obj: Dict[str, Any]) -> str:
        payload = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @classmethod
    def build_snapshot(
        cls,
        system_config: Any,
        *,
        sec_user_agent: Optional[str] = None,
        statute_strict_mode: Optional[bool] = None,
        sec_rate_limit: Optional[float] = None,
        retry_policy: Optional[Dict[str, Any]] = None,
        supplementary_whitelist: Optional[list] = None,
    ) -> Dict[str, Any]:
        """Normalize and assemble a minimal, portable snapshot for locking."""
        snapshot: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "system": {
                "storage_provider": getattr(system_config, "storage_provider", None),
                "max_workers": getattr(system_config, "max_workers", None),
            },
            "sec": {
                "user_agent": sec_user_agent,
                "rate_limit": sec_rate_limit,
            },
            "statute_mapper": {
                "strict_mode": statute_strict_mode,
            },
            "retry_policy": retry_policy or {},
            "supplementary_whitelist": supplementary_whitelist or [],
        }
        # Compute signature over stable fields only (exclude volatile timestamp)
        stable = {
            "system": snapshot["system"],
            "sec": snapshot["sec"],
            "statute_mapper": snapshot["statute_mapper"],
            "retry_policy": snapshot["retry_policy"],
            "supplementary_whitelist": snapshot["supplementary_whitelist"],
        }
        snapshot["signature"] = cls._hash(stable)
        return snapshot

    @classmethod
    def verify_or_create_lock(
        cls,
        snapshot: Dict[str, Any],
        lock_path: Optional[Path] = None,
        *,
        allow_create: bool = True,
    ) -> bool:
        """Verify existing lock file matches the provided snapshot.

        If no lock exists and allow_create=True, create it from the snapshot.
        Returns True if verified/created successfully, False if mismatch.
        """
        lock_path = lock_path or cls.DEFAULT_LOCK_PATH
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        # Recompute expected signature from stable fields to avoid timestamp mismatch
        stable = {
            "system": snapshot.get("system"),
            "sec": snapshot.get("sec"),
            "statute_mapper": snapshot.get("statute_mapper"),
            "retry_policy": snapshot.get("retry_policy"),
            "supplementary_whitelist": snapshot.get("supplementary_whitelist"),
        }
        expected_sig = snapshot.get("signature") or cls._hash(stable)

        if lock_path.exists():
            try:
                on_disk = json.loads(lock_path.read_text(encoding="utf-8"))
                disk_sig = on_disk.get("signature")
                # Compute stable signature from on-disk snapshot for migration support
                disk_stable = {
                    "system": on_disk.get("system"),
                    "sec": on_disk.get("sec"),
                    "statute_mapper": on_disk.get("statute_mapper"),
                    "retry_policy": on_disk.get("retry_policy"),
                    "supplementary_whitelist": on_disk.get("supplementary_whitelist"),
                }
                disk_stable_sig = cls._hash(disk_stable)

                if disk_sig == expected_sig or disk_stable_sig == expected_sig:
                    # If signatures match via stable comparison but stored signature differs, rewrite file with canonical signature
                    if disk_sig != expected_sig:
                        try:
                            on_disk["signature"] = expected_sig
                            lock_path.write_text(json.dumps(on_disk, indent=2), encoding="utf-8")
                        except Exception:
                            pass
                    return True
                return False
            except Exception:
                return False
        else:
            if allow_create:
                lock_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
                return True
            return False
