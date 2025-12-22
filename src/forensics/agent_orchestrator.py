"""
Agent Orchestrator - Agent Definition Parser and Workflow Manager
================================================================

Parses agent definitions from .claude/agents/ directory and provides
programmatic access to agent capabilities for DOJ-grade forensic analysis.

This module bridges the gap between declarative agent definitions (markdown)
and executable orchestration workflows (Python).

Usage:
    orchestrator = AgentOrchestrator()
    agents = orchestrator.list_available_agents()
    workflow = orchestrator.create_workflow("full_forensic", cik="320187")
    result = await orchestrator.execute_workflow(workflow)
"""

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class AgentCategory(Enum):
    """Agent category classification."""
    FORENSIC = "forensic"
    ORCHESTRATION = "orchestration"
    INFRASTRUCTURE = "infrastructure"
    DEVELOPMENT = "development"


@dataclass
class AgentDefinition:
    """Parsed agent definition from markdown file."""
    name: str
    category: AgentCategory
    description: str
    tools: List[str]
    file_path: Path
    capabilities: List[str] = field(default_factory=list)
    workflow_patterns: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "tools": self.tools,
            "file_path": str(self.file_path),
            "capabilities": self.capabilities,
            "workflow_patterns": self.workflow_patterns
        }


@dataclass
class WorkflowDefinition:
    """Workflow definition combining multiple agents."""
    workflow_id: str
    workflow_type: str
    description: str
    agents: List[str]
    execution_order: List[List[str]]  # List of parallel stages
    input_requirements: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)


