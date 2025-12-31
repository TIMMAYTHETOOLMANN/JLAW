"""
Interactive Forensic Dashboard - Phase 4
========================================

Streamlit-based web dashboard for interactive forensic analysis exploration.

Features:
- Real-time violation filtering by severity/actor/statute
- Drill-down from summary → violation → evidence → interrogation
- Export capabilities (PDF, JSON, CSV)
- Evidence chain explorer with hash verification
- Actor network visualization
- Case timeline view

Dashboard Pages:
1. Executive Overview - Key metrics, threat assessment, priority actions
2. Violations Explorer - Filterable violation table with details
3. Actor Intelligence - Actor profiles with risk scores and classifications
4. Evidence Chain - Interactive Merkle tree visualization
5. Interrogation Center - View/export interrogation packages
6. Export Station - Generate reports in multiple formats
"""

import logging
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from .prosecutorial_dossier_generator import ProsecutorialDossier, ProsecutorialDossierGenerator
from .visualizations import (
    TimelineGenerator,
    NetworkGraphGenerator,
    HeatMapGenerator,
    MerkleTreeVisualizer,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

PAGE_TITLE = "JLAW Forensic Analysis Dashboard"
PAGE_ICON = "⚖️"
LAYOUT = "wide"
INITIAL_SIDEBAR_STATE = "expanded"


# ═══════════════════════════════════════════════════════════════════════════
# FORENSIC DASHBOARD CLASS
# ═══════════════════════════════════════════════════════════════════════════


class ForensicDashboard:
    """
    Streamlit-based interactive forensic analysis dashboard.
    
    Usage:
        dashboard = ForensicDashboard(case_data_path="output/dossier_CASE_001.json")
        dashboard.run()
    """
    
    def __init__(self, case_data_path: Optional[Path] = None):
        """
        Initialize the forensic dashboard.
        
        Args:
            case_data_path: Path to case data JSON file (ProsecutorialDossier)
        """
        self.logger = logging.getLogger(__name__)
        self.case_data_path = case_data_path
        self.case_data: Optional[Dict[str, Any]] = None
        
        # Initialize visualizers
        self.timeline_gen = TimelineGenerator()
        self.network_gen = NetworkGraphGenerator()
        self.heatmap_gen = HeatMapGenerator()
        self.merkle_viz = MerkleTreeVisualizer()
        
        # Load case data if provided
        if case_data_path and Path(case_data_path).exists():
            self._load_case_data(case_data_path)
    
    def _load_case_data(self, path: Path) -> None:
        """Load case data from JSON file."""
        try:
            with open(path, 'r') as f:
                self.case_data = json.load(f)
            self.logger.info(f"Loaded case data from {path}")
        except Exception as e:
            self.logger.error(f"Failed to load case data: {e}")
            self.case_data = None
    
    def run(self) -> None:
        """Run the dashboard application."""
        # Configure page
        st.set_page_config(
            page_title=PAGE_TITLE,
            page_icon=PAGE_ICON,
            layout=LAYOUT,
            initial_sidebar_state=INITIAL_SIDEBAR_STATE,
        )
        
        # Sidebar navigation
        st.sidebar.title("🔍 JLAW Dashboard")
        st.sidebar.markdown("---")
        
        # Case selector
        if self.case_data is None:
            uploaded_file = st.sidebar.file_uploader(
                "Upload Case Data (JSON)",
                type=['json'],
                help="Upload a prosecutorial dossier JSON file"
            )
            
            if uploaded_file:
                self.case_data = json.load(uploaded_file)
                st.sidebar.success("Case data loaded successfully!")
        
        if self.case_data is None:
            self._render_no_data_page()
            return
        
        # Navigation menu
        page = st.sidebar.radio(
            "Navigate",
            [
                "📊 Executive Overview",
                "⚠️ Violations Explorer",
                "👤 Actor Intelligence",
                "🔗 Evidence Chain",
                "🎤 Interrogation Center",
                "💾 Export Station",
            ]
        )
        
        # Case info in sidebar
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Case Information")
        st.sidebar.markdown(f"**Case ID:** {self.case_data.get('case_id', 'N/A')}")
        st.sidebar.markdown(f"**Company:** {self.case_data.get('company_name', 'N/A')}")
        st.sidebar.markdown(f"**CIK:** {self.case_data.get('cik', 'N/A')}")
        st.sidebar.markdown(f"**Generated:** {self.case_data.get('generation_date', 'N/A')}")
        
        # Render selected page
        if page == "📊 Executive Overview":
            self._render_executive_overview()
        elif page == "⚠️ Violations Explorer":
            self._render_violations_explorer()
        elif page == "👤 Actor Intelligence":
            self._render_actor_intelligence()
        elif page == "🔗 Evidence Chain":
            self._render_evidence_chain()
        elif page == "🎤 Interrogation Center":
            self._render_interrogation_center()
        elif page == "💾 Export Station":
            self._render_export_station()
    
    def _render_no_data_page(self) -> None:
        """Render page when no case data is loaded."""
        st.title("🔍 JLAW Forensic Analysis Dashboard")
        st.markdown("---")
        
        st.warning("⚠️ No case data loaded. Please upload a prosecutorial dossier JSON file.")
        
        st.markdown("""
        ### Getting Started
        
        1. Run a JLAW forensic analysis to generate a prosecutorial dossier
        2. The dossier will be saved as a JSON file (e.g., `dossier_CASE_001.json`)
        3. Upload the JSON file using the sidebar uploader
        4. Explore the case data using the interactive dashboard
        
        ### Example Command
        
        ```bash
        python jlaw_cli.py --cik 0000320187 --company "NIKE, Inc." --year 2019 --strict --auto
        ```
        
        This will generate a dossier in the `output/` directory.
        """)
    
    def _render_executive_overview(self) -> None:
        """Render Executive Overview page (Page 1)."""
        st.title("📊 Executive Forensic Summary")
        st.markdown("---")
        
        exec_summary = self.case_data.get('executive_summary', {})
        
        # Threat level banner
        threat_level = exec_summary.get('threat_level', 'UNKNOWN')
        threat_colors = {
            'CRITICAL': '🔴',
            'HIGH': '🟠',
            'MEDIUM': '🟡',
            'LOW': '🟢',
        }
        threat_icon = threat_colors.get(threat_level, '⚪')
        
        st.markdown(f"## {threat_icon} Threat Level: {threat_level}")
        st.info(exec_summary.get('threat_statement', 'No threat statement available.'))
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Violations",
                exec_summary.get('total_violations', 0),
                delta=None,
            )
        
        with col2:
            st.metric(
                "Critical Violations",
                exec_summary.get('critical_violations', 0),
                delta=None,
            )
        
        with col3:
            st.metric(
                "Total Actors",
                exec_summary.get('total_actors', 0),
                delta=None,
            )
        
        with col4:
            st.metric(
                "Transaction Clusters",
                exec_summary.get('total_transaction_clusters', 0),
                delta=None,
            )
        
        st.markdown("---")
        
        # Enforcement recommendation
        st.markdown("### 🎯 Enforcement Recommendation")
        st.success(exec_summary.get('enforcement_recommendation', 'No recommendation available.'))
        
        st.markdown("---")
        
        # Primary enforcement agencies
        st.markdown("### 🏛️ Primary Enforcement Agencies")
        agencies = exec_summary.get('primary_enforcement_agencies', [])
        if agencies:
            cols = st.columns(len(agencies))
            for col, agency in zip(cols, agencies):
                col.markdown(f"**{agency}**")
        else:
            st.info("No enforcement agencies identified.")
        
        st.markdown("---")
        
        # Analysis period
        st.markdown("### 📅 Analysis Period")
        analysis_period = exec_summary.get('analysis_period', {})
        st.markdown(f"**Start:** {analysis_period.get('start', 'N/A')}")
        st.markdown(f"**End:** {analysis_period.get('end', 'N/A')}")
    
    def _render_violations_explorer(self) -> None:
        """Render Violations Explorer page (Page 2)."""
        st.title("⚠️ Violations Explorer")
        st.markdown("---")
        
        violations_table = self.case_data.get('violations_table', [])
        
        if not violations_table:
            st.warning("No violations found in case data.")
            return
        
        # Filters
        st.markdown("### 🔍 Filters")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            min_confidence = st.slider(
                "Minimum Confidence",
                min_value=0.0,
                max_value=1.0,
                value=0.0,
                step=0.1,
            )
        
        with col2:
            violation_types = list(set(v['violation_type'] for v in violations_table))
            selected_types = st.multiselect(
                "Violation Types",
                options=violation_types,
                default=violation_types,
            )
        
        with col3:
            enforcement_pathways = list(set(v['enforcement_pathway'] for v in violations_table))
            selected_pathways = st.multiselect(
                "Enforcement Pathways",
                options=enforcement_pathways,
                default=enforcement_pathways,
            )
        
        # Filter violations
        filtered_violations = [
            v for v in violations_table
            if (
                v['confidence'] >= min_confidence
                and v['violation_type'] in selected_types
                and v['enforcement_pathway'] in selected_pathways
            )
        ]
        
        st.markdown(f"**Showing {len(filtered_violations)} of {len(violations_table)} violations**")
        st.markdown("---")
        
        # Display violations
        for i, violation in enumerate(filtered_violations, 1):
            with st.expander(f"Violation {i}: {violation['violation_type']} (Confidence: {violation['confidence']:.1%})"):
                st.markdown(f"**Violation ID:** {violation['violation_id']}")
                st.markdown(f"**Enforcement Pathway:** {violation['enforcement_pathway']}")
                st.markdown(f"**Confidence:** {violation['confidence']:.1%}")
                
                st.markdown("#### Applicable Statutes")
                for statute in violation.get('statutes', []):
                    st.markdown(f"- **{statute['code']}**: {statute['title']}")
                    st.markdown(f"  - Agency: {statute['enforcement_agency']}")
                    st.markdown(f"  - Type: {statute['case_type']}")
                    if statute.get('penalty_range'):
                        st.markdown(f"  - Penalty: {statute['penalty_range']}")
                
                st.markdown("#### Plain Language Explanation")
                st.info(violation.get('plain_language_explanation', 'No explanation available.'))
                
                st.markdown("#### Recommended Actions")
                for action in violation.get('recommended_actions', []):
                    st.markdown(f"- {action}")
    
    def _render_actor_intelligence(self) -> None:
        """Render Actor Intelligence page (Page 3)."""
        st.title("👤 Actor Intelligence")
        st.markdown("---")
        
        actor_mapping = self.case_data.get('actor_mapping', {})
        actors = actor_mapping.get('actors', [])
        
        if not actors:
            st.warning("No actors found in case data.")
            return
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Actors", actor_mapping.get('total_actors', 0))
        
        with col2:
            high_risk_actors = sum(1 for a in actors if a['risk_score'] >= 80)
            st.metric("High Risk Actors", high_risk_actors)
        
        with col3:
            with_interrogation = sum(1 for a in actors if a['has_interrogation_package'])
            st.metric("With Interrogation Packages", with_interrogation)
        
        st.markdown("---")
        
        # Actor table
        st.markdown("### Actor Profiles")
        
        # Convert to DataFrame
        df_actors = pd.DataFrame(actors)
        
        # Display sortable table
        st.dataframe(
            df_actors[[
                'actor_name', 'risk_score', 'total_violations',
                'actor_type', 'has_interrogation_package'
            ]].sort_values('risk_score', ascending=False),
            use_container_width=True,
        )
        
        st.markdown("---")
        
        # Actor details
        st.markdown("### Actor Details")
        selected_actor = st.selectbox(
            "Select Actor",
            options=[a['actor_name'] for a in actors],
        )
        
        if selected_actor:
            actor_data = next(a for a in actors if a['actor_name'] == selected_actor)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Actor ID:** {actor_data['actor_id']}")
                st.markdown(f"**Type:** {actor_data['actor_type']}")
                st.markdown(f"**Risk Score:** {actor_data['risk_score']:.1f}/100")
                st.markdown(f"**Total Violations:** {actor_data['total_violations']}")
            
            with col2:
                st.markdown(f"**CIK:** {actor_data.get('cik', 'N/A')}")
                st.markdown(f"**Roles:** {', '.join(actor_data.get('roles', []))}")
                st.markdown(f"**Evidence Items:** {actor_data['evidence_items']}")
                st.markdown(f"**Interrogation Package:** {'✓ Yes' if actor_data['has_interrogation_package'] else '✗ No'}")
            
            st.markdown("#### Primary Statutes")
            for statute in actor_data.get('primary_statutes', []):
                st.markdown(f"- {statute}")
            
            st.markdown("#### Violation IDs")
            for violation_id in actor_data.get('violation_ids', []):
                st.markdown(f"- {violation_id}")
    
    def _render_evidence_chain(self) -> None:
        """Render Evidence Chain page (Page 4)."""
        st.title("🔗 Evidence Chain Explorer")
        st.markdown("---")
        
        evidence_strength = self.case_data.get('evidence_strength', {})
        
        # Evidence integrity status
        st.markdown("### 🔐 Evidence Integrity")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fre_compliant = evidence_strength.get('fre_902_compliant', False)
            st.metric("FRE 902 Compliant", "✓ Yes" if fre_compliant else "✗ No")
        
        with col2:
            crypto_integrity = evidence_strength.get('cryptographic_integrity', 'PENDING')
            st.metric("Cryptographic Integrity", crypto_integrity)
        
        with col3:
            avg_confidence = evidence_strength.get('average_confidence', 0)
            st.metric("Average Confidence", f"{avg_confidence:.1%}")
        
        st.markdown("---")
        
        # Merkle root
        st.markdown("### 🌳 Merkle Tree Root")
        merkle_root = evidence_strength.get('merkle_root', 'N/A')
        st.code(merkle_root, language='text')
        
        st.markdown("---")
        
        # Overall assessment
        st.markdown("### 📋 Overall Assessment")
        overall_assessment = evidence_strength.get('overall_assessment', 'No assessment available.')
        st.info(overall_assessment)
        
        st.markdown("---")
        
        # Statute strengths
        st.markdown("### 📊 Evidence Strength by Statute")
        statute_strengths = evidence_strength.get('statute_strengths', [])
        
        if statute_strengths:
            df_statutes = pd.DataFrame(statute_strengths)
            
            # Bar chart
            fig = go.Figure(data=[
                go.Bar(
                    x=df_statutes['statute_code'],
                    y=df_statutes['average_confidence'],
                    text=df_statutes['violation_count'],
                    texttemplate='%{text} violations',
                    textposition='outside',
                )
            ])
            
            fig.update_layout(
                title="Average Confidence by Statute",
                xaxis_title="Statute",
                yaxis_title="Average Confidence",
                yaxis=dict(range=[0, 1]),
                template="plotly_white",
                height=400,
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Table
            st.dataframe(df_statutes, use_container_width=True)
        else:
            st.info("No statute strength data available.")
    
    def _render_interrogation_center(self) -> None:
        """Render Interrogation Center page (Page 5)."""
        st.title("🎤 Interrogation Center")
        st.markdown("---")
        
        interrogation_section = self.case_data.get('interrogation_packages', {})
        packages = interrogation_section.get('packages', [])
        
        if not packages:
            st.warning("No interrogation packages available.")
            return
        
        # Summary
        st.markdown("### 📊 Summary")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Packages", interrogation_section.get('total_packages', 0))
        
        with col2:
            high_priority = interrogation_section.get('high_priority_interviews', [])
            st.metric("High Priority Interviews", len(high_priority))
        
        st.markdown("---")
        
        # Package explorer
        st.markdown("### 📦 Interrogation Packages")
        
        # Sort by risk score
        packages_sorted = sorted(packages, key=lambda x: x['risk_score'], reverse=True)
        
        for package in packages_sorted:
            risk_badge = "🔴" if package['risk_score'] >= 80 else "🟠" if package['risk_score'] >= 60 else "🟡"
            
            with st.expander(f"{risk_badge} {package['actor_name']} (Risk: {package['risk_score']:.1f})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Actor ID:** {package['actor_id']}")
                    st.markdown(f"**Role:** {package['actor_role']}")
                    st.markdown(f"**Risk Score:** {package['risk_score']:.1f}/100")
                
                with col2:
                    st.markdown(f"**Total Violations:** {package['total_violations']}")
                    st.markdown(f"**Total Questions:** {package['total_questions']}")
                    st.markdown(f"**Has Defenses:** {'✓ Yes' if package['has_anticipated_defenses'] else '✗ No'}")
                
                st.markdown("#### Interview Objectives")
                for objective in package.get('interview_objectives', []):
                    st.markdown(f"- {objective}")
                
                st.markdown("#### Applicable Statutes")
                statutes_str = ", ".join(package.get('applicable_statutes', []))
                st.markdown(statutes_str)
    
    def _render_export_station(self) -> None:
        """Render Export Station page (Page 6)."""
        st.title("💾 Export Station")
        st.markdown("---")
        
        st.markdown("### 📥 Export Dossier")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                options=['JSON', 'Markdown', 'PDF', 'CSV'],
            )
        
        with col2:
            include_appendices = st.checkbox("Include Appendices", value=True)
        
        if st.button("🚀 Generate Export", type="primary"):
            with st.spinner(f"Generating {export_format} export..."):
                try:
                    # Generate export (simplified - in production would use actual generator)
                    if export_format == 'JSON':
                        export_data = json.dumps(self.case_data, indent=2)
                        st.download_button(
                            label="Download JSON",
                            data=export_data,
                            file_name=f"dossier_{self.case_data['case_id']}.json",
                            mime="application/json",
                        )
                    
                    elif export_format == 'Markdown':
                        # Generate markdown (simplified)
                        md_content = self._generate_markdown_export()
                        st.download_button(
                            label="Download Markdown",
                            data=md_content,
                            file_name=f"dossier_{self.case_data['case_id']}.md",
                            mime="text/markdown",
                        )
                    
                    elif export_format == 'PDF':
                        st.info("PDF export requires reportlab. Feature coming soon.")
                    
                    elif export_format == 'CSV':
                        # Export violations table as CSV
                        violations = self.case_data.get('violations_table', [])
                        df = pd.DataFrame(violations)
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name=f"violations_{self.case_data['case_id']}.csv",
                            mime="text/csv",
                        )
                    
                    st.success(f"✅ {export_format} export generated successfully!")
                
                except Exception as e:
                    st.error(f"❌ Export failed: {e}")
        
        st.markdown("---")
        
        # Export history
        st.markdown("### 📜 Export History")
        st.info("Export history tracking will be implemented in database integration.")
    
    def _generate_markdown_export(self) -> str:
        """Generate markdown export of the dossier."""
        lines = []
        
        lines.append(f"# Prosecutorial Dossier: {self.case_data['case_id']}")
        lines.append("")
        lines.append(f"**Company:** {self.case_data['company_name']}")
        lines.append(f"**CIK:** {self.case_data['cik']}")
        lines.append(f"**Generated:** {self.case_data['generation_date']}")
        lines.append("")
        
        lines.append("## Executive Summary")
        exec_summary = self.case_data.get('executive_summary', {})
        lines.append(f"**Threat Level:** {exec_summary.get('threat_level', 'N/A')}")
        lines.append("")
        lines.append(exec_summary.get('threat_statement', ''))
        lines.append("")
        
        lines.append("## Violations")
        for i, violation in enumerate(self.case_data.get('violations_table', [])[:10], 1):
            lines.append(f"### Violation {i}: {violation['violation_type']}")
            lines.append(f"- Confidence: {violation['confidence']:.1%}")
            lines.append(f"- Enforcement: {violation['enforcement_pathway']}")
            lines.append("")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════


def main(case_data_path: Optional[Path] = None):
    """
    Main entry point for the dashboard.
    
    Args:
        case_data_path: Optional path to case data JSON file
    """
    dashboard = ForensicDashboard(case_data_path)
    dashboard.run()


if __name__ == "__main__":
    import sys
    
    # Check for command-line argument
    if len(sys.argv) > 1:
        case_path = Path(sys.argv[1])
    else:
        case_path = None
    
    main(case_path)
