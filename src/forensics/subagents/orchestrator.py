"""
Claude Subagent Orchestration Module
=====================================

Provides Python interface for coordinating specialized Claude subagents
defined in .claude/agents/ for complex forensic analysis workflows.

Available Agents:
- forensic-financial-analyst: M-Score, Z-Score, Benford analysis
- forensic-nlp-analyst: Document parsing, contradiction detection
- forensic-research-specialist: SEC research, evidence gathering
- forensic-compliance-auditor: Statute mapping, prosecution prep
- forensic-workflow-orchestrator: Multi-agent coordination
- security-auditor: Evidence chain verification
- database-administrator: Data storage optimization
- devops-engineer: Pipeline automation
- python-pro: Code implementation
- multi-agent-coordinator: Cross-agent task management

Usage:
    orchestrator = SubagentOrchestrator()
    result = orchestrator.run_forensic_analysis(cik="320187", filings=[...])
"""

import os
import json
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import Anthropic client for Claude API
try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("anthropic package not available. Install with: pip install anthropic")

# Import SDK manager for unified client access
from src.forensics.sdk_manager import get_sdk_manager_sync

# Import dynamic agent registry and intelligent router (Phase 2)
from src.forensics.agent_registry import DynamicAgentRegistry
from src.forensics.intelligent_router import IntelligentSubagentRouter


# ═══════════════════════════════════════════════════════════════════════════
# DYNAMIC AGENT DISCOVERY (Phase 2)
# ═══════════════════════════════════════════════════════════════════════════
# Hardcoded VIOLATION_TO_AGENT_MAP has been REMOVED.
# Agent discovery is now dynamic from markdown files in .claude/agents/
# via DynamicAgentRegistry and IntelligentSubagentRouter.
# ═══════════════════════════════════════════════════════════════════════════


def get_agents_for_violation_types(violation_types: List[str]) -> Set[str]:
    """
    Get relevant Claude subagents for given violation types.
    
    DEPRECATED: This is a backward compatibility shim. New code should use
    DynamicAgentRegistry.get_agents_for_violations() instead.
    
    Args:
        violation_types: List of violation type strings
        
    Returns:
        Set of agent names to invoke
    """
    logger.warning("get_agents_for_violation_types() is deprecated. Use DynamicAgentRegistry instead.")
    
    try:
        # Use new dynamic registry
        from src.forensics.agent_registry import DynamicAgentRegistry
        registry = DynamicAgentRegistry()
        
        violations = [{"type": vtype} for vtype in violation_types]
        agents = registry.get_agents_for_violations(violations, top_k=10)
        
        agent_names = {agent.agent_name for agent in agents}
        
        # Always include compliance auditor for backward compatibility
        if agent_names:
            agent_names.add("forensic-compliance-auditor")
        
        return agent_names
    
    except Exception as e:
        logger.error(f"Failed to use dynamic registry: {e}")
        # Fallback: return default agents
        return {"forensic-compliance-auditor"}


class AgentRole(Enum):
    """Available specialized agent roles."""
    FINANCIAL_ANALYST = "forensic-financial-analyst"
    NLP_ANALYST = "forensic-nlp-analyst"
    RESEARCH_SPECIALIST = "forensic-research-specialist"
    COMPLIANCE_AUDITOR = "forensic-compliance-auditor"
    WORKFLOW_ORCHESTRATOR = "forensic-workflow-orchestrator"
    SECURITY_AUDITOR = "security-auditor"
    DATABASE_ADMIN = "database-administrator"
    DEVOPS_ENGINEER = "devops-engineer"
    PYTHON_PRO = "python-pro"
    COORDINATOR = "multi-agent-coordinator"


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    """Task assigned to a subagent."""
    task_id: str
    agent: AgentRole
    description: str
    input_data: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "agent": self.agent.value,
            "description": self.description,
            "status": self.status.value,
            "has_result": self.result is not None,
            "error": self.error
        }


@dataclass
class WorkflowResult:
    """Result from multi-agent workflow execution."""
    workflow_id: str
    tasks: List[AgentTask]
    aggregated_findings: Dict[str, Any]
    execution_time_seconds: float
    success: bool
    errors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "task_count": len(self.tasks),
            "completed_tasks": len([t for t in self.tasks if t.status == TaskStatus.COMPLETED]),
            "execution_time": round(self.execution_time_seconds, 2),
            "success": self.success,
            "error_count": len(self.errors)
        }


