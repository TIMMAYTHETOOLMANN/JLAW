"""
Strict Execution Configuration
================================

Configurable thresholds and settings for strict forensic execution mode.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class AnalysisThresholds:
    """Thresholds for forensic analysis quality gates."""
    
    # Phase 2: Data Collection
    min_filings_total: int = 1
    min_filings_per_type: Dict[str, int] = field(default_factory=lambda: {
        "10-K": 1,      # Annual report required
        "10-Q": 3,      # At least 3 quarters
        "DEF 14A": 1,   # Proxy statement required
        "4": 10,        # Form 4 insider trades
        "8-K": 5,       # Material events
    })
    
    # Phase 3: Document Parsing
    min_documents_parsed: int = 1
    min_chunks_indexed: int = 10
    
    # Phase 4: Node Analysis
    min_nodes_successful: int = 12  # out of 15
    min_node_success_rate: float = 0.80  # 80% success rate
    
    # Phase 5: Pattern Detection
    min_patterns_executed: int = 20  # out of 23
    
    # Phase 8: Evidence Chain
    require_evidence_chain: bool = True
    require_dual_agent_validation: bool = False  # Optional in default config
    
    # Global settings
    halt_on_critical_failure: bool = True
    preserve_partial_results: bool = True
    generate_abort_report: bool = True


@dataclass
class StrictExecutionConfig:
    """Complete strict execution configuration."""
    
    # Enable strict mode
    strict_mode: bool = False
    
    # Thresholds
    thresholds: AnalysisThresholds = field(default_factory=AnalysisThresholds)
    
    # Exit codes
    exit_code_configuration_failure: int = 1
    exit_code_data_collection_failure: int = 2
    exit_code_document_parsing_failure: int = 3
    exit_code_node_execution_failure: int = 4
    exit_code_pattern_detection_failure: int = 5
    exit_code_evidence_chain_failure: int = 6
    exit_code_dossier_generation_failure: int = 7
    
    # Remediation guidance
    remediation_messages: Dict[int, str] = field(default_factory=lambda: {
        1: "Configuration failed. Check: SEC API credentials, module dependencies, API connectivity.",
        2: "Data collection failed. Check: CIK number validity, date range, SEC EDGAR access, rate limiting.",
        3: "Document parsing failed. Check: Filing accessibility, parser dependencies, document formats.",
        4: "Node execution below threshold. Check: Data quality, node dependencies, analysis parameters.",
        5: "Pattern detection failed. Check: Detection module configuration, input data completeness.",
        6: "Evidence chain integrity failure. Check: Hash computation, custody logging, data preservation.",
        7: "Dossier generation failed. Check: Report generator dependencies, output directory permissions.",
    })
    
    def get_remediation_message(self, exit_code: int) -> str:
        """Get remediation guidance for an exit code."""
        return self.remediation_messages.get(exit_code, "Unknown failure. Check logs for details.")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "strict_mode": self.strict_mode,
            "thresholds": {
                "min_filings_total": self.thresholds.min_filings_total,
                "min_filings_per_type": self.thresholds.min_filings_per_type,
                "min_documents_parsed": self.thresholds.min_documents_parsed,
                "min_chunks_indexed": self.thresholds.min_chunks_indexed,
                "min_nodes_successful": self.thresholds.min_nodes_successful,
                "min_node_success_rate": self.thresholds.min_node_success_rate,
                "min_patterns_executed": self.thresholds.min_patterns_executed,
                "require_evidence_chain": self.thresholds.require_evidence_chain,
                "require_dual_agent_validation": self.thresholds.require_dual_agent_validation,
            },
            "halt_on_critical_failure": self.thresholds.halt_on_critical_failure,
            "preserve_partial_results": self.thresholds.preserve_partial_results,
        }


# Default configurations
DEFAULT_CONFIG = StrictExecutionConfig(strict_mode=False)

STRICT_CONFIG = StrictExecutionConfig(
    strict_mode=True,
    thresholds=AnalysisThresholds(
        min_filings_total=5,
        min_nodes_successful=12,
        min_patterns_executed=20,
        require_evidence_chain=True,
    )
)

# Investigation-specific configs
DOJ_INVESTIGATION_CONFIG = StrictExecutionConfig(
    strict_mode=True,
    thresholds=AnalysisThresholds(
        min_filings_total=10,
        min_filings_per_type={
            "10-K": 2,
            "10-Q": 4,
            "DEF 14A": 2,
            "4": 20,
            "8-K": 10,
        },
        min_nodes_successful=14,
        min_node_success_rate=0.90,
        min_patterns_executed=22,
        require_evidence_chain=True,
        require_dual_agent_validation=True,
    )
)

SEC_REFERRAL_CONFIG = StrictExecutionConfig(
    strict_mode=True,
    thresholds=AnalysisThresholds(
        min_filings_total=5,
        min_nodes_successful=12,
        min_patterns_executed=20,
        require_evidence_chain=True,
        require_dual_agent_validation=False,
    )
)


def load_config(config_name: Optional[str] = None) -> StrictExecutionConfig:
    """
    Load a configuration by name.
    
    Args:
        config_name: Name of config ('default', 'strict', 'doj', 'sec')
        
    Returns:
        StrictExecutionConfig instance
    """
    configs = {
        "default": DEFAULT_CONFIG,
        "strict": STRICT_CONFIG,
        "doj": DOJ_INVESTIGATION_CONFIG,
        "sec": SEC_REFERRAL_CONFIG,
    }
    
    return configs.get(config_name or "default", DEFAULT_CONFIG)
