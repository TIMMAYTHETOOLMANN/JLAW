"""
Financial Network Mapper
========================

Generates multi-layer financial network visualisations showing:
- Beneficial ownership chains (who ultimately controls what)
- Capital flow maps (who paid whom, amounts, direction)
- Board interlock networks (common board members across companies)
- Insider cluster maps (who transacted in coordinated windows)
- Shell / nominee ownership chains
- Cross-company relationship webs

Uses networkx for graph construction and plotly for rich interactive outputs.
Also exports static PNG via matplotlib for PDF embedding.

Output formats:
- Plotly interactive HTML
- Static PNG (matplotlib)
- Structured JSON edge/node list
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import networkx as nx
    _NX_AVAILABLE = True
except ImportError:
    _NX_AVAILABLE = False

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _PLOTLY_AVAILABLE = True
except ImportError:
    _PLOTLY_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np
    _MPL_AVAILABLE = True
except ImportError:
    _MPL_AVAILABLE = False

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# DATA MODELS
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class NetworkNode:
    """A node in the financial network."""
    node_id: str
    label: str
    node_type: str          # INDIVIDUAL | CORPORATION | FUND | TRUST | REGULATOR
    risk_score: float = 0.0
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NetworkEdge:
    """A directed edge representing a relationship or capital flow."""
    source_id: str
    target_id: str
    edge_type: str          # OWNERSHIP | BOARD_SEAT | TRANSACTION | REPORTS_TO | CONTROLS
    weight: float = 1.0     # Transaction volume or ownership percentage
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FinancialNetworkData:
    """
    Complete network data structure ready for visualisation.

    Produced by FinancialNetworkMapper and consumed by the visualisation layer.
    """
    network_id: str
    company_name: str
    cik: str
    analysis_period: str
    generated_at: str

    nodes: List[NetworkNode] = field(default_factory=list)
    edges: List[NetworkEdge] = field(default_factory=list)

    # Derived metrics
    density: float = 0.0
    avg_degree: float = 0.0
    max_degree_node: str = ""
    hub_nodes: List[str] = field(default_factory=list)  # High-centrality actors
    cluster_count: int = 0
    risk_clusters: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "network_id": self.network_id,
            "company_name": self.company_name,
            "cik": self.cik,
            "analysis_period": self.analysis_period,
            "generated_at": self.generated_at,
            "metrics": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "density": self.density,
                "avg_degree": self.avg_degree,
                "max_degree_node": self.max_degree_node,
                "hub_nodes": self.hub_nodes,
                "cluster_count": self.cluster_count,
            },
            "nodes": [asdict(n) for n in self.nodes],
            "edges": [asdict(e) for e in self.edges],
            "risk_clusters": self.risk_clusters,
        }


# ═══════════════════════════════════════════════════════════════════════════
# MAPPER
# ═══════════════════════════════════════════════════════════════════════════


class FinancialNetworkMapper:
    """
    Builds and visualises financial relationship networks from forensic data.

    Usage::

        mapper = FinancialNetworkMapper()
        net = mapper.build_network(
            company_name="NIKE, Inc.",
            cik="320187",
            analysis_results=analysis_results_dict,
        )
        mapper.export_interactive_html(net, output_dir / "network_map.html")
        mapper.export_static_png(net, output_dir / "network_map.png")
        mapper.export_json(net, output_dir / "network_map.json")
    """

    # Node type colours
    _NODE_COLORS: Dict[str, str] = {
        "INDIVIDUAL": "#4A90D9",
        "CORPORATION": "#E74C3C",
        "FUND": "#9B59B6",
        "TRUST": "#F39C12",
        "REGULATOR": "#27AE60",
        "UNKNOWN": "#95A5A6",
    }

    # Edge type colours
    _EDGE_COLORS: Dict[str, str] = {
        "OWNERSHIP": "#E74C3C",
        "BOARD_SEAT": "#2980B9",
        "TRANSACTION": "#F39C12",
        "REPORTS_TO": "#95A5A6",
        "CONTROLS": "#8E44AD",
        "UNKNOWN": "#BDC3C7",
    }

    # Risk score → bubble size multiplier
    _RISK_SIZE_BASE = 15
    _RISK_SIZE_SCALE = 0.5

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    # ── public API ──────────────────────────────────────────────────────────

    def build_network(
        self,
        company_name: str,
        cik: str,
        analysis_results: Dict[str, Any],
        analysis_period: str = "",
    ) -> FinancialNetworkData:
        """
        Build a FinancialNetworkData structure from forensic analysis results.

        Args:
            company_name: Company display name.
            cik: SEC CIK.
            analysis_results: Full forensic analysis results dict.
            analysis_period: Period label.

        Returns:
            FinancialNetworkData ready for visualisation or export.
        """
        import hashlib

        network_id = hashlib.sha256(
            f"{cik}{company_name}{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16].upper()

        net = FinancialNetworkData(
            network_id=network_id,
            company_name=company_name,
            cik=cik,
            analysis_period=analysis_period or "N/A",
            generated_at=datetime.utcnow().isoformat() + "Z",
        )

        # Add the target company as central node
        company_node = NetworkNode(
            node_id=f"CORP_{cik}",
            label=company_name,
            node_type="CORPORATION",
            risk_score=self._company_risk_score(analysis_results),
        )
        net.nodes.append(company_node)

        # Add insider nodes
        self._add_insider_nodes(net, analysis_results, cik)

        # Add relationship edges
        self._add_insider_edges(net, analysis_results, cik)

        # Add beneficiary edges
        self._add_beneficiary_edges(net, analysis_results, cik)

        # Add actor relationship edges
        self._add_actor_relationship_edges(net, analysis_results)

        # Compute network metrics
        if _NX_AVAILABLE:
            self._compute_metrics(net)

        self.logger.info(
            "Network built: %d nodes, %d edges",
            len(net.nodes),
            len(net.edges),
        )
        return net

    def export_interactive_html(
        self, net: FinancialNetworkData, path: Path
    ) -> Optional[Path]:
        """Export network as interactive Plotly HTML."""
        if not _PLOTLY_AVAILABLE or not _NX_AVAILABLE:
            self.logger.warning(
                "plotly/networkx not available; skipping interactive HTML export"
            )
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        fig = self._build_plotly_figure(net)
        fig.write_html(str(path), include_plotlyjs="cdn")
        self.logger.info("Financial network HTML → %s", path)
        return path

    def export_static_png(
        self, net: FinancialNetworkData, path: Path
    ) -> Optional[Path]:
        """Export network as static PNG using matplotlib."""
        if not _MPL_AVAILABLE or not _NX_AVAILABLE:
            self.logger.warning(
                "matplotlib/networkx not available; skipping PNG export"
            )
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        self._build_matplotlib_figure(net, path)
        self.logger.info("Financial network PNG → %s", path)
        return path

    def export_json(self, net: FinancialNetworkData, path: Path) -> Path:
        """Export network data as JSON."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(net.to_dict(), fh, indent=2, default=str)
        self.logger.info("Financial network JSON → %s", path)
        return path

    # ── internal builders ────────────────────────────────────────────────────

    def _company_risk_score(self, analysis_results: Dict[str, Any]) -> float:
        """Compute a composite risk score for the company node."""
        n_critical = analysis_results.get("critical_alerts", 0)
        n_high = analysis_results.get("high_alerts", 0)
        n_total = analysis_results.get("total_violations", 0)
        score = min(100.0, (n_critical * 20 + n_high * 10 + n_total * 0.5))
        return round(score, 1)

    def _add_insider_nodes(
        self,
        net: FinancialNetworkData,
        analysis_results: Dict[str, Any],
        cik: str,
    ) -> None:
        """Add individual insider/actor nodes."""
        existing_ids = {n.node_id for n in net.nodes}

        # From actors list
        for actor in analysis_results.get("actors", []):
            node_id = f"ACTOR_{actor.get('actor_id', actor.get('name', 'UNK'))}"
            if node_id in existing_ids:
                continue
            net.nodes.append(
                NetworkNode(
                    node_id=node_id,
                    label=actor.get("name", "Unknown"),
                    node_type="INDIVIDUAL",
                    risk_score=float(actor.get("risk_score", 0)),
                    attributes={
                        "roles": actor.get("roles", []),
                        "actor_type": actor.get("actor_type", ""),
                    },
                )
            )
            existing_ids.add(node_id)

        # From violations (owners not already in actors list)
        violations = analysis_results.get("violations", [])
        for v in violations:
            name = v.get("reporting_owner") or v.get("actor") or ""
            if not name:
                continue
            node_id = f"INSIDER_{name.replace(' ', '_').upper()[:20]}"
            if node_id in existing_ids:
                continue
            penalty = v.get("estimated_penalty", 0)
            net.nodes.append(
                NetworkNode(
                    node_id=node_id,
                    label=name,
                    node_type="INDIVIDUAL",
                    risk_score=min(100.0, penalty / 1000),
                    attributes={"first_violation_type": v.get("type", "")},
                )
            )
            existing_ids.add(node_id)

        # From beneficiaries
        for b in analysis_results.get("beneficiaries", []):
            name = b.get("name", "")
            if not name:
                continue
            node_id = f"BENEF_{name.replace(' ', '_').upper()[:20]}"
            if node_id in existing_ids:
                continue
            net.nodes.append(
                NetworkNode(
                    node_id=node_id,
                    label=name,
                    node_type="INDIVIDUAL",
                    risk_score=float(b.get("risk_score", 0)),
                    attributes={
                        "role": b.get("role", ""),
                        "total_profit": b.get("total_profit", 0),
                    },
                )
            )
            existing_ids.add(node_id)

    def _add_insider_edges(
        self,
        net: FinancialNetworkData,
        analysis_results: Dict[str, Any],
        cik: str,
    ) -> None:
        """Add REPORTS_TO and TRANSACTION edges from insiders to company."""
        company_node_id = f"CORP_{cik}"
        existing_node_ids = {n.node_id for n in net.nodes}

        violations = analysis_results.get("violations", [])
        seen_edges: set = set()

        for v in violations:
            name = v.get("reporting_owner") or v.get("actor") or ""
            if not name:
                continue
            insider_id = f"INSIDER_{name.replace(' ', '_').upper()[:20]}"
            if insider_id not in existing_node_ids:
                insider_id = next(
                    (n.node_id for n in net.nodes if n.label == name),
                    None,
                )
            if not insider_id:
                continue

            edge_key = (insider_id, company_node_id, "REPORTS_TO")
            if edge_key not in seen_edges:
                net.edges.append(
                    NetworkEdge(
                        source_id=insider_id,
                        target_id=company_node_id,
                        edge_type="REPORTS_TO",
                        weight=1.0,
                    )
                )
                seen_edges.add(edge_key)

            # Transaction edge (insider → company or company → insider)
            tx_key = (insider_id, company_node_id, "TRANSACTION")
            if tx_key not in seen_edges:
                shares = float(v.get("shares", 0) or 0)
                net.edges.append(
                    NetworkEdge(
                        source_id=insider_id,
                        target_id=company_node_id,
                        edge_type="TRANSACTION",
                        weight=shares,
                        attributes={
                            "violation_type": v.get("type", ""),
                            "accession_number": v.get("accession_number", ""),
                        },
                    )
                )
                seen_edges.add(tx_key)

    def _add_beneficiary_edges(
        self,
        net: FinancialNetworkData,
        analysis_results: Dict[str, Any],
        cik: str,
    ) -> None:
        """Add OWNERSHIP / control edges for beneficiaries."""
        company_node_id = f"CORP_{cik}"
        existing_node_ids = {n.node_id for n in net.nodes}

        for b in analysis_results.get("beneficiaries", []):
            name = b.get("name", "")
            if not name:
                continue
            node_id = f"BENEF_{name.replace(' ', '_').upper()[:20]}"
            if node_id not in existing_node_ids:
                continue
            profit = float(b.get("total_profit", 0) or 0)
            net.edges.append(
                NetworkEdge(
                    source_id=node_id,
                    target_id=company_node_id,
                    edge_type="OWNERSHIP",
                    weight=max(profit / 1_000_000, 0.1),
                    attributes={"profit_usd": profit, "role": b.get("role", "")},
                )
            )

    def _add_actor_relationship_edges(
        self,
        net: FinancialNetworkData,
        analysis_results: Dict[str, Any],
    ) -> None:
        """Add relationships from the analysis_results relationships list."""
        existing_node_ids = {n.node_id for n in net.nodes}

        for rel in analysis_results.get("relationships", []):
            src = rel.get("source", "")
            tgt = rel.get("target", "")
            if not src or not tgt:
                continue

            # Try to match to existing node IDs by label
            src_id = next(
                (n.node_id for n in net.nodes if n.label == src or n.node_id == src),
                None,
            )
            tgt_id = next(
                (n.node_id for n in net.nodes if n.label == tgt or n.node_id == tgt),
                None,
            )
            if not src_id or not tgt_id:
                continue

            net.edges.append(
                NetworkEdge(
                    source_id=src_id,
                    target_id=tgt_id,
                    edge_type=rel.get("relationship_type", "UNKNOWN"),
                    weight=float(rel.get("strength", 1.0)),
                    attributes=rel,
                )
            )

    def _compute_metrics(self, net: FinancialNetworkData) -> None:
        """Compute graph-theoretic metrics using networkx."""
        if not _NX_AVAILABLE:
            return

        G = nx.DiGraph()
        for node in net.nodes:
            G.add_node(node.node_id, **asdict(node))
        for edge in net.edges:
            G.add_edge(edge.source_id, edge.target_id, weight=edge.weight)

        if G.number_of_nodes() == 0:
            return

        net.density = round(nx.density(G), 4)

        degrees = dict(G.degree())
        if degrees:
            avg = sum(degrees.values()) / len(degrees)
            net.avg_degree = round(avg, 2)
            net.max_degree_node = max(degrees, key=degrees.get)

        # Hub nodes: top 20% by degree
        sorted_nodes = sorted(degrees, key=degrees.get, reverse=True)
        top_n = max(1, len(sorted_nodes) // 5)
        net.hub_nodes = sorted_nodes[:top_n]

        # Weakly connected components as risk clusters
        clusters = list(nx.weakly_connected_components(G))
        net.cluster_count = len(clusters)
        net.risk_clusters = [list(c) for c in clusters if len(c) > 1]

    # ── plotly visualisation ─────────────────────────────────────────────────

    def _build_plotly_figure(self, net: FinancialNetworkData) -> "go.Figure":
        """Build a rich interactive Plotly network figure."""
        G = nx.DiGraph()
        for node in net.nodes:
            G.add_node(node.node_id)
        for edge in net.edges:
            G.add_edge(edge.source_id, edge.target_id)

        # Use spring layout
        pos = nx.spring_layout(G, seed=42, k=2.5 / max(len(G.nodes()) ** 0.5, 1))

        # Separate traces by node type for legend
        traces: List[go.Scatter] = []
        node_by_id = {n.node_id: n for n in net.nodes}

        # Edge traces (one per edge type for legend grouping)
        for edge_type, edge_color in self._EDGE_COLORS.items():
            typed_edges = [
                e for e in net.edges if e.edge_type == edge_type
            ]
            if not typed_edges:
                continue
            ex, ey = [], []
            for edge in typed_edges:
                src_pos = pos.get(edge.source_id)
                tgt_pos = pos.get(edge.target_id)
                if src_pos is None or tgt_pos is None:
                    continue
                ex += [src_pos[0], tgt_pos[0], None]
                ey += [src_pos[1], tgt_pos[1], None]

            traces.append(
                go.Scatter(
                    x=ex, y=ey,
                    mode="lines",
                    line={"width": 1.5, "color": edge_color},
                    hoverinfo="none",
                    name=edge_type,
                    legendgroup=f"edge_{edge_type}",
                )
            )

        # Node traces by type
        for node_type, node_color in self._NODE_COLORS.items():
            typed_nodes = [n for n in net.nodes if n.node_type == node_type]
            if not typed_nodes:
                continue
            nx_vals, ny_vals, texts, hovers, sizes = [], [], [], [], []
            for node in typed_nodes:
                p = pos.get(node.node_id)
                if p is None:
                    continue
                nx_vals.append(p[0])
                ny_vals.append(p[1])
                texts.append(node.label[:20])
                hovers.append(
                    f"<b>{node.label}</b><br>"
                    f"Type: {node.node_type}<br>"
                    f"Risk Score: {node.risk_score:.0f}/100"
                )
                sizes.append(
                    self._RISK_SIZE_BASE + node.risk_score * self._RISK_SIZE_SCALE
                )

            traces.append(
                go.Scatter(
                    x=nx_vals, y=ny_vals,
                    mode="markers+text",
                    marker={"size": sizes, "color": node_color, "opacity": 0.85,
                            "line": {"width": 1.5, "color": "#fff"}},
                    text=texts,
                    textposition="top center",
                    hovertext=hovers,
                    hoverinfo="text",
                    name=node_type,
                    legendgroup=f"node_{node_type}",
                )
            )

        fig = go.Figure(
            data=traces,
            layout=go.Layout(
                title={
                    "text": (
                        f"Financial Relationship Network — {net.company_name} "
                        f"({net.analysis_period})"
                    ),
                    "x": 0.5,
                    "font": {"size": 18, "color": "#0D1B2A"},
                },
                showlegend=True,
                legend={"bgcolor": "#f0f2f5", "bordercolor": "#999"},
                hovermode="closest",
                xaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
                yaxis={"showgrid": False, "zeroline": False, "showticklabels": False},
                paper_bgcolor="#fafaf9",
                plot_bgcolor="#fafaf9",
                margin={"l": 20, "r": 20, "t": 60, "b": 20},
                annotations=[
                    {
                        "text": (
                            f"Nodes: {len(net.nodes)} | "
                            f"Edges: {len(net.edges)} | "
                            f"Density: {net.density:.3f} | "
                            f"Hub: {net.max_degree_node}"
                        ),
                        "showarrow": False,
                        "xref": "paper",
                        "yref": "paper",
                        "x": 0.01,
                        "y": 0.01,
                        "font": {"size": 11, "color": "#555"},
                    }
                ],
            ),
        )
        return fig

    # ── matplotlib visualisation ─────────────────────────────────────────────

    def _build_matplotlib_figure(
        self, net: FinancialNetworkData, path: Path
    ) -> None:
        """Build a static matplotlib network PNG for PDF embedding."""
        G = nx.DiGraph()
        for node in net.nodes:
            G.add_node(
                node.node_id,
                label=node.label,
                node_type=node.node_type,
                risk=node.risk_score,
            )
        for edge in net.edges:
            G.add_edge(edge.source_id, edge.target_id, edge_type=edge.edge_type)

        if len(G.nodes()) == 0:
            return

        pos = nx.spring_layout(G, seed=42, k=2.5 / max(len(G.nodes()) ** 0.5, 1))

        fig, ax = plt.subplots(figsize=(14, 10))
        ax.set_facecolor("#0D1B2A")
        fig.patch.set_facecolor("#0D1B2A")

        # Draw edges
        for edge in net.edges:
            if edge.source_id not in pos or edge.target_id not in pos:
                continue
            x0, y0 = pos[edge.source_id]
            x1, y1 = pos[edge.target_id]
            color = self._EDGE_COLORS.get(edge.edge_type, "#BDC3C7")
            ax.annotate(
                "",
                xy=(x1, y1),
                xytext=(x0, y0),
                arrowprops={
                    "arrowstyle": "->",
                    "color": color,
                    "alpha": 0.6,
                    "lw": max(0.5, edge.weight * 0.3),
                },
            )

        # Draw nodes
        node_by_id = {n.node_id: n for n in net.nodes}
        for node_id, (x, y) in pos.items():
            n = node_by_id.get(node_id)
            if n is None:
                continue
            color = self._NODE_COLORS.get(n.node_type, "#95A5A6")
            size = self._RISK_SIZE_BASE + n.risk_score * self._RISK_SIZE_SCALE
            ax.scatter(x, y, s=size * 8, c=color, zorder=5, alpha=0.9,
                       edgecolors="white", linewidths=1.2)
            ax.text(
                x, y + 0.06,
                n.label[:18],
                ha="center",
                fontsize=7,
                color="white",
                fontweight="bold",
                zorder=6,
            )

        # Legend
        handles = [
            mpatches.Patch(color=c, label=t)
            for t, c in self._NODE_COLORS.items()
            if any(n.node_type == t for n in net.nodes)
        ]
        ax.legend(
            handles=handles,
            loc="lower left",
            framealpha=0.7,
            facecolor="#1B2838",
            labelcolor="white",
            fontsize=8,
        )

        ax.set_title(
            f"Financial Network — {net.company_name} ({net.analysis_period})",
            color="white",
            fontsize=14,
            fontweight="bold",
            pad=16,
        )
        ax.axis("off")
        plt.tight_layout()
        plt.savefig(str(path), dpi=150, bbox_inches="tight", facecolor="#0D1B2A")
        plt.close(fig)
