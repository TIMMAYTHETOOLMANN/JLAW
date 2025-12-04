"""
System Lock Module for JLAW Forensics
=====================================

Provides system configuration locking and state management to:
- Prevent configuration drift
- Ensure consistent analysis outputs
- Lock system in production-ready state
- Verify system integrity on startup

The system can be locked to prevent modification of:
- Analysis thresholds
- Detection parameters
- Output formats
- Violation categories
"""

import hashlib
import json
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class SystemState(Enum):
    """System operational state"""
    UNLOCKED = "unlocked"          # System can be modified
    LOCKED = "locked"              # System is production-locked
    VERIFICATION_FAILED = "verification_failed"  # Lock verification failed


@dataclass
class AnalysisParameters:
    """
    Locked analysis parameters - these cannot be modified when system is locked.
    
    These define the core detection logic and thresholds.
    """
    # Late filing detection
    late_filing_tolerance_days: int = 2  # SEC requires 2 business days for Form 4
    
    # Zero-dollar transaction detection
    zero_dollar_threshold: float = 0.01
    
    # Penalty tiers for late filings (days: penalty amount)
    penalty_tier_1_days: int = 10
    penalty_tier_1_amount: float = 25_000.0
    penalty_tier_2_days: int = 30
    penalty_tier_2_amount: float = 50_000.0
    penalty_tier_3_amount: float = 100_000.0
    
    # Material misstatement keywords
    misstatement_keywords: List[str] = field(default_factory=lambda: [
        'restated', 'restate', 'restating', 'modified retrospective',
        'restatement', 'revised', 'corrected'
    ])
    
    # SOX violation detection
    sox_302_exhibit_patterns: List[str] = field(default_factory=lambda: [
        '31.1', '31.2', 'EX-31.1', 'EX-31.2'
    ])
    
    # Damage estimation defaults
    material_misstatement_damages: float = 15_000_000.0
    sox_302_violation_damages: float = 5_000_000.0
    
    # Confidence thresholds
    min_prosecution_confidence: float = 0.70
    high_confidence_threshold: float = 0.85
    definitive_confidence_threshold: float = 1.0


@dataclass
class OutputConfiguration:
    """
    Locked output configuration - standardized report format.
    """
    # Report formats
    default_output_format: str = "doj_level"
    supported_formats: List[str] = field(default_factory=lambda: [
        "doj_level", "json", "pdf", "all"
    ])
    
    # Report sections
    include_executive_summary: bool = True
    include_detailed_findings: bool = True
    include_evidence_packages: bool = True
    include_damage_calculations: bool = True
    include_statutory_references: bool = True
    
    # Evidence documentation
    evidence_chain_required: bool = True
    chain_of_custody_required: bool = True
    exact_quotes_required: bool = True
    document_locations_required: bool = True


@dataclass
class SystemConfiguration:
    """
    Complete system configuration that gets locked.
    """
    # Version info
    system_version: str = "1.0.0"
    enhancement_protocol_version: str = "9.0"
    
    # Analysis parameters
    analysis: AnalysisParameters = field(default_factory=AnalysisParameters)
    
    # Output configuration
    output: OutputConfiguration = field(default_factory=OutputConfiguration)
    
    # Operational parameters
    max_workers: int = 5
    parallel_processing: bool = True
    save_intermediate_results: bool = True
    
    # SEC compliance
    sec_rate_limit_per_second: float = 10.0
    sec_user_agent_required: bool = True
    
    # Evidence standards
    min_evidence_items: int = 1
    min_reasoning_chain_steps: int = 2


