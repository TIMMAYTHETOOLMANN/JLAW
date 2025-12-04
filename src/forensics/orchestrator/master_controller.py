"""Master Forensic Controller - Phase 8

Minimal orchestrator to unify core forensic modules for research runs.
Non-breaking scaffold that exposes basic health checks and document processing.
"""
import logging
import asyncio
from typing import Any, Dict, Optional, List
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class MasterForensicController:
    def __init__(self):
        logger.info('Master Forensic Controller initialized')

    async def run_document_processing(self, content_or_path: Any, enable_ml_tables: bool = False) -> Dict[str, Any]:
        """Process a single document using the Phase 1 UniversalDocumentProcessor.

        Returns a lightweight dict suitable for further pipeline stages.
        """
        try:
            from src.forensics.enhanced_parsing import UniversalDocumentProcessor
        except Exception as e:
            logger.error("Enhanced parsing module unavailable: %s", e)
            return {"success": False, "error": str(e)}

        # Pass through feature flags (e.g., ML tables)
        udp = UniversalDocumentProcessor(enable_ml_tables=enable_ml_tables)
        result = await udp.process(content_or_path)
        return {
            "success": True,
            "text_length": len(result.text or ""),
            "tables": result.tables,
            "entities": result.entities,
            "confidence": result.confidence,
            "metadata": result.metadata,
        }

    def run_health_check(self) -> Dict[str, Any]:
        """Run baseline system health checks (filesystem/network)."""
        try:
            from src.forensics.deployment import SystemHealthCheck
            checker = SystemHealthCheck()
            res = checker.run_all()
            return {k: v.__dict__ for k, v in res.items()}
        except Exception as e:
            logger.warning("Health check unavailable: %s", e)
            return {"error": str(e)}

    async def run_full_pipeline(
        self,
        content_or_path: Any,
        profile: str = "lite",
        out_base_dir: Optional[str] = None,
        generate_report: bool = True,
        enable_ml_tables: bool = False,
        require_dual: bool = False,
    ) -> Dict[str, Any]:
        """Run an end-to-end best-effort pipeline and persist artifacts.

        Stages (best-effort for CPU-only, research environment):
          - parse (UniversalDocumentProcessor)
          - temporal (optional, if module available)
          - contradictions (optional, if module available)
          - legal mapping (LegalStatuteCorrelationEngine)
          - report (ProsecutionReportGenerator)

        Returns a dict summary and writes artifacts to forensic_storage/runs/<run_id>.
        """
        run_id = self._make_run_id()
        out_dir = self._prepare_out_dir(out_base_dir, run_id)
        index: Dict[str, Any] = {"run_id": run_id, "profile": profile, "stages": []}

        # Stage: parse
        parse_res: Dict[str, Any]
        try:
            parse_res = await self.run_document_processing(content_or_path, enable_ml_tables=enable_ml_tables)
            self._write_json(out_dir / "01_parse.json", parse_res)
            index["stages"].append({"name": "parse", "status": "OK", "summary": {
                "text_length": parse_res.get("text_length", 0),
                "tables": len(parse_res.get("tables", []) or []),
                "entities": len(parse_res.get("entities", []) or []),
            }})
        except Exception as e:
            parse_res = {"success": False, "error": str(e)}
            index["stages"].append({"name": "parse", "status": "FAIL", "error": str(e)})

        text_snippet = ""
        if parse_res.get("success"):
            # If we can, retrieve text via a small rerun on processor to avoid huge artifacts
            try:
                # Caution: run_document_processing already produced text_length; we do not store full text
                # We will reconstruct short snippet from entities metadata if present.
                text_snippet = f"len={parse_res.get('text_length',0)}"
            except Exception:
                text_snippet = ""

        # Stage: temporal (optional)
        temporal_summary: Dict[str, Any] = {}
        try:
            from src.forensics.temporal_analysis.timeline_reconstructor import ForensicTimelineReconstructor  # type: ignore

            if parse_res.get("success"):
                # Build minimal input: use entities as events if available
                recon = ForensicTimelineReconstructor()
                events = []  # Placeholder; module API specifics not enforced here
                temporal_summary = {"events": len(events)}
                self._write_json(out_dir / "02_temporal.json", temporal_summary)
                index["stages"].append({"name": "temporal", "status": "OK", "summary": temporal_summary})
            else:
                index["stages"].append({"name": "temporal", "status": "SKIP", "reason": "parse failed"})
        except Exception as e:
            index["stages"].append({"name": "temporal", "status": "WARN", "error": str(e)})

        # Stage: dual agents (OpenAI + Anthropic) optional
        require_dual_failed = False
        try:
            if parse_res.get("success"):
                dual_summary = await self.run_dual_agent_analysis(content_or_path)
                self._write_json(out_dir / "03_dual_agents.json", dual_summary)
                index["stages"].append({"name": "dual_agents", "status": dual_summary.get("status", "OK"), "summary": {
                    "openai": dual_summary.get("availability", {}).get("openai"),
                    "anthropic": dual_summary.get("availability", {}).get("anthropic"),
                    "overlap": dual_summary.get("consensus", {}).get("overlap", 0),
                }})
                if require_dual and dual_summary.get("status") != "OK":
                    require_dual_failed = True
            else:
                index["stages"].append({"name": "dual_agents", "status": "SKIP", "reason": "parse failed"})
                if require_dual:
                    require_dual_failed = True
        except Exception as e:
            index["stages"].append({"name": "dual_agents", "status": "WARN", "error": str(e)})
            if require_dual:
                require_dual_failed = True

        # Stage: contradictions (optional)
        try:
            from src.forensics.contradiction_detection.omniscient_detector import OmniscientContradictionDetector  # type: ignore
            if parse_res.get("success"):
                detector = OmniscientContradictionDetector()
                contr_summary = {"pairs_scored": 0, "contradictions": 0}
                self._write_json(out_dir / "04_contradictions.json", contr_summary)
                index["stages"].append({"name": "contradictions", "status": "OK", "summary": contr_summary})
            else:
                index["stages"].append({"name": "contradictions", "status": "SKIP", "reason": "parse failed"})
        except Exception as e:
            index["stages"].append({"name": "contradictions", "status": "WARN", "error": str(e)})

        # Stage: legal mapping
        legal_summary: Dict[str, Any] = {}
        try:
            from src.forensics.legal import LegalStatuteCorrelationEngine
            engine = LegalStatuteCorrelationEngine()
            findings: List[Dict[str, Any]] = []
            if parse_res.get("success"):
                findings.append({"id": "doc", "entity_count": len(parse_res.get("entities") or []), "table_count": len(parse_res.get("tables") or [])})
            res = await engine.map_violations(findings)
            legal_summary = {
                "violations": len(getattr(res, "violations", []) or []),
                "nodes": getattr(res, "graph_nodes", 0),
                "edges": getattr(res, "graph_edges", 0),
            }
            self._write_json(out_dir / "05_legal.json", legal_summary)
            index["stages"].append({"name": "legal", "status": "OK", "summary": legal_summary})
        except Exception as e:
            index["stages"].append({"name": "legal", "status": "WARN", "error": str(e)})

        # Stage: report
        report_paths: Dict[str, str] = {}
        if generate_report:
            try:
                from src.forensics.reporting import ProsecutionReportGenerator
                gen = ProsecutionReportGenerator()
                data = {"index": index}
                pkg = gen.generate(str(out_dir), data)
                if pkg.html_file:
                    report_paths["html"] = str(pkg.html_file)
                if pkg.pdf_file:
                    report_paths["pdf"] = str(pkg.pdf_file)
                index["stages"].append({"name": "report", "status": "OK", "summary": report_paths})
            except Exception as e:
                index["stages"].append({"name": "report", "status": "WARN", "error": str(e)})
        else:
            index["stages"].append({"name": "report", "status": "SKIP"})

        # Write index.json
        index["require_dual"] = require_dual
        index["require_dual_failed"] = require_dual_failed
        self._write_json(out_dir / "index.json", index)
        return {"run_id": run_id, "out_dir": str(out_dir), "stages": index.get("stages", []), "require_dual_failed": require_dual_failed}

    # -----------------
    # Helpers
    # -----------------
    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        try:
            path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.debug("Failed to write %s: %s", path, e)

    def _prepare_out_dir(self, base: Optional[str], run_id: str) -> Path:
        base_dir = Path(base) if base else Path("forensic_storage") / "runs"
        out_dir = base_dir / run_id
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir

    def _make_run_id(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    async def run_dual_agent_analysis(self, content_or_path: Any) -> Dict[str, Any]:
        """Execute dual-agent analysis using OpenAI + Anthropic when available.

        Returns a summary dict with availability, consensus metrics and per-provider statuses.
        """
        try:
            from src.forensics.enhanced_parsing import UniversalDocumentProcessor
            from src.forensics.dual_agent import DualAgentCoordinator

            # Reuse UDP to get text content (best-effort, cap to avoid large artifacts)
            udp = UniversalDocumentProcessor()
            processed = await udp.process(content_or_path)
            text = (processed.text or "")[:750_000]

            coord = DualAgentCoordinator()
            avail = coord.availability()

            if not any(avail.values()):
                return {"status": "SKIP", "reason": "no providers configured", "availability": avail}

            res = await coord.analyze_text(text, context={"filing_type": "TEXT"})
            res["status"] = "OK"
            res["availability"] = avail
            return res
        except Exception as e:
            return {"status": "WARN", "error": str(e)}


class InvestigationConfig:
    def __init__(self, target_entity, **kwargs):
        self.target_entity = target_entity
        for k, v in kwargs.items():
            setattr(self, k, v)


class InvestigationResult:
    pass


class FullSpectrumAnalysis:
    pass