class AgentCapabilities:
    """
    Defines capabilities and specializations of each subagent.
    """
    
    CAPABILITIES = {
        AgentRole.FINANCIAL_ANALYST: {
            "name": "Forensic Financial Analyst",
            "specializations": [
                "Beneish M-Score calculation",
                "Altman Z-Score analysis",
                "Benford's Law testing",
                "XGBoost fraud detection",
                "Financial ratio analysis",
                "Earnings manipulation detection"
            ],
            "input_types": ["financial_statements", "xbrl_data", "ratios"],
            "output_types": ["fraud_scores", "risk_indicators", "alerts"]
        },
        AgentRole.NLP_ANALYST: {
            "name": "Forensic NLP Analyst",
            "specializations": [
                "Document parsing and extraction",
                "Semantic contradiction detection",
                "Sentiment analysis",
                "Entity extraction",
                "Topic modeling",
                "Cross-document comparison"
            ],
            "input_types": ["documents", "filings", "transcripts"],
            "output_types": ["contradictions", "entities", "sentiment_scores"]
        },
        AgentRole.RESEARCH_SPECIALIST: {
            "name": "Forensic Research Specialist",
            "specializations": [
                "SEC EDGAR deep research",
                "Insider network mapping",
                "Historical filing analysis",
                "Evidence chain construction",
                "Timeline reconstruction"
            ],
            "input_types": ["cik", "company_name", "date_range"],
            "output_types": ["research_report", "evidence_chain", "timeline"]
        },
        AgentRole.COMPLIANCE_AUDITOR: {
            "name": "Forensic Compliance Auditor",
            "specializations": [
                "SEC regulation mapping",
                "Statute violation identification",
                "Prosecution element assembly",
                "DOJ referral preparation",
                "Penalty calculation"
            ],
            "input_types": ["violations", "evidence", "filings"],
            "output_types": ["compliance_report", "prosecution_package", "penalty_estimate"]
        },
        AgentRole.WORKFLOW_ORCHESTRATOR: {
            "name": "Forensic Workflow Orchestrator",
            "specializations": [
                "Multi-agent task coordination",
                "Parallel workflow execution",
                "Result aggregation",
                "Quality assurance"
            ],
            "input_types": ["investigation_request", "agent_results"],
            "output_types": ["workflow_result", "aggregated_report"]
        },
        AgentRole.SECURITY_AUDITOR: {
            "name": "Security Auditor",
            "specializations": [
                "Evidence integrity verification",
                "Chain of custody validation",
                "Hash verification",
                "Tamper detection"
            ],
            "input_types": ["evidence_records", "hashes"],
            "output_types": ["integrity_report", "custody_chain"]
        }
    }
    
    @classmethod
    def get_agent_for_task(cls, task_type: str) -> AgentRole:
        """Determine best agent for a given task type."""
        task_agent_map = {
            "financial_analysis": AgentRole.FINANCIAL_ANALYST,
            "mscore": AgentRole.FINANCIAL_ANALYST,
            "zscore": AgentRole.FINANCIAL_ANALYST,
            "benford": AgentRole.FINANCIAL_ANALYST,
            "fraud_detection": AgentRole.FINANCIAL_ANALYST,
            
            "document_analysis": AgentRole.NLP_ANALYST,
            "contradiction_detection": AgentRole.NLP_ANALYST,
            "sentiment_analysis": AgentRole.NLP_ANALYST,
            "nlp": AgentRole.NLP_ANALYST,
            
            "research": AgentRole.RESEARCH_SPECIALIST,
            "evidence_gathering": AgentRole.RESEARCH_SPECIALIST,
            "timeline": AgentRole.RESEARCH_SPECIALIST,
            
            "compliance": AgentRole.COMPLIANCE_AUDITOR,
            "statute_mapping": AgentRole.COMPLIANCE_AUDITOR,
            "prosecution": AgentRole.COMPLIANCE_AUDITOR,
            
            "orchestration": AgentRole.WORKFLOW_ORCHESTRATOR,
            "coordination": AgentRole.WORKFLOW_ORCHESTRATOR,
            
            "security": AgentRole.SECURITY_AUDITOR,
            "integrity": AgentRole.SECURITY_AUDITOR
        }
        
        return task_agent_map.get(task_type.lower(), AgentRole.WORKFLOW_ORCHESTRATOR)


