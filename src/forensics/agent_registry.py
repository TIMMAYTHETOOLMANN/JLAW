"""
Dynamic Agent Registry for JLAW Forensic System
===============================================

Dynamically discovers and registers Claude subagents from markdown files in
.claude/agents/ directory. Extracts capability metadata from frontmatter and
builds reverse index for intelligent agent selection based on violation types.

Key Features:
- Automatic agent discovery from markdown files
- Frontmatter parsing (YAML between --- delimiters)
- Capability metadata extraction (name, description, tools, priority)
- Violation-to-agent reverse index building
- Intelligent agent scoring and top-K selection

Usage:
    from src.forensics.agent_registry import DynamicAgentRegistry
    
    registry = DynamicAgentRegistry()
    agents = registry.get_agents_for_violations(
        violations=[{"type": "insider_trading"}],
        top_k=5
    )
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
import yaml

logger = logging.getLogger(__name__)


@dataclass
class AgentCapability:
    """
    Metadata for a Claude subagent extracted from markdown file.
    
    Attributes:
        agent_name: Unique agent identifier (e.g., 'forensic-financial-analyst')
        description: Brief description of agent capabilities
        violation_types: Set of violation types this agent can handle
        tools: List of tools available to agent (Read, Write, Edit, etc.)
        priority: Agent priority (higher = spawned first), default 50
        requires_anthropic: Whether agent requires Anthropic API access
        markdown_path: Path to agent markdown file
        prompt_template: Full prompt content from markdown
    """
    agent_name: str
    description: str
    violation_types: Set[str] = field(default_factory=set)
    tools: List[str] = field(default_factory=list)
    priority: int = 50
    requires_anthropic: bool = True
    markdown_path: Path = None
    prompt_template: str = ""
    
    def matches_violation(self, violation_type: str) -> bool:
        """
        Check if agent can handle a violation type.
        
        Args:
            violation_type: Violation type string (e.g., 'insider_trading')
            
        Returns:
            True if agent has this violation type in capabilities
        """
        # Normalize violation type
        normalized = violation_type.lower().replace(" ", "_").replace("-", "_")
        
        # Check exact match
        if normalized in self.violation_types:
            return True
        
        # Check partial match
        for vtype in self.violation_types:
            if normalized in vtype or vtype in normalized:
                return True
        
        return False
    
    def score_for_violations(self, violation_types: List[str]) -> float:
        """
        Calculate relevance score for a list of violations.
        
        Args:
            violation_types: List of violation type strings
            
        Returns:
            Score (0.0-1.0) indicating agent relevance
        """
        if not violation_types:
            return 0.0
        
        matches = sum(1 for vt in violation_types if self.matches_violation(vt))
        return matches / len(violation_types)


class DynamicAgentRegistry:
    """
    Discovers and registers Claude subagents from markdown files.
    
    Scans .claude/agents/**/*.md files, parses frontmatter to extract
    capability metadata, and builds reverse index for violation-based
    agent selection.
    """
    
    def __init__(self, agents_dir: Optional[Path] = None):
        """
        Initialize agent registry and discover agents.
        
        Args:
            agents_dir: Path to agents directory (defaults to .claude/agents/)
        """
        self.agents_dir = agents_dir or self._find_agents_dir()
        self.agents: Dict[str, AgentCapability] = {}
        self.violation_to_agents: Dict[str, Set[str]] = {}
        
        # Discover agents from markdown files
        self._discover_agents()
        
        logger.info(f"🧠 DynamicAgentRegistry initialized: {len(self.agents)} agents discovered")
    
    def _find_agents_dir(self) -> Path:
        """
        Locate .claude/agents/ directory relative to project root.
        
        Returns:
            Path to agents directory
        """
        # Try multiple strategies to find agents directory
        current = Path(__file__).resolve()
        
        # Strategy 1: Go up from src/forensics to project root
        for parent in current.parents:
            agents_path = parent / ".claude" / "agents"
            if agents_path.exists() and agents_path.is_dir():
                return agents_path
        
        # Strategy 2: Use current working directory
        cwd_agents = Path.cwd() / ".claude" / "agents"
        if cwd_agents.exists() and cwd_agents.is_dir():
            return cwd_agents
        
        # Strategy 3: Fallback to relative path
        fallback = Path(__file__).parent.parent.parent / ".claude" / "agents"
        if fallback.exists() and fallback.is_dir():
            return fallback
        
        logger.warning(f"Could not locate .claude/agents/ directory, using fallback: {fallback}")
        return fallback
    
    def _discover_agents(self) -> None:
        """
        Recursively discover agent markdown files and parse metadata.
        
        Scans .claude/agents/**/*.md and extracts capability information
        from frontmatter and content.
        """
        if not self.agents_dir.exists():
            logger.warning(f"Agents directory not found: {self.agents_dir}")
            return
        
        # Find all markdown files recursively
        markdown_files = list(self.agents_dir.rglob("*.md"))
        logger.debug(f"Found {len(markdown_files)} markdown files in {self.agents_dir}")
        
        for md_path in markdown_files:
            try:
                capability = self._parse_agent_markdown(md_path)
                if capability:
                    self.agents[capability.agent_name] = capability
                    
                    # Build reverse index: violation_type -> agent names
                    for vtype in capability.violation_types:
                        if vtype not in self.violation_to_agents:
                            self.violation_to_agents[vtype] = set()
                        self.violation_to_agents[vtype].add(capability.agent_name)
                    
                    logger.debug(f"Registered agent: {capability.agent_name} (priority: {capability.priority})")
            except Exception as e:
                logger.warning(f"Failed to parse agent markdown {md_path}: {e}")
    
    def _parse_agent_markdown(self, md_path: Path) -> Optional[AgentCapability]:
        """
        Parse agent markdown file and extract capability metadata.
        
        Expects YAML frontmatter between --- delimiters at start of file:
        
        ---
        name: forensic-financial-analyst
        description: Quantitative forensic analyst...
        tools: Read, Write, Edit, Bash
        priority: 80
        ---
        
        Extracts violation types from "## Violation Types" section (list items).
        
        Args:
            md_path: Path to markdown file
            
        Returns:
            AgentCapability object or None if parsing fails
        """
        try:
            content = md_path.read_text(encoding='utf-8')
        except Exception as e:
            logger.warning(f"Could not read {md_path}: {e}")
            return None
        
        # Extract YAML frontmatter
        frontmatter_match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        
        if not frontmatter_match:
            # No frontmatter, try to extract basic info from filename
            agent_name = md_path.stem
            logger.debug(f"No frontmatter in {md_path}, using filename: {agent_name}")
            return AgentCapability(
                agent_name=agent_name,
                description=f"Agent {agent_name}",
                markdown_path=md_path,
                prompt_template=content
            )
        
        frontmatter_yaml = frontmatter_match.group(1)
        body_content = frontmatter_match.group(2)
        
        # Parse YAML frontmatter
        try:
            metadata = yaml.safe_load(frontmatter_yaml) or {}
        except yaml.YAMLError as e:
            logger.warning(f"YAML parse error in {md_path}: {e}")
            metadata = {}
        
        # Extract agent name (required)
        agent_name = metadata.get('name', md_path.stem)
        
        # Extract description
        description = metadata.get('description', '')
        
        # Extract tools
        tools_raw = metadata.get('tools', '')
        if isinstance(tools_raw, str):
            tools = [t.strip() for t in tools_raw.split(',') if t.strip()]
        elif isinstance(tools_raw, list):
            tools = [str(t).strip() for t in tools_raw if t]
        else:
            tools = []
        
        # Extract priority
        priority = metadata.get('priority', 50)
        if isinstance(priority, str):
            try:
                priority = int(priority)
            except ValueError:
                priority = 50
        
        # Extract violation types from body content
        violation_types = self._extract_violation_types(body_content)
        
        return AgentCapability(
            agent_name=agent_name,
            description=description,
            violation_types=violation_types,
            tools=tools,
            priority=priority,
            requires_anthropic=True,
            markdown_path=md_path,
            prompt_template=body_content.strip()
        )
    
    def _extract_violation_types(self, content: str) -> Set[str]:
        """
        Extract violation types from markdown content.
        
        Looks for "## Violation Types" section and extracts list items.
        
        Example:
            ## Violation Types
            - insider_trading
            - accounting_fraud
            - options_backdating
        
        Args:
            content: Markdown content
            
        Returns:
            Set of violation type strings (normalized)
        """
        violation_types = set()
        
        # Find "## Violation Types" section
        violation_section_match = re.search(
            r'##\s+Violation\s+Types\s*\n(.*?)(?=\n##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        if not violation_section_match:
            return violation_types
        
        section_content = violation_section_match.group(1)
        
        # Extract list items (lines starting with -)
        for line in section_content.split('\n'):
            line = line.strip()
            if line.startswith('-') or line.startswith('*'):
                # Remove list marker and clean up
                vtype = line.lstrip('-*').strip()
                # Normalize: lowercase, underscores
                vtype_normalized = vtype.lower().replace(" ", "_").replace("-", "_")
                if vtype_normalized:
                    violation_types.add(vtype_normalized)
        
        return violation_types
    
    def get_agents_for_violations(
        self,
        violations: List[Dict[str, Any]],
        top_k: int = 5
    ) -> List[AgentCapability]:
        """
        Get top-K most relevant agents for given violations.
        
        Scores agents based on violation type match count, then sorts by:
        1. Match score (higher = more violation types matched)
        2. Priority (higher = spawned first)
        3. Agent name (alphabetically for determinism)
        
        Args:
            violations: List of violation dicts with 'type' or 'violation_type' key
            top_k: Maximum number of agents to return (default: 5)
            
        Returns:
            List of AgentCapability objects, sorted by relevance
            
        Example:
            violations = [
                {"type": "insider_trading", "confidence": 0.92},
                {"type": "late_form4", "days_late": 5}
            ]
            agents = registry.get_agents_for_violations(violations, top_k=3)
        """
        if not violations:
            return []
        
        # Extract violation types
        violation_types = []
        for v in violations:
            vtype = v.get('type') or v.get('violation_type') or v.get('violation_class', '')
            if vtype:
                violation_types.append(vtype)
        
        if not violation_types:
            return []
        
        # Score all agents
        agent_scores = []
        for agent_name, capability in self.agents.items():
            score = capability.score_for_violations(violation_types)
            if score > 0:
                agent_scores.append((score, capability))
        
        # Sort by: score (desc), priority (desc), name (asc)
        agent_scores.sort(
            key=lambda x: (-x[0], -x[1].priority, x[1].agent_name)
        )
        
        # Return top-K
        return [cap for score, cap in agent_scores[:top_k]]
    
    def get_agent(self, name: str) -> Optional[AgentCapability]:
        """
        Get agent by name.
        
        Args:
            name: Agent name (e.g., 'forensic-financial-analyst')
            
        Returns:
            AgentCapability object or None if not found
        """
        return self.agents.get(name)
    
    def list_agents(self) -> List[str]:
        """
        Get list of all registered agent names.
        
        Returns:
            List of agent names sorted alphabetically
        """
        return sorted(self.agents.keys())
    
    def get_agents_by_violation_type(self, violation_type: str) -> List[AgentCapability]:
        """
        Get all agents that can handle a specific violation type.
        
        Args:
            violation_type: Violation type string (e.g., 'insider_trading')
            
        Returns:
            List of AgentCapability objects
        """
        # Normalize violation type
        normalized = violation_type.lower().replace(" ", "_").replace("-", "_")
        
        # Get agent names from reverse index
        agent_names = self.violation_to_agents.get(normalized, set())
        
        # Return capabilities sorted by priority
        capabilities = [self.agents[name] for name in agent_names if name in self.agents]
        capabilities.sort(key=lambda x: (-x.priority, x.agent_name))
        
        return capabilities
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with registry metrics
        """
        return {
            "total_agents": len(self.agents),
            "total_violation_types": len(self.violation_to_agents),
            "agents_by_priority": self._get_priority_distribution(),
            "violation_coverage": {
                vtype: len(agents) for vtype, agents in self.violation_to_agents.items()
            }
        }
    
    def _get_priority_distribution(self) -> Dict[str, int]:
        """Get distribution of agents by priority ranges."""
        distribution = {
            "critical (80-100)": 0,
            "high (60-79)": 0,
            "medium (40-59)": 0,
            "low (0-39)": 0
        }
        
        for capability in self.agents.values():
            if capability.priority >= 80:
                distribution["critical (80-100)"] += 1
            elif capability.priority >= 60:
                distribution["high (60-79)"] += 1
            elif capability.priority >= 40:
                distribution["medium (40-59)"] += 1
            else:
                distribution["low (0-39)"] += 1
        
        return distribution


__all__ = [
    'DynamicAgentRegistry',
    'AgentCapability'
]
