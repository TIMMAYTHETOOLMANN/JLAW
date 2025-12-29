"""
Timeline Visualizer
===================

Generates execution timeline data for visualization of agent execution
patterns, parallelization opportunities, and performance bottlenecks.

Features:
- Generate timeline data in Gantt chart format
- Track phase and agent execution overlaps
- Identify parallelization opportunities
- Export timeline JSON for visualization tools

Usage:
    from src.profiling import PerformanceMetricsCollector, TimelineVisualizer
    
    # After collecting metrics
    visualizer = TimelineVisualizer()
    timeline = visualizer.generate_timeline(metrics_collector)
    
    # Export to JSON
    visualizer.export_json(timeline, Path("output/timeline.json"))
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

from .performance_metrics import PerformanceMetricsCollector

logger = logging.getLogger(__name__)


class TimelineVisualizer:
    """
    Generate execution timeline for visualization.
    
    Creates timeline data in a format suitable for Gantt charts
    and other visualization tools.
    """
    
    def __init__(self):
        """Initialize timeline visualizer."""
        logger.debug("TimelineVisualizer initialized")
    
    def generate_timeline(
        self,
        metrics: PerformanceMetricsCollector
    ) -> Dict[str, Any]:
        """
        Generate timeline data in Gantt chart format.
        
        Args:
            metrics: PerformanceMetricsCollector with collected metrics
            
        Returns:
            Dictionary with timeline data for visualization
        """
        if not metrics.agent_metrics:
            logger.warning("No agent metrics available for timeline generation")
            return {
                "investigation_id": metrics.investigation_id,
                "total_duration": 0.0,
                "phases": [],
                "agents": [],
                "parallelization_opportunities": []
            }
        
        base_time = metrics.start_time
        
        # Generate phase timeline
        phases = []
        for phase in metrics.phase_metrics:
            phases.append({
                "name": phase.phase_name,
                "start": round(phase.start_time - base_time, 3),
                "end": round(
                    (phase.end_time if phase.end_time else phase.start_time) - base_time,
                    3
                ),
                "duration": round(phase.duration_seconds, 3),
                "status": phase.status,
                "agents_count": len(phase.agent_metrics),
                "total_cost": round(phase.total_cost, 4)
            })
        
        # Generate agent timeline
        agents = []
        for agent in metrics.agent_metrics:
            agents.append({
                "name": agent.agent_name,
                "type": agent.agent_type,
                "tier": agent.tier,
                "start": round(agent.start_time - base_time, 3),
                "end": round(
                    (agent.end_time if agent.end_time else agent.start_time) - base_time,
                    3
                ),
                "duration": round(agent.duration_seconds, 3),
                "tokens": agent.total_tokens,
                "cost": round(agent.total_cost, 4),
                "violations": agent.violations_found,
                "status": agent.status
            })
        
        # Identify parallelization opportunities
        parallelization_opportunities = self._identify_parallelization_opportunities(
            metrics
        )
        
        # Calculate execution overlap
        overlap_analysis = self._analyze_execution_overlap(metrics)
        
        return {
            "investigation_id": metrics.investigation_id,
            "total_duration": round(
                max((a.end_time or a.start_time) for a in metrics.agent_metrics) - base_time,
                3
            ) if metrics.agent_metrics else 0.0,
            "phases": phases,
            "agents": agents,
            "parallelization_opportunities": parallelization_opportunities,
            "overlap_analysis": overlap_analysis
        }
    
    def _identify_parallelization_opportunities(
        self,
        metrics: PerformanceMetricsCollector
    ) -> List[Dict[str, Any]]:
        """
        Identify agents that could be parallelized.
        
        Looks for:
        - Agents in same tier that ran sequentially
        - Agents with no apparent dependencies
        
        Args:
            metrics: Performance metrics collector
            
        Returns:
            List of parallelization opportunities
        """
        opportunities = []
        
        # Group agents by tier
        agents_by_tier: Dict[str, List] = {}
        for agent in metrics.agent_metrics:
            tier = agent.tier or "unknown"
            if tier not in agents_by_tier:
                agents_by_tier[tier] = []
            agents_by_tier[tier].append(agent)
        
        # Check for sequential execution within tiers
        for tier, agents in agents_by_tier.items():
            if len(agents) < 2:
                continue
            
            # Sort by start time
            sorted_agents = sorted(agents, key=lambda a: a.start_time)
            
            # Find agents that ran sequentially (no overlap)
            sequential_groups = []
            current_group = [sorted_agents[0]]
            
            for i in range(1, len(sorted_agents)):
                prev_agent = sorted_agents[i-1]
                curr_agent = sorted_agents[i]
                
                # Check if current agent started after previous ended
                prev_end = prev_agent.end_time or prev_agent.start_time
                if curr_agent.start_time >= prev_end:
                    current_group.append(curr_agent)
                else:
                    # Overlap detected, start new group
                    if len(current_group) >= 2:
                        sequential_groups.append(current_group)
                    current_group = [curr_agent]
            
            # Add last group
            if len(current_group) >= 2:
                sequential_groups.append(current_group)
            
            # Report opportunities
            for group in sequential_groups:
                total_time = sum(a.duration_seconds for a in group)
                potential_time = max(a.duration_seconds for a in group)
                time_savings = total_time - potential_time
                
                if time_savings > 5.0:  # Only report if >5 seconds savings
                    opportunities.append({
                        "tier": tier,
                        "agents": [a.agent_name for a in group],
                        "current_time": round(total_time, 2),
                        "parallel_time": round(potential_time, 2),
                        "time_savings": round(time_savings, 2),
                        "savings_percentage": round(
                            (time_savings / total_time) * 100, 1
                        )
                    })
        
        return opportunities
    
    def _analyze_execution_overlap(
        self,
        metrics: PerformanceMetricsCollector
    ) -> Dict[str, Any]:
        """
        Analyze how much agent execution overlapped.
        
        Args:
            metrics: Performance metrics collector
            
        Returns:
            Dictionary with overlap analysis
        """
        if not metrics.agent_metrics:
            return {
                "total_agent_time": 0.0,
                "actual_wall_time": 0.0,
                "parallelization_factor": 1.0,
                "overlap_percentage": 0.0
            }
        
        # Calculate total agent execution time (sum of all durations)
        total_agent_time = sum(a.duration_seconds for a in metrics.agent_metrics)
        
        # Calculate actual wall time (min start to max end)
        min_start = min(a.start_time for a in metrics.agent_metrics)
        max_end = max(
            (a.end_time if a.end_time else a.start_time)
            for a in metrics.agent_metrics
        )
        actual_wall_time = max_end - min_start
        
        # Calculate parallelization factor
        parallelization_factor = (
            total_agent_time / actual_wall_time
            if actual_wall_time > 0 else 1.0
        )
        
        # Calculate overlap percentage
        # (how much time was saved by parallel execution)
        time_saved = total_agent_time - actual_wall_time
        overlap_percentage = (
            (time_saved / total_agent_time) * 100
            if total_agent_time > 0 else 0.0
        )
        
        return {
            "total_agent_time": round(total_agent_time, 2),
            "actual_wall_time": round(actual_wall_time, 2),
            "parallelization_factor": round(parallelization_factor, 2),
            "overlap_percentage": round(overlap_percentage, 1)
        }
    
    def export_json(
        self,
        timeline: Dict[str, Any],
        output_path: Path
    ):
        """
        Export timeline to JSON file.
        
        Args:
            timeline: Timeline dictionary from generate_timeline()
            output_path: Path for output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(timeline, f, indent=2)
        
        logger.info(f"Exported timeline to {output_path}")
    
    def generate_gantt_html(
        self,
        timeline: Dict[str, Any],
        output_path: Path
    ):
        """
        Generate simple HTML Gantt chart visualization.
        
        Args:
            timeline: Timeline dictionary from generate_timeline()
            output_path: Path for output HTML file
        """
        # Simple HTML template with inline CSS
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>JLAW Execution Timeline - {investigation_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .timeline {{ margin-top: 20px; }}
        .phase {{ 
            background: #e3f2fd; 
            border-left: 4px solid #2196f3;
            padding: 10px;
            margin: 10px 0;
        }}
        .agent {{ 
            background: #f5f5f5; 
            border-left: 4px solid #4caf50;
            padding: 8px;
            margin: 5px 0 5px 20px;
            font-size: 14px;
        }}
        .metrics {{ color: #666; font-size: 12px; }}
        .opportunity {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <h1>JLAW Execution Timeline</h1>
    <p><strong>Investigation ID:</strong> {investigation_id}</p>
    <p><strong>Total Duration:</strong> {total_duration}s</p>
    
    <h2>Phases</h2>
    <div class="timeline">
        {phases_html}
    </div>
    
    <h2>Parallelization Opportunities</h2>
    {opportunities_html}
</body>
</html>
"""
        
        # Generate phases HTML
        phases_html = ""
        for phase in timeline["phases"]:
            phases_html += f"""
        <div class="phase">
            <strong>{phase['name']}</strong><br>
            <span class="metrics">
                Duration: {phase['duration']}s | 
                Agents: {phase['agents_count']} | 
                Cost: ${phase['total_cost']}
            </span>
        </div>
"""
        
        # Generate opportunities HTML
        opportunities_html = ""
        if timeline.get("parallelization_opportunities"):
            for opp in timeline["parallelization_opportunities"]:
                opportunities_html += f"""
        <div class="opportunity">
            <strong>Tier: {opp['tier']}</strong><br>
            Agents: {', '.join(opp['agents'])}<br>
            <span class="metrics">
                Current: {opp['current_time']}s → 
                Parallel: {opp['parallel_time']}s 
                (Save: {opp['time_savings']}s, {opp['savings_percentage']}%)
            </span>
        </div>
"""
        else:
            opportunities_html = "<p>No parallelization opportunities identified.</p>"
        
        # Fill template
        html_content = html_template.format(
            investigation_id=timeline["investigation_id"],
            total_duration=timeline["total_duration"],
            phases_html=phases_html,
            opportunities_html=opportunities_html
        )
        
        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Exported Gantt chart HTML to {output_path}")