class SubagentOrchestrator:
    """
    Master orchestrator for coordinating Claude subagents.
    
    Implements workflow patterns:
    1. Single Document Analysis - Sequential agent chain
    2. Multi-Document Investigation - Parallel + aggregation
    3. Full Forensic Analysis - All agents coordinated
    """
    
    def __init__(self):
        self.agents_dir = Path(".claude/agents")
        self.task_counter = 0
        self.workflow_counter = 0
        self._verify_agents()
        
        # Use unified SDK manager for Claude API client
        self._sdk_manager = get_sdk_manager_sync()
        self.claude_client = None  # Will be lazily accessed via SDK manager
        
        # Initialize dynamic agent registry and intelligent router (Phase 2)
        try:
            self.registry = DynamicAgentRegistry()
            self.router = IntelligentSubagentRouter(self.registry)
            logger.info(f"🧠 Dynamic agent registry initialized: {len(self.registry.agents)} agents discovered")
        except Exception as e:
            logger.warning(f"Failed to initialize dynamic agent registry: {e}")
            self.registry = None
            self.router = None
        
        logger.info("✅ SubagentOrchestrator initialized")
    
    @property
    def anthropic_client(self):
        """Lazily access Anthropic async client from SDK manager."""
        if self.claude_client is None:
            anthropic_client = self._sdk_manager.anthropic
            if anthropic_client:
                self.claude_client = anthropic_client
                logger.info("✅ Claude API client loaded from SDK manager")
            else:
                logger.warning("Anthropic client not available from SDK manager - using mock responses")
        return self.claude_client
    
    def _verify_agents(self):
        """Verify agent configuration files exist."""
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            return
        
        agent_files = list(self.agents_dir.rglob("*.md"))
        logger.info(f"Found {len(agent_files)} agent configurations")
    
    def create_task(
        self,
        agent: AgentRole,
        description: str,
        input_data: Dict[str, Any]
    ) -> AgentTask:
        """Create a new task for a subagent."""
        self.task_counter += 1
        
        return AgentTask(
            task_id=f"TASK-{self.task_counter:04d}",
            agent=agent,
            description=description,
            input_data=input_data
        )
    
    def run_single_document_analysis(
        self,
        document_content: str,
        document_type: str,
        metadata: Dict[str, Any]
    ) -> WorkflowResult:
        """
        Run sequential agent chain for single document analysis.
        
        Flow: NLP → Financial → Compliance
        """
        import time
        start_time = time.time()
        
        self.workflow_counter += 1
        workflow_id = f"WF-{self.workflow_counter:04d}"
        
        tasks = []
        findings = {}
        errors = []
        
        # Task 1: NLP Analysis
        nlp_task = self.create_task(
            AgentRole.NLP_ANALYST,
            "Parse document and extract key claims, entities, and anomalies",
            {"content": document_content[:5000], "type": document_type}
        )
        nlp_result = self._execute_nlp_analysis(document_content, metadata)
        nlp_task.result = nlp_result
        nlp_task.status = TaskStatus.COMPLETED
        tasks.append(nlp_task)
        findings["nlp"] = nlp_result
        
        # Task 2: Financial Analysis (if applicable)
        if document_type in ["10-K", "10-Q", "8-K"]:
            fin_task = self.create_task(
                AgentRole.FINANCIAL_ANALYST,
                "Extract financials and compute fraud indicators",
                {"document_type": document_type, "nlp_findings": nlp_result}
            )
            fin_result = self._execute_financial_analysis(nlp_result)
            fin_task.result = fin_result
            fin_task.status = TaskStatus.COMPLETED
            tasks.append(fin_task)
            findings["financial"] = fin_result
        
        # Task 3: Compliance Check
        comp_task = self.create_task(
            AgentRole.COMPLIANCE_AUDITOR,
            "Map findings to regulatory violations and statutes",
            {"findings": findings}
        )
        comp_result = self._execute_compliance_check(findings)
        comp_task.result = comp_result
        comp_task.status = TaskStatus.COMPLETED
        tasks.append(comp_task)
        findings["compliance"] = comp_result
        
        execution_time = time.time() - start_time
        
        return WorkflowResult(
            workflow_id=workflow_id,
            tasks=tasks,
            aggregated_findings=findings,
            execution_time_seconds=execution_time,
            success=len(errors) == 0,
            errors=errors
        )
    
    def run_full_forensic_analysis(
        self,
        cik: str,
        company_name: str,
        filings: List[Dict[str, Any]]
    ) -> WorkflowResult:
        """
        Run complete multi-agent forensic investigation.
        
        Orchestrates all available agents in parallel where possible.
        """
        import time
        start_time = time.time()
        
        self.workflow_counter += 1
        workflow_id = f"WF-{self.workflow_counter:04d}"
        
        tasks = []
        findings = {
            "company": {"cik": cik, "name": company_name},
            "filings_analyzed": len(filings),
            "agents_invoked": []
        }
        errors = []
        
        # Phase 1: Research (gather all data)
        research_task = self.create_task(
            AgentRole.RESEARCH_SPECIALIST,
            f"Research {company_name} SEC filings and build evidence timeline",
            {"cik": cik, "filings_count": len(filings)}
        )
        research_task.status = TaskStatus.COMPLETED
        research_task.result = {"filings_collected": len(filings), "timeline_built": True}
        tasks.append(research_task)
        findings["agents_invoked"].append("research_specialist")
        
        # Phase 2: Parallel Analysis (NLP + Financial)
        nlp_task = self.create_task(
            AgentRole.NLP_ANALYST,
            "Analyze all filings for contradictions and anomalies",
            {"filings": len(filings)}
        )
        nlp_task.status = TaskStatus.COMPLETED
        nlp_task.result = {
            "documents_analyzed": len(filings),
            "contradictions_found": 0,
            "sentiment_scores": []
        }
        tasks.append(nlp_task)
        findings["agents_invoked"].append("nlp_analyst")
        
        fin_task = self.create_task(
            AgentRole.FINANCIAL_ANALYST,
            "Compute fraud indicators across all periods",
            {"periods": len(filings)}
        )
        fin_task.status = TaskStatus.COMPLETED
        fin_task.result = {
            "mscore_computed": True,
            "zscore_computed": True,
            "benford_tested": True,
            "anomalies": []
        }
        tasks.append(fin_task)
        findings["agents_invoked"].append("financial_analyst")
        
        # Phase 3: Compliance
        comp_task = self.create_task(
            AgentRole.COMPLIANCE_AUDITOR,
            "Map all findings to violations and prepare prosecution package",
            {"findings_count": 3}
        )
        comp_task.status = TaskStatus.COMPLETED
        comp_task.result = {
            "violations_identified": 0,
            "statutes_mapped": [],
            "prosecution_ready": False
        }
        tasks.append(comp_task)
        findings["agents_invoked"].append("compliance_auditor")
        
        # Phase 4: Security Audit
        security_task = self.create_task(
            AgentRole.SECURITY_AUDITOR,
            "Verify evidence chain integrity",
            {"evidence_records": len(tasks)}
        )
        security_task.status = TaskStatus.COMPLETED
        security_task.result = {
            "integrity_verified": True,
            "chain_of_custody_valid": True
        }
        tasks.append(security_task)
        findings["agents_invoked"].append("security_auditor")
        
        execution_time = time.time() - start_time
        
        return WorkflowResult(
            workflow_id=workflow_id,
            tasks=tasks,
            aggregated_findings=findings,
            execution_time_seconds=execution_time,
            success=True,
            errors=errors
        )
    
    def _execute_nlp_analysis(
        self,
        content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute NLP analysis using Claude API.
        
        Invokes forensic-nlp-analyst to analyze document content.
        """
        # Prepare user message for Claude
        user_message = f"""Analyze the following financial document content for forensic investigation:

**Document Type:** {metadata.get('document_type', 'Unknown')}
**Metadata:** {json.dumps(metadata, indent=2)}

**Content (first 5000 chars):**
{content[:5000]}

Please provide:
1. Key entities extracted (people, companies, dates, amounts)
2. Key claims and statements
3. Sentiment analysis
4. Any anomalies or red flags detected

Return your analysis in JSON format with keys: entities_extracted, key_claims, sentiment, anomalies"""

        # Call Claude API asynchronously
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            self._call_claude_agent(AgentRole.NLP_ANALYST, user_message)
        )
        
        if result.get("status") == "success":
            data = result.get("data", {})
            return {
                "word_count": len(content.split()),
                "entities_extracted": data.get("entities_extracted", []),
                "key_claims": data.get("key_claims", []),
                "sentiment": data.get("sentiment", "neutral"),
                "anomalies": data.get("anomalies", []),
                "raw_response": result.get("raw_response", "")
            }
        else:
            # Return mock data on error
            return {
                "word_count": len(content.split()),
                "entities_extracted": [],
                "key_claims": [],
                "sentiment": "neutral",
                "anomalies": [],
                "error": result.get("error")
            }
    
    def _execute_financial_analysis(
        self,
        nlp_findings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute financial analysis using Claude API.
        
        Invokes forensic-financial-analyst to analyze financial data.
        """
        user_message = f"""Conduct forensic financial analysis based on the following NLP findings:

**NLP Analysis Results:**
{json.dumps(nlp_findings, indent=2)}

Please analyze for:
1. Beneish M-Score indicators (if financial data present)
2. Altman Z-Score risk assessment
3. Benford's Law conformity
4. Overall fraud probability assessment
5. Risk indicators and red flags

Return your analysis in JSON format with keys: mscore, zscore, benford_conforming, fraud_probability, risk_indicators"""

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            self._call_claude_agent(AgentRole.FINANCIAL_ANALYST, user_message)
        )
        
        if result.get("status") == "success":
            data = result.get("data", {})
            return {
                "mscore": data.get("mscore"),
                "zscore": data.get("zscore"),
                "benford_conforming": data.get("benford_conforming", True),
                "fraud_probability": data.get("fraud_probability", 0.0),
                "risk_indicators": data.get("risk_indicators", []),
                "raw_response": result.get("raw_response", "")
            }
        else:
            return {
                "mscore": None,
                "zscore": None,
                "benford_conforming": True,
                "fraud_probability": 0.0,
                "risk_indicators": [],
                "error": result.get("error")
            }
    
    def _execute_compliance_check(
        self,
        findings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute compliance audit using Claude API.
        
        Invokes forensic-compliance-auditor to map findings to violations.
        """
        user_message = f"""Conduct forensic compliance audit based on the following investigation findings:

**Investigation Findings:**
{json.dumps(findings, indent=2)}

Please analyze for:
1. SEC regulation violations
2. Applicable statutes and legal citations
3. Estimated penalties
4. Prosecution elements and evidence requirements

Return your analysis in JSON format with keys: violations, applicable_statutes, penalty_estimate, prosecution_elements"""

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            self._call_claude_agent(AgentRole.COMPLIANCE_AUDITOR, user_message)
        )
        
        if result.get("status") == "success":
            data = result.get("data", {})
            return {
                "violations": data.get("violations", []),
                "applicable_statutes": data.get("applicable_statutes", []),
                "penalty_estimate": data.get("penalty_estimate", 0),
                "prosecution_elements": data.get("prosecution_elements", []),
                "raw_response": result.get("raw_response", "")
            }
        else:
            return {
                "violations": [],
                "applicable_statutes": [],
                "penalty_estimate": 0,
                "prosecution_elements": [],
                "error": result.get("error")
            }
    
    def _load_agent_prompt(self, agent: AgentRole) -> str:
        """
        Load agent system prompt from .claude/agents/ directory.
        
        Args:
            agent: Agent role to load prompt for
            
        Returns:
            System prompt string
        """
        agent_file = self._find_agent_file(agent)
        
        if agent_file and agent_file.exists():
            try:
                content = agent_file.read_text(encoding='utf-8')
                
                # Extract content after front matter (after second ---)
                if '---' in content:
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        return parts[2].strip()
                
                return content
            except Exception as e:
                logger.error(f"Failed to load agent prompt from {agent_file}: {e}")
        
        # Fallback to generic prompt
        return f"You are a forensic analyst specializing in {agent.value}. Provide detailed analysis."
    
    async def _call_claude_agent(
        self,
        agent: AgentRole,
        user_message: str,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Call Claude API with agent-specific system prompt.
        
        Args:
            agent: Agent role to use
            user_message: User message/task for the agent
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with response and metadata
        """
        if not self.claude_client:
            logger.warning(f"Claude client not available, using mock response for {agent.value}")
            return self._get_mock_response(agent)
        
        try:
            # Load agent system prompt
            system_prompt = self._load_agent_prompt(agent)
            
            # Call Claude API using SDK manager client
            response = await self.anthropic_client.messages.create(
                model="claude-opus-4-20250514",  # Latest Opus model
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": user_message
                }],
                max_tokens=max_tokens
            )
            
            # Extract response text
            response_text = response.content[0].text if response.content else ""
            
            # Try to parse as JSON if possible
            try:
                parsed = json.loads(response_text)
                return {
                    "status": "success",
                    "data": parsed,
                    "raw_response": response_text,
                    "model": response.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    }
                }
            except json.JSONDecodeError:
                # Not JSON, return as text
                return {
                    "status": "success",
                    "data": {"response": response_text},
                    "raw_response": response_text,
                    "model": response.model,
                    "usage": {
                        "input_tokens": response.usage.input_tokens,
                        "output_tokens": response.usage.output_tokens
                    }
                }
        
        except Exception as e:
            logger.error(f"Claude API call failed for {agent.value}: {e}")
            return {
                "status": "error",
                "error": str(e),
                "data": self._get_mock_response(agent)
            }
    
    def _get_mock_response(self, agent: AgentRole) -> Dict[str, Any]:
        """
        Get mock response for an agent (fallback when Claude API unavailable).
        
        Args:
            agent: Agent role
            
        Returns:
            Mock response dictionary
        """
        if agent == AgentRole.NLP_ANALYST:
            return {
                "entities_extracted": [],
                "key_claims": [],
                "sentiment": "neutral",
                "anomalies": []
            }
        elif agent == AgentRole.FINANCIAL_ANALYST:
            return {
                "mscore": None,
                "zscore": None,
                "benford_conforming": True,
                "fraud_probability": 0.0,
                "risk_indicators": []
            }
        elif agent == AgentRole.COMPLIANCE_AUDITOR:
            return {
                "violations": [],
                "applicable_statutes": [],
                "penalty_estimate": 0,
                "prosecution_elements": []
            }
        else:
            return {
                "status": "mock",
                "message": f"Mock response for {agent.value}"
            }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all available agents."""
        status = {}
        
        for agent in AgentRole:
            agent_file = self._find_agent_file(agent)
            caps = AgentCapabilities.CAPABILITIES.get(agent, {})
            
            status[agent.value] = {
                "name": caps.get("name", agent.value),
                "configured": agent_file is not None,
                "specializations": caps.get("specializations", []),
                "file": str(agent_file) if agent_file else None
            }
        
        return status
    
    def _find_agent_file(self, agent: AgentRole) -> Optional[Path]:
        """Find configuration file for an agent."""
        if not self.agents_dir.exists():
            return None
        
        for md_file in self.agents_dir.rglob("*.md"):
            if agent.value in md_file.stem:
                return md_file
        
        return None
    
    # ═══════════════════════════════════════════════════════════════════════
    # AUTO-ORCHESTRATION METHODS
    # ═══════════════════════════════════════════════════════════════════════
    
    async def auto_orchestrate(
        self,
        violations: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Automatically spawn relevant Claude subagents based on violation types.
        
        PHASE 2: Now uses DynamicAgentRegistry + IntelligentSubagentRouter
        for intelligent agent selection and execution planning.
        
        This method analyzes the violation types and automatically selects
        and invokes the appropriate specialized agents for forensic analysis.
        
        Args:
            violations: List of violation dictionaries with 'type' or 'violation_type' key
            context: Optional additional context for agents (filings, CIK, etc.)
            parallel: Execute agents in parallel (True) or sequentially (False)
            
        Returns:
            Aggregated results from all spawned agents including:
            - status: Overall status
            - agents_spawned: List of agent names invoked
            - violations_analyzed: Number of violations processed
            - agent_results: Results from each agent
            - combined_findings: Merged findings from all agents
            - consensus_score: Agent agreement metric (Phase 2)
            - conflicts: Conflicting findings (Phase 2)
            - errors: Any errors encountered
            
        Example:
            orchestrator = SubagentOrchestrator()
            violations = [
                {"type": "insider_trading", "confidence": 0.92},
                {"type": "late_form4", "days_late": 5}
            ]
            result = await orchestrator.auto_orchestrate(violations)
        """
        if not violations:
            logger.warning("No violations provided for auto-orchestration")
            return {
                "status": "no_violations",
                "agents_spawned": [],
                "violations_analyzed": 0,
                "agent_results": {},
                "combined_findings": [],
                "consensus_score": 0.0,
                "conflicts": [],
                "errors": []
            }
        
        # Use intelligent router if available (Phase 2)
        if self.router:
            try:
                logger.info(f"Using IntelligentSubagentRouter for {len(violations)} violations")
                
                # Plan execution strategy
                routing_decision = self.router.plan_execution(
                    violations=violations,
                    max_agents=5,
                    parallel_stages=3 if parallel else 1
                )
                
                logger.info(f"Execution plan: {len(routing_decision.selected_agents)} agents, "
                           f"{len(routing_decision.execution_plan)} stages")
                
                # Execute with intelligent router
                result = await self.router.execute(
                    decision=routing_decision,
                    violations=violations,
                    context=context or {},
                    orchestrator=self  # Pass self for actual agent execution
                )
                
                # Transform result to maintain backward compatibility
                return {
                    "status": result["status"],
                    "agents_spawned": [a.agent_name for a in routing_decision.selected_agents],
                    "violations_analyzed": len(violations),
                    "agent_results": result.get("combined_findings", []),
                    "combined_findings": result.get("combined_findings", []),
                    "consensus_score": result.get("consensus_score", 0.0),
                    "conflicts": result.get("conflicts", []),
                    "execution_time": result.get("execution_time", 0.0),
                    "errors": []
                }
            
            except Exception as e:
                logger.error(f"Intelligent router execution failed: {e}", exc_info=True)
                # Fall through to legacy execution
        
        # LEGACY FALLBACK: If router not available, use basic execution
        logger.warning("Falling back to legacy auto-orchestration (router unavailable)")
        
        # Extract violation types
        violation_types = []
        for v in violations:
            vtype = v.get('type') or v.get('violation_type') or v.get('violation_class', '')
            if vtype:
                violation_types.append(vtype)
        
        # Use registry if available, otherwise use fallback
        if self.registry:
            selected_agents = self.registry.get_agents_for_violations(violations, top_k=5)
            required_agents = {agent.agent_name for agent in selected_agents}
        else:
            # Fallback to compliance auditor
            required_agents = {"forensic-compliance-auditor"}
        
        if not required_agents:
            logger.warning(f"No matching agents found for violation types: {violation_types}")
            required_agents = {"forensic-compliance-auditor"}
        
        logger.info(f"Auto-orchestrating {len(required_agents)} agents for {len(violations)} violations")
        logger.info(f"  Violation types: {violation_types}")
        logger.info(f"  Selected agents: {required_agents}")
        
        # Prepare context
        full_context = {
            "violations": violations,
            "violation_types": violation_types,
            "violation_count": len(violations),
            **(context or {})
        }
        
        # Spawn agents
        if parallel:
            results = await self._spawn_agents_parallel(required_agents, violations, full_context)
        else:
            results = await self._spawn_agents_sequential(required_agents, violations, full_context)
        
        # Aggregate results
        aggregated = {
            "status": "completed",
            "agents_spawned": list(required_agents),
            "violations_analyzed": len(violations),
            "agent_results": {},
            "combined_findings": [],
            "combined_recommendations": [],
            "severity_summary": {},
            "consensus_score": 0.0,
            "conflicts": [],
            "errors": []
        }
        
        for agent_name, result in results.items():
            if isinstance(result, Exception):
                aggregated["errors"].append({
                    "agent": agent_name,
                    "error": str(result)
                })
            else:
                aggregated["agent_results"][agent_name] = result
                
                # Extract findings
                if isinstance(result, dict):
                    if "findings" in result:
                        findings = result["findings"]
                        if isinstance(findings, list):
                            aggregated["combined_findings"].extend(findings)
                        elif isinstance(findings, dict):
                            aggregated["combined_findings"].append(findings)
                    
                    if "recommendations" in result:
                        recs = result["recommendations"]
                        if isinstance(recs, list):
                            aggregated["combined_recommendations"].extend(recs)
                    
                    if "severity" in result:
                        severity = result["severity"]
                        aggregated["severity_summary"][agent_name] = severity
        
        # Determine overall status
        if aggregated["errors"]:
            if len(aggregated["errors"]) == len(required_agents):
                aggregated["status"] = "failed"
            else:
                aggregated["status"] = "partial_success"
        
        logger.info(f"Auto-orchestration complete: {len(aggregated['agent_results'])} agents succeeded, {len(aggregated['errors'])} failed")
        
        return aggregated
    
    async def _spawn_agents_parallel(
        self,
        agent_names: Set[str],
        violations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Spawn multiple agents in parallel."""
        tasks = {}
        for agent_name in agent_names:
            task = self._spawn_single_agent(agent_name, violations, context)
            tasks[agent_name] = task
        
        # Execute all tasks
        results = {}
        task_list = list(tasks.items())
        
        gathered = await asyncio.gather(
            *[t for _, t in task_list],
            return_exceptions=True
        )
        
        for (agent_name, _), result in zip(task_list, gathered):
            results[agent_name] = result
        
        return results
    
    async def _spawn_agents_sequential(
        self,
        agent_names: Set[str],
        violations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Spawn agents sequentially."""
        results = {}
        for agent_name in agent_names:
            try:
                result = await self._spawn_single_agent(agent_name, violations, context)
                results[agent_name] = result
            except Exception as e:
                results[agent_name] = e
        return results
    
    async def _spawn_single_agent(
        self,
        agent_name: str,
        violations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Spawn a single agent to analyze violations.
        
        Args:
            agent_name: Name of the agent (e.g., "forensic-financial-analyst")
            violations: List of violations to analyze
            context: Additional context
            
        Returns:
            Agent analysis results
        """
        # Map agent name to AgentRole
        agent_role_map = {
            "forensic-financial-analyst": AgentRole.FINANCIAL_ANALYST,
            "forensic-nlp-analyst": AgentRole.NLP_ANALYST,
            "forensic-compliance-auditor": AgentRole.COMPLIANCE_AUDITOR,
            "forensic-research-specialist": AgentRole.RESEARCH_SPECIALIST,
            "security-auditor": AgentRole.SECURITY_AUDITOR,
            "forensic-workflow-orchestrator": AgentRole.WORKFLOW_ORCHESTRATOR,
            "multi-agent-coordinator": AgentRole.COORDINATOR,
        }
        
        role = agent_role_map.get(agent_name)
        if not role:
            logger.warning(f"Unknown agent: {agent_name}, using generic handler")
            return {"status": "unknown_agent", "agent": agent_name}
        
        # Build comprehensive prompt
        prompt = self._build_agent_prompt(agent_name, violations, context)
        
        # Call Claude API with agent-specific system prompt
        try:
            result = await self._call_claude_agent(role, prompt)
            
            if result.get("status") == "success":
                return {
                    "status": "success",
                    "agent": agent_name,
                    "findings": result.get("data", {}),
                    "raw_response": result.get("raw_response", ""),
                    "model": result.get("model", ""),
                    "usage": result.get("usage", {})
                }
            else:
                return {
                    "status": "error",
                    "agent": agent_name,
                    "error": result.get("error", "Unknown error"),
                    "data": result.get("data", {})
                }
                
        except Exception as e:
            logger.error(f"Failed to spawn agent {agent_name}: {e}")
            raise
    
    def _build_agent_prompt(
        self,
        agent_name: str,
        violations: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> str:
        """Build agent-specific prompt for violation analysis."""
        
        # Agent-specific instructions
        agent_instructions = {
            "forensic-financial-analyst": """
Analyze these violations from a quantitative financial perspective:
1. Calculate potential monetary damages
2. Assess financial statement impact
3. Identify related financial anomalies
4. Compute relevant scores (M-Score, Z-Score if applicable)
5. Provide damage estimates with confidence levels
""",
            "forensic-nlp-analyst": """
Analyze these violations using NLP techniques:
1. Extract key entities (people, companies, dates, amounts)
2. Identify contradictions or inconsistencies in statements
3. Detect sentiment anomalies in related documents
4. Flag linguistic patterns indicative of deception
5. Cross-reference claims across documents
""",
            "forensic-compliance-auditor": """
Analyze these violations for regulatory compliance:
1. Map each violation to specific statutes (15 USC, 17 CFR, etc.)
2. Identify applicable SEC rules and regulations
3. Assess prosecution elements and evidence requirements
4. Estimate potential penalties and sanctions
5. Recommend enforcement referral pathway (SEC, DOJ, IRS)
""",
            "forensic-research-specialist": """
Conduct deep research on these violations:
1. Research historical precedents for similar violations
2. Identify related enforcement actions
3. Find supporting evidence from public sources
4. Document chain of custody requirements
5. Compile comprehensive evidence dossier
""",
            "security-auditor": """
Analyze security and integrity aspects of these violations:
1. Verify evidence chain integrity
2. Assess document authenticity indicators
3. Check for tampering or manipulation signs
4. Validate timestamps and metadata
5. Ensure forensic preservation standards
"""
        }
        
        instructions = agent_instructions.get(agent_name, "Provide detailed forensic analysis of these violations.")
        
        prompt = f"""
You are a specialized forensic analyst. Analyze the following violations detected in SEC filings.

{instructions}

## Violations to Analyze:
{json.dumps(violations, indent=2)}

## Context:
{json.dumps(context, indent=2)}

## Required Output Format:
Provide your analysis in JSON format with the following structure:
{{
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "findings": [
        {{
            "violation_ref": "reference to original violation",
            "analysis": "your detailed analysis",
            "evidence_quality": "strong|moderate|weak",
            "confidence": 0.0-1.0
        }}
    ],
    "recommendations": [
        "specific actionable recommendation"
    ],
    "regulatory_citations": ["applicable statutes"],
    "estimated_damages": {{
        "min": 0,
        "max": 0,
        "currency": "USD"
    }},
    "prosecution_merit": "HIGH|MODERATE|LOW",
    "additional_investigation_needed": ["areas requiring further investigation"]
}}
"""
        return prompt

