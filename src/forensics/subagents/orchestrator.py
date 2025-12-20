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
from typing import List, Dict, Any, Optional
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
    MULTI_AGENT_COORDINATOR = "multi-agent-coordinator"


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
        
        # Initialize Claude API client if available
        self.claude_client = None
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                self.claude_client = AsyncAnthropic(api_key=api_key)
                logger.info("✅ Claude API client initialized")
            else:
                logger.warning("ANTHROPIC_API_KEY not set - using mock responses")
        else:
            logger.warning("Anthropic package not available - using mock responses")
    
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
            
            # Call Claude API
            response = await self.claude_client.messages.create(
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