class AgentOrchestrator:
    """
    Agent Orchestrator - Parses and manages agent definitions.
    
    Features:
    1. Parse agent definitions from .claude/agents/ markdown files
    2. Discover available agents and their capabilities
    3. Create workflow definitions combining multiple agents
    4. Integrate with existing SubagentOrchestrator for execution
    5. Track agent usage and performance metrics
    
    Integration with Phase 7:
    - Called during Phase 7: Subagent Orchestration
    - Provides agent capabilities to execution engine
    - Coordinates multi-agent forensic workflows
    """
    
    def __init__(self, agents_dir: Optional[Path] = None):
        """
        Initialize Agent Orchestrator.
        
        Args:
            agents_dir: Path to .claude/agents directory (default: .claude/agents)
        """
        if agents_dir is None:
            # Try relative to current directory and project root
            if Path(".claude/agents").exists():
                agents_dir = Path(".claude/agents")
            elif Path("../.claude/agents").exists():
                agents_dir = Path("../.claude/agents")
            else:
                # Default fallback
                agents_dir = Path(".claude/agents")
        
        self.agents_dir = agents_dir
        self.agents: Dict[str, AgentDefinition] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        
        # Parse agent definitions on initialization
        self._parse_agent_definitions()
        
        logger.info(f"AgentOrchestrator initialized with {len(self.agents)} agents")
    
    def _parse_agent_definitions(self):
        """Parse all agent definition markdown files."""
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            logger.info("Agent orchestration will operate in degraded mode")
            return
        
        # Find all markdown files
        agent_files = list(self.agents_dir.rglob("*.md"))
        logger.info(f"Found {len(agent_files)} agent definition files")
        
        for agent_file in agent_files:
            try:
                agent_def = self._parse_agent_file(agent_file)
                if agent_def:
                    self.agents[agent_def.name] = agent_def
                    logger.debug(f"Parsed agent: {agent_def.name}")
            except Exception as e:
                logger.error(f"Failed to parse {agent_file}: {e}")
        
        logger.info(f"Successfully parsed {len(self.agents)} agents")
    
    def _parse_agent_file(self, file_path: Path) -> Optional[AgentDefinition]:
        """
        Parse a single agent markdown file.
        
        Format:
        ---
        name: agent-name
        description: Agent description
        tools: Read, Write, Edit, Bash, Glob, Grep
        ---
        
        # Agent content...
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Extract YAML front matter
            front_matter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
            
            if not front_matter_match:
                logger.warning(f"No front matter found in {file_path}")
                return None
            
            front_matter_text = front_matter_match.group(1)
            body_text = front_matter_match.group(2)
            
            # Parse front matter fields
            name_match = re.search(r'^name:\s*(.+)$', front_matter_text, re.MULTILINE)
            desc_match = re.search(r'^description:\s*(.+)$', front_matter_text, re.MULTILINE)
            tools_match = re.search(r'^tools:\s*(.+)$', front_matter_text, re.MULTILINE)
            
            if not (name_match and desc_match):
                logger.warning(f"Missing required fields in {file_path}")
                return None
            
            name = name_match.group(1).strip()
            description = desc_match.group(1).strip()
            tools = [t.strip() for t in tools_match.group(1).split(',')] if tools_match else []
            
            # Determine category from file path
            category = AgentCategory.DEVELOPMENT  # Default
            if 'forensic' in str(file_path):
                category = AgentCategory.FORENSIC
            elif 'orchestration' in str(file_path):
                category = AgentCategory.ORCHESTRATION
            elif 'infrastructure' in str(file_path):
                category = AgentCategory.INFRASTRUCTURE
            
            # Extract capabilities from body (headers starting with ###)
            capabilities = re.findall(r'^###\s+\d+\.\s+(.+)$', body_text, re.MULTILINE)
            
            # Extract workflow patterns
            workflow_patterns = []
            if 'Pattern A:' in body_text or 'Pattern B:' in body_text:
                workflow_patterns = re.findall(r'Pattern [A-Z]:\s*(.+)', body_text)
            
            return AgentDefinition(
                name=name,
                category=category,
                description=description,
                tools=tools,
                file_path=file_path,
                capabilities=capabilities,
                workflow_patterns=workflow_patterns
            )
            
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {e}", exc_info=True)
            return None
    
    def list_available_agents(self) -> List[AgentDefinition]:
        """
        List all available agents.
        
        Returns:
            List of parsed agent definitions
        """
        return list(self.agents.values())
    
    def get_agent(self, name: str) -> Optional[AgentDefinition]:
        """
        Get agent definition by name.
        
        Args:
            name: Agent name
            
        Returns:
            AgentDefinition or None
        """
        return self.agents.get(name)
    
    def get_agents_by_category(self, category: AgentCategory) -> List[AgentDefinition]:
        """
        Get all agents in a specific category.
        
        Args:
            category: Agent category
            
        Returns:
            List of agents in that category
        """
        return [agent for agent in self.agents.values() if agent.category == category]
    
    def create_workflow(
        self,
        workflow_type: str,
        **input_data
    ) -> WorkflowDefinition:
        """
        Create a workflow definition.
        
        Supported workflow types:
        - 'single_document': Sequential analysis of one document
        - 'multi_document': Parallel analysis of multiple documents
        - 'full_forensic': Complete forensic investigation
        - 'contradiction_detection': NLP-focused contradiction analysis
        - 'financial_analysis': Financial metrics and fraud detection
        
        Args:
            workflow_type: Type of workflow to create
            **input_data: Input parameters for the workflow
            
        Returns:
            WorkflowDefinition
        """
        workflow_id = f"WF-{len(self.workflows) + 1:04d}"
        
        # Define workflow patterns
        if workflow_type == 'single_document':
            workflow = WorkflowDefinition(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                description="Sequential single document analysis",
                agents=['forensic-nlp-analyst', 'forensic-financial-analyst', 'forensic-compliance-auditor'],
                execution_order=[
                    ['forensic-nlp-analyst'],
                    ['forensic-financial-analyst'],
                    ['forensic-compliance-auditor']
                ],
                input_requirements=input_data
            )
        
        elif workflow_type == 'multi_document':
            workflow = WorkflowDefinition(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                description="Parallel multi-document investigation",
                agents=['forensic-nlp-analyst', 'forensic-compliance-auditor'],
                execution_order=[
                    ['forensic-nlp-analyst'] * 4,  # Parallel NLP analysis
                    ['forensic-compliance-auditor']  # Aggregation
                ],
                input_requirements=input_data
            )
        
        elif workflow_type == 'full_forensic':
            workflow = WorkflowDefinition(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                description="Complete forensic investigation",
                agents=[
                    'forensic-research-specialist',
                    'forensic-nlp-analyst',
                    'forensic-financial-analyst',
                    'security-auditor',
                    'forensic-compliance-auditor'
                ],
                execution_order=[
                    ['forensic-research-specialist'],  # Timeline construction
                    ['forensic-nlp-analyst', 'forensic-financial-analyst', 'security-auditor'],  # Parallel analysis
                    ['forensic-compliance-auditor']  # Final audit
                ],
                input_requirements=input_data
            )
        
        elif workflow_type == 'contradiction_detection':
            workflow = WorkflowDefinition(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                description="NLP contradiction detection analysis",
                agents=['forensic-nlp-analyst'],
                execution_order=[
                    ['forensic-nlp-analyst']
                ],
                input_requirements=input_data
            )
        
        elif workflow_type == 'financial_analysis':
            workflow = WorkflowDefinition(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                description="Financial fraud detection analysis",
                agents=['forensic-financial-analyst', 'forensic-compliance-auditor'],
                execution_order=[
                    ['forensic-financial-analyst'],
                    ['forensic-compliance-auditor']
                ],
                input_requirements=input_data
            )
        
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
        
        self.workflows[workflow_id] = workflow
        logger.info(f"Created workflow {workflow_id}: {workflow_type}")
        
        return workflow
    
    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        use_subagent_orchestrator: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a workflow.
        
        Args:
            workflow: Workflow definition to execute
            use_subagent_orchestrator: Use existing SubagentOrchestrator if available
            
        Returns:
            Workflow execution results
        """
        logger.info(f"Executing workflow {workflow.workflow_id}: {workflow.workflow_type}")
        
        if use_subagent_orchestrator:
            # Integrate with existing SubagentOrchestrator
            try:
                from src.forensics.subagents.orchestrator import SubagentOrchestrator
                
                orchestrator = SubagentOrchestrator()
                
                # Route to appropriate orchestrator method based on workflow type
                if workflow.workflow_type == 'single_document':
                    # Extract document from input requirements
                    doc_content = workflow.input_requirements.get('document_content', '')
                    doc_type = workflow.input_requirements.get('document_type', 'unknown')
                    metadata = workflow.input_requirements.get('metadata', {})
                    
                    result = orchestrator.run_single_document_analysis(
                        document_content=doc_content,
                        document_type=doc_type,
                        metadata=metadata
                    )
                    
                    return {
                        'workflow_id': workflow.workflow_id,
                        'status': 'completed' if result.success else 'failed',
                        'findings': result.aggregated_findings,
                        'execution_time': result.execution_time_seconds,
                        'errors': result.errors
                    }
                
                elif workflow.workflow_type == 'full_forensic':
                    # Execute full forensic workflow
                    cik = workflow.input_requirements.get('cik')
                    filings = workflow.input_requirements.get('filings', [])
                    
                    result = orchestrator.run_full_forensic_investigation(
                        cik=cik,
                        filings=filings
                    )
                    
                    return {
                        'workflow_id': workflow.workflow_id,
                        'status': 'completed' if result.success else 'failed',
                        'findings': result.aggregated_findings,
                        'execution_time': result.execution_time_seconds,
                        'errors': result.errors
                    }
                
                else:
                    # Mock execution for other workflow types
                    logger.warning(f"Workflow type {workflow.workflow_type} not yet implemented")
                    return {
                        'workflow_id': workflow.workflow_id,
                        'status': 'not_implemented',
                        'message': f"Workflow type {workflow.workflow_type} execution pending"
                    }
                    
            except ImportError as e:
                logger.warning(f"SubagentOrchestrator not available: {e}")
                # Fall through to mock execution
        
        # Mock execution if SubagentOrchestrator not available
        logger.info(f"Mock execution of workflow {workflow.workflow_id}")
        return {
            'workflow_id': workflow.workflow_id,
            'status': 'mock',
            'agents_used': workflow.agents,
            'execution_order': workflow.execution_order,
            'message': 'Mock execution - SubagentOrchestrator integration pending'
        }
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about available agents.
        
        Returns:
            Dictionary with agent statistics
        """
        stats = {
            'total_agents': len(self.agents),
            'by_category': {},
            'agents': [agent.to_dict() for agent in self.agents.values()]
        }
        
        for category in AgentCategory:
            count = len(self.get_agents_by_category(category))
            stats['by_category'][category.value] = count
        
        return stats
