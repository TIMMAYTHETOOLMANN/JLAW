"""
Dependency Resolver - Analyze and resolve dependency chains.
"""

from typing import Dict, List, Set
from collections import defaultdict, deque


class DependencyResolver:
    """
    Analyze dependency chains and determine impact of failures.
    
    Tracks which components depend on which others and calculates
    the cascading impact when a component fails.
    """
    
    def __init__(self):
        """Initialize dependency resolver."""
        self.dependencies = self._build_dependency_graph()
    
    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """
        Build dependency graph for JLAW components.
        
        Returns:
            Dictionary mapping component to list of components that depend on it
        """
        return {
            # Core infrastructure
            "python_3.10+": [
                "All Nodes",
                "All Detection Patterns",
                "All AI Agents",
                "Evidence Chain",
                "Reporting Layer",
            ],
            "requirements.txt": [
                "All Modules",
            ],
            
            # SEC EDGAR
            "SEC_USER_AGENT": [
                "Node 1: Form 4 Insider Trading",
                "Node 2: DEF 14A Compensation",
                "Node 3: 10-Q Temporal Consistency",
                "Node 4: 10-K SOX Certification",
                "Node 5: IRC §83 Tax Calculator",
                "Node 6: Enforcement Routing",
                "Node 7: 13F-HR Holdings",
                "Node 8: 13D/13G Ownership",
                "Node 9: 8-K Material Events",
                "Node 10: Form 144 Restricted Sales",
            ],
            
            # AI APIs
            "OPENAI_API_KEY": [
                "Phase 6: Dual-Agent Validation",
                "GPT-4 Agent",
            ],
            "ANTHROPIC_API_KEY": [
                "Phase 6: Dual-Agent Validation",
                "Phase 7: Subagent Orchestration",
                "Claude 3 Agent",
                "10 Claude Subagents",
                "Node 12: Earnings Call Analysis (DeBERTa fallback)",
            ],
            
            # Market data
            "POLYGON_API_KEY": [
                "Node 15: Market Correlation",
            ],
            
            # Databases
            "NEO4J": [
                "Node 11: Executive Network Mapping",
            ],
            "TIMESCALEDB": [
                "Node 15: Market Correlation (time-series storage)",
                "Historical data storage",
            ],
            
            # Optional heavy dependencies
            "TORCH": [
                "DeBERTa Contradiction Detector",
                "XGBoost Fraud Classifier (optional acceleration)",
            ],
            "TRANSFORMERS": [
                "DeBERTa Contradiction Detector",
                "Node 12: Earnings Call Analysis",
            ],
            
            # Evidence chain
            "HASH_SERVICE": [
                "Phase 8: Evidence Chain",
                "All forensic outputs",
                "FRE 902 compliance",
            ],
            "MERKLE_TREE": [
                "Phase 8: Evidence Chain",
                "Evidence integrity verification",
            ],
            "RFC3161_TIMESTAMP": [
                "Phase 8: Evidence Chain",
                "Timestamp proof generation",
            ],
            
            # Nodes (sequential dependencies)
            "NODE_1": [
                "Phase 4: Node Analysis",
                "Cross-node correlation",
            ],
            "NODE_2": [
                "Phase 4: Node Analysis",
                "Cross-node correlation",
            ],
            "NODE_3": [
                "Phase 4: Node Analysis",
                "Cross-node correlation",
            ],
            "NODE_4": [
                "Phase 4: Node Analysis",
                "Cross-node correlation",
            ],
            "NODE_5": [
                "Phase 4: Node Analysis",
                "Node 6: Enforcement Routing",
            ],
            "NODE_6": [
                "Phase 4: Node Analysis",
            ],
            "NODE_7": [
                "Phase 4: Node Analysis",
                "Cross-node correlation",
            ],
            "NODE_8": [
                "Phase 4: Node Analysis",
                "Cross-node correlation",
            ],
            "NODE_9": [
                "Phase 4: Node Analysis",
                "Cross-node correlation",
            ],
            "NODE_10": [
                "Phase 4: Node Analysis",
                "Cross-node correlation",
            ],
            "NODE_11": [
                "Phase 4: Node Analysis",
                "Network analysis features",
            ],
            "NODE_12": [
                "Phase 4: Node Analysis",
                "NLP analysis features",
            ],
            "NODE_13": [
                "Phase 4: Node Analysis",
                "Financial health scoring",
            ],
            "NODE_14": [
                "Phase 4: Node Analysis",
                "Financial health scoring",
            ],
            "NODE_15": [
                "Phase 4: Node Analysis",
                "Market correlation analysis",
            ],
            
            # Detection patterns
            "BENEISH_MSCORE": [
                "Phase 5: Pattern Detection",
                "Earnings manipulation detection",
            ],
            "BENFORD_LAW": [
                "Phase 5: Pattern Detection",
                "Numerical anomaly detection",
            ],
            "OPTIONS_BACKDATING": [
                "Phase 5: Pattern Detection",
                "Executive compensation fraud",
            ],
            "CHANNEL_STUFFING": [
                "Phase 5: Pattern Detection",
                "Revenue manipulation detection",
            ],
            "XGBOOST_FRAUD": [
                "Phase 5: Pattern Detection",
                "ML-based fraud detection",
            ],
            "DEBERTA_CONTRADICTION": [
                "Phase 5: Pattern Detection",
                "Narrative contradiction detection",
            ],
            
            # Reporting
            "MARKDOWN_REPORTER": [
                "Phase 9: Dossier Generation",
            ],
            "JSON_REPORTER": [
                "Phase 9: Dossier Generation",
            ],
            "PDF_REPORTER": [
                "Phase 9: Dossier Generation",
            ],
            "COURT_PDF": [
                "Phase 9: Dossier Generation",
                "FRE 902 compliant output",
            ],
        }
    
    def get_impacted_components(self, failed_component: str) -> List[str]:
        """
        Get list of components that will be impacted if given component fails.
        
        Args:
            failed_component: Name of component that failed
            
        Returns:
            List of component names that depend on the failed component
        """
        return self.dependencies.get(failed_component, [])
    
    def calculate_failure_impact(self, failed_components: List[str]) -> Dict[str, List[str]]:
        """
        Calculate cascading impact of multiple component failures.
        
        Args:
            failed_components: List of failed component names
            
        Returns:
            Dictionary mapping each failed component to its impacted dependents
        """
        impact = {}
        
        for component in failed_components:
            impacted = self.get_impacted_components(component)
            if impacted:
                impact[component] = impacted
        
        return impact
    
    def find_dependency_chain(self, component: str) -> List[List[str]]:
        """
        Find all dependency chains from component to end users.
        
        Args:
            component: Component to analyze
            
        Returns:
            List of dependency chains (each chain is a list of component names)
        """
        chains = []
        
        def dfs(current: str, path: List[str]):
            """Depth-first search to find all paths."""
            dependents = self.dependencies.get(current, [])
            
            if not dependents:
                # Leaf node - end of chain
                chains.append(path + [current])
                return
            
            for dependent in dependents:
                if dependent not in path:  # Avoid cycles
                    dfs(dependent, path + [current])
        
        dfs(component, [])
        return chains
    
    def get_critical_components(self) -> List[str]:
        """
        Get list of critical components with the most dependents.
        
        Returns:
            List of component names sorted by number of dependents (descending)
        """
        component_impact = []
        
        for component, dependents in self.dependencies.items():
            # Calculate direct and transitive dependents
            all_dependents = set()
            queue = deque(dependents)
            
            while queue:
                dependent = queue.popleft()
                if dependent not in all_dependents:
                    all_dependents.add(dependent)
                    # Add transitive dependents
                    if dependent in self.dependencies:
                        queue.extend(self.dependencies[dependent])
            
            component_impact.append((component, len(all_dependents)))
        
        # Sort by impact (descending)
        component_impact.sort(key=lambda x: x[1], reverse=True)
        
        return [comp for comp, _ in component_impact if _ > 0]
    
    def is_critical(self, component: str, threshold: int = 3) -> bool:
        """
        Determine if component is critical based on number of dependents.
        
        Args:
            component: Component to check
            threshold: Minimum number of dependents to be considered critical
            
        Returns:
            True if component is critical
        """
        dependents = self.get_impacted_components(component)
        return len(dependents) >= threshold
    
    def generate_impact_report(self, failed_components: List[str]) -> str:
        """
        Generate human-readable impact report for failures.
        
        Args:
            failed_components: List of failed component names
            
        Returns:
            Formatted impact report
        """
        lines = [
            "=" * 80,
            "DEPENDENCY IMPACT ANALYSIS",
            "=" * 80,
            "",
        ]
        
        impact = self.calculate_failure_impact(failed_components)
        
        if not impact:
            lines.append("No dependency impact detected.")
            return "\n".join(lines)
        
        for component, dependents in impact.items():
            is_critical = self.is_critical(component)
            criticality = "🔴 CRITICAL" if is_critical else "🟡 NON-CRITICAL"
            
            lines.extend([
                f"{criticality} - {component}",
                f"  Impacts {len(dependents)} component(s):",
            ])
            
            for dependent in dependents:
                lines.append(f"    - {dependent}")
            
            lines.append("")
        
        # Summary
        total_impacted = sum(len(deps) for deps in impact.values())
        critical_count = sum(1 for comp in impact.keys() if self.is_critical(comp))
        
        lines.extend([
            "=" * 80,
            "SUMMARY",
            "=" * 80,
            f"Failed Components: {len(failed_components)}",
            f"Critical Failures: {critical_count}",
            f"Total Impacted Components: {total_impacted}",
            "",
        ])
        
        return "\n".join(lines)
