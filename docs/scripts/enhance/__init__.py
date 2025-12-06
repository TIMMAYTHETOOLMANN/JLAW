#!/usr/bin/env python3
"""
JLAW Financial Forensics Subpackage
═══════════════════════════════════════════════════════════════════════════════

Provides advanced financial flow tracing and gift transaction analysis
for SEC Form 4 forensic investigations. 

Components:
- FinancialFlowTracer: Core flow tracing engine
- GiftTransaction: Gift transaction data structure
- FinancialFlowChain: Complete traced flow chain
- ComplianceFramework: Regulatory compliance mapping
- FlowTracerNITSAdapter: NITS core integration

Author: JLAW Forensic Analysis System
Version: 2.0.0
═══════════════════════════════════════════════════════════════════════════════
"""

__version__ = "2.0.0"
__author__ = "JLAW Forensic Analysis System"

from .financial_flow_tracer import (
    # Core Classes
    FinancialFlowTracer,
    SECDataRetriever,
    
    # Data Structures
    GiftTransaction,
    FlowEvent,
    FinancialFlowChain,
    ComplianceViolation,
    
    # Enums
    FlowEventType,
    ViolationSeverity,
    
    # Framework
    ComplianceFramework,
    TracerConfig,
    
    # NITS Integration
    FlowTracerNITSAdapter,
    
    # Entry Point
    run_financial_flow_tracer
)

__all__ = [
    # Core
    "FinancialFlowTracer",
    "SECDataRetriever",
    
    # Data Structures
    "GiftTransaction",
    "FlowEvent", 
    "FinancialFlowChain",
    "ComplianceViolation",
    
    # Enums
    "FlowEventType",
    "ViolationSeverity",
    
    # Framework
    "ComplianceFramework",
    "TracerConfig",
    
    # Integration
    "FlowTracerNITSAdapter",
    
    # Entry Point
    "run_financial_flow_tracer"
]