class SystemLock:
    """
    Manages system configuration locking and verification.
    
    When locked, the system configuration cannot be modified.
    All analysis runs will use the same parameters.
    """
    
    DEFAULT_LOCK_FILE = Path("forensic_storage") / "system.lock.json"
    
    def __init__(self, lock_file: Optional[Path] = None):
        self.lock_file = lock_file or self.DEFAULT_LOCK_FILE
        self._state = SystemState.UNLOCKED
        self._config: Optional[SystemConfiguration] = None
        self._signature: Optional[str] = None
    
    @staticmethod
    def _compute_hash(config: SystemConfiguration) -> str:
        """Compute SHA-256 hash of configuration"""
        # Convert to dict and sort for consistent hashing
        config_dict = asdict(config)
        json_str = json.dumps(config_dict, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(json_str.encode('utf-8')).hexdigest()
    
    def get_default_config(self) -> SystemConfiguration:
        """Get default production configuration"""
        return SystemConfiguration()
    
    def lock(self, config: Optional[SystemConfiguration] = None) -> bool:
        """
        Lock the system with the given configuration.
        
        Args:
            config: Configuration to lock. If None, uses default production config.
            
        Returns:
            True if lock succeeded
        """
        if config is None:
            config = self.get_default_config()
        
        self._config = config
        self._signature = self._compute_hash(config)
        self._state = SystemState.LOCKED
        
        # Write lock file
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)
        
        lock_data = {
            "locked_at": datetime.now(timezone.utc).isoformat(),
            "signature": self._signature,
            "config": asdict(config)
        }
        
        self.lock_file.write_text(
            json.dumps(lock_data, indent=2, default=str),
            encoding='utf-8'
        )
        
        return True
    
    def verify(self) -> SystemState:
        """
        Verify system lock integrity.
        
        Returns:
            Current system state
        """
        if not self.lock_file.exists():
            self._state = SystemState.UNLOCKED
            return self._state
        
        try:
            lock_data = json.loads(self.lock_file.read_text(encoding='utf-8'))
            stored_signature = lock_data.get('signature')
            stored_config = lock_data.get('config', {})
            
            # Reconstruct configuration
            analysis_data = stored_config.get('analysis', {})
            output_data = stored_config.get('output', {})
            
            analysis = AnalysisParameters(
                late_filing_tolerance_days=analysis_data.get('late_filing_tolerance_days', 2),
                zero_dollar_threshold=analysis_data.get('zero_dollar_threshold', 0.01),
                penalty_tier_1_days=analysis_data.get('penalty_tier_1_days', 10),
                penalty_tier_1_amount=analysis_data.get('penalty_tier_1_amount', 25000.0),
                penalty_tier_2_days=analysis_data.get('penalty_tier_2_days', 30),
                penalty_tier_2_amount=analysis_data.get('penalty_tier_2_amount', 50000.0),
                penalty_tier_3_amount=analysis_data.get('penalty_tier_3_amount', 100000.0),
                misstatement_keywords=analysis_data.get('misstatement_keywords', []),
                sox_302_exhibit_patterns=analysis_data.get('sox_302_exhibit_patterns', []),
                material_misstatement_damages=analysis_data.get('material_misstatement_damages', 15000000.0),
                sox_302_violation_damages=analysis_data.get('sox_302_violation_damages', 5000000.0),
                min_prosecution_confidence=analysis_data.get('min_prosecution_confidence', 0.70),
                high_confidence_threshold=analysis_data.get('high_confidence_threshold', 0.85),
                definitive_confidence_threshold=analysis_data.get('definitive_confidence_threshold', 1.0),
            )
            
            output = OutputConfiguration(
                default_output_format=output_data.get('default_output_format', 'doj_level'),
                supported_formats=output_data.get('supported_formats', []),
                include_executive_summary=output_data.get('include_executive_summary', True),
                include_detailed_findings=output_data.get('include_detailed_findings', True),
                include_evidence_packages=output_data.get('include_evidence_packages', True),
                include_damage_calculations=output_data.get('include_damage_calculations', True),
                include_statutory_references=output_data.get('include_statutory_references', True),
                evidence_chain_required=output_data.get('evidence_chain_required', True),
                chain_of_custody_required=output_data.get('chain_of_custody_required', True),
                exact_quotes_required=output_data.get('exact_quotes_required', True),
                document_locations_required=output_data.get('document_locations_required', True),
            )
            
            config = SystemConfiguration(
                system_version=stored_config.get('system_version', '1.0.0'),
                enhancement_protocol_version=stored_config.get('enhancement_protocol_version', '9.0'),
                analysis=analysis,
                output=output,
                max_workers=stored_config.get('max_workers', 5),
                parallel_processing=stored_config.get('parallel_processing', True),
                save_intermediate_results=stored_config.get('save_intermediate_results', True),
                sec_rate_limit_per_second=stored_config.get('sec_rate_limit_per_second', 10.0),
                sec_user_agent_required=stored_config.get('sec_user_agent_required', True),
                min_evidence_items=stored_config.get('min_evidence_items', 1),
                min_reasoning_chain_steps=stored_config.get('min_reasoning_chain_steps', 2),
            )
            
            # Verify hash
            computed_signature = self._compute_hash(config)
            
            if computed_signature == stored_signature:
                self._state = SystemState.LOCKED
                self._config = config
                self._signature = stored_signature
            else:
                self._state = SystemState.VERIFICATION_FAILED
                
        except Exception as e:
            self._state = SystemState.VERIFICATION_FAILED
        
        return self._state
    
    def get_config(self) -> Optional[SystemConfiguration]:
        """Get current locked configuration"""
        if self._state == SystemState.UNLOCKED:
            self.verify()
        return self._config
    
    def is_locked(self) -> bool:
        """Check if system is locked"""
        if self._state == SystemState.UNLOCKED:
            self.verify()
        return self._state == SystemState.LOCKED
    
    def unlock(self) -> bool:
        """
        Unlock the system (remove lock file).
        
        Returns:
            True if unlock succeeded
        """
        if self.lock_file.exists():
            self.lock_file.unlink()
        
        self._state = SystemState.UNLOCKED
        self._config = None
        self._signature = None
        return True
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get comprehensive system lock status report"""
        self.verify()
        
        report = {
            "state": self._state.value,
            "lock_file": str(self.lock_file),
            "lock_file_exists": self.lock_file.exists(),
            "signature": self._signature,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if self._config:
            report["config"] = {
                "system_version": self._config.system_version,
                "enhancement_protocol_version": self._config.enhancement_protocol_version,
                "late_filing_tolerance_days": self._config.analysis.late_filing_tolerance_days,
                "zero_dollar_threshold": self._config.analysis.zero_dollar_threshold,
                "default_output_format": self._config.output.default_output_format,
                "evidence_chain_required": self._config.output.evidence_chain_required,
            }
        
        return report
