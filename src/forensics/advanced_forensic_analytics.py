"""
Advanced Forensic Analytics Module - Module 1
Implements graph-based contradiction detection and enhanced financial forensics.
Integrates with existing JLAW forensic system with full backward compatibility.
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field
import logging

# Core dependencies
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    cosine_similarity = None

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    spacy = None

# JLAW core imports
from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel, ForensicBlock
)

logger = logging.getLogger(__name__)


@dataclass
class ContradictionDetection:
    """Result of semantic contradiction analysis."""
    claim1: Tuple[str, str, str]  # (subject, predicate, object)
    claim2: Tuple[str, str, str]
    similarity_score: float
    contradiction_type: str
    severity: str
    explanation: str
    filing_section1: Optional[str] = None
    filing_section2: Optional[str] = None
    evidence_hash: Optional[str] = None


@dataclass
class BeneishMScore:
    """Beneish M-Score manipulation probability result."""
    score: float
    probability: float
    manipulation_flag: bool
    risk_level: str
    components: Dict[str, float]
    interpretation: str
    evidence_hash: Optional[str] = None


@dataclass
class AdvancedForensicResult:
    """Combined results from advanced forensic analytics."""
    timestamp: str
    cik: str
    filing_type: str
    contradictions: List[ContradictionDetection]
    beneish_analysis: Optional[BeneishMScore]
    graph_metrics: Dict[str, Any]
    overall_risk_score: float
    critical_findings: List[str]
    evidence_chain_hash: str


class SemanticContradictionGraph:
    """
    Graph-based semantic contradiction detection using NLP.
    Identifies contradictory claims within SEC filings using dependency parsing
    and semantic similarity analysis.
    """
    
    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize semantic contradiction detector.
        
        Args:
            model_name: SentenceTransformer model for embeddings
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError(
                "NetworkX required: pip install networkx\n"
                "This is required for graph-based analysis."
            )
        
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers required: pip install sentence-transformers\n"
                "This is required for semantic similarity analysis."
            )
        
        self.knowledge_graph = nx.DiGraph()
        self.embedder = SentenceTransformer(model_name)
        self.hash_chain = ForensicHashChain("semantic_contradiction")
        
        # Load spaCy if available
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                logger.warning(
                    "SpaCy model not found. Install with: python -m spacy download en_core_web_sm"
                )
        
        logger.info("SemanticContradictionGraph initialized successfully")
    
    async def build_filing_graph(
        self,
        filing_text: str,
        section_name: Optional[str] = None
    ) -> int:
        """
        Build knowledge graph from filing text using dependency parsing.
        
        Args:
            filing_text: Text content to analyze
            section_name: Optional section identifier
            
        Returns:
            Number of claims extracted
        """
        if not self.nlp:
            logger.warning("SpaCy not available, using fallback extraction")
            return await self._build_graph_fallback(filing_text, section_name)
        
        claims_extracted = 0
        
        # Process text with spaCy
        doc = self.nlp(filing_text[:1000000])  # Limit for memory
        
        for sent in doc.sents:
            # Extract subject-predicate-object triplets
            subject = [tok for tok in sent if tok.dep_ == "nsubj"]
            predicate = [tok for tok in sent if tok.dep_ == "ROOT"]
            obj = [tok for tok in sent if tok.dep_ in ["dobj", "pobj", "attr"]]
            
            if subject and predicate and obj:
                claim = (
                    subject[0].text,
                    predicate[0].text,
                    obj[0].text
                )
                
                # Generate embedding for full sentence
                embedding = self.embedder.encode(sent.text)
                
                # Add to knowledge graph
                self.knowledge_graph.add_node(
                    claim,
                    embedding=embedding,
                    sentence=sent.text,
                    section=section_name or "unknown"
                )
                
                claims_extracted += 1
        
        # Log to integrity chain
        await self.hash_chain.add_evidence(
            data={
                "action": "build_graph",
                "section": section_name,
                "claims_extracted": claims_extracted,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            integrity_level=IntegrityLevel.HIGH
        )
        
        logger.info(f"Extracted {claims_extracted} claims from filing")
        return claims_extracted
    
    async def _build_graph_fallback(
        self,
        filing_text: str,
        section_name: Optional[str]
    ) -> int:
        """
        Fallback method for building graph without spaCy.
        Uses simple sentence splitting and embedding.
        """
        # Split into sentences (simple approach)
        sentences = filing_text.split(". ")
        claims_extracted = 0
        
        for sent in sentences[:500]:  # Limit for performance
            if len(sent.split()) < 5:  # Skip very short sentences
                continue
            
            # Use sentence as claim (without structure)
            claim = (sent[:50], "states", sent[50:100] if len(sent) > 50 else sent)
            
            # Generate embedding
            embedding = self.embedder.encode(sent)
            
            self.knowledge_graph.add_node(
                claim,
                embedding=embedding,
                sentence=sent,
                section=section_name or "unknown"
            )
            
            claims_extracted += 1
        
        return claims_extracted
    
    async def detect_contradictions(
        self,
        threshold: float = 0.85,
        max_contradictions: int = 50
    ) -> List[ContradictionDetection]:
        """
        Detect semantic contradictions in knowledge graph.
        
        Args:
            threshold: Similarity threshold for contradiction detection
            max_contradictions: Maximum contradictions to return
            
        Returns:
            List of detected contradictions
        """
        contradictions = []
        nodes = list(self.knowledge_graph.nodes(data=True))
        
        logger.info(f"Analyzing {len(nodes)} claims for contradictions")
        
        for i, (claim1, data1) in enumerate(nodes):
            for claim2, data2 in nodes[i+1:]:
                # Calculate semantic similarity
                similarity = cosine_similarity(
                    data1['embedding'].reshape(1, -1),
                    data2['embedding'].reshape(1, -1)
                )[0][0]
                
                # Check if semantically similar but contradictory
                if similarity > threshold:
                    is_contradictory, explanation = self._are_contradictory(
                        claim1,
                        claim2,
                        data1['sentence'],
                        data2['sentence']
                    )
                    
                    if is_contradictory:
                        severity = self._assess_contradiction_severity(
                            similarity,
                            claim1,
                            claim2
                        )
                        
                        contradiction = ContradictionDetection(
                            claim1=claim1,
                            claim2=claim2,
                            similarity_score=float(similarity),
                            contradiction_type='SEMANTIC_CONTRADICTION',
                            severity=severity,
                            explanation=explanation,
                            filing_section1=data1.get('section'),
                            filing_section2=data2.get('section')
                        )
                        
                        contradictions.append(contradiction)
                        
                        if len(contradictions) >= max_contradictions:
                            break
            
            if len(contradictions) >= max_contradictions:
                break
        
        # Log detection results
        await self.hash_chain.add_evidence(
            data={
                "action": "detect_contradictions",
                "contradictions_found": len(contradictions),
                "threshold": threshold,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            integrity_level=IntegrityLevel.CRITICAL
        )
        
        logger.info(f"Detected {len(contradictions)} contradictions")
        return contradictions
    
    def _are_contradictory(
        self,
        claim1: Tuple[str, str, str],
        claim2: Tuple[str, str, str],
        sentence1: str,
        sentence2: str
    ) -> Tuple[bool, str]:
        """
        Determine if two claims are contradictory.
        
        Returns:
            Tuple of (is_contradictory, explanation)
        """
        # Check for negation patterns
        negation_words = {'not', 'no', 'never', 'none', 'neither', 'nothing', 'cannot', 'won\'t', 'don\'t'}
        
        sent1_lower = sentence1.lower()
        sent2_lower = sentence2.lower()
        
        has_negation_1 = any(word in sent1_lower for word in negation_words)
        has_negation_2 = any(word in sent2_lower for word in negation_words)
        
        # If one has negation and other doesn't, likely contradictory
        if has_negation_1 != has_negation_2:
            return True, "Negation pattern detected in similar statements"
        
        # Check for opposite numerical claims
        if self._has_opposite_numbers(sentence1, sentence2):
            return True, "Contradictory numerical values detected"
        
        # Check for conflicting temporal claims
        if self._has_conflicting_time(sentence1, sentence2):
            return True, "Conflicting temporal claims detected"
        
        return False, ""
    
    def _has_opposite_numbers(self, sent1: str, sent2: str) -> bool:
        """Check if sentences contain opposite numerical claims."""
        # Look for increase/decrease patterns
        increase_words = {'increase', 'grow', 'rise', 'gain', 'improve', 'up'}
        decrease_words = {'decrease', 'decline', 'fall', 'loss', 'deteriorate', 'down'}
        
        sent1_words = set(sent1.lower().split())
        sent2_words = set(sent2.lower().split())
        
        has_increase_1 = bool(sent1_words & increase_words)
        has_decrease_1 = bool(sent1_words & decrease_words)
        has_increase_2 = bool(sent2_words & increase_words)
        has_decrease_2 = bool(sent2_words & decrease_words)
        
        return (has_increase_1 and has_decrease_2) or (has_decrease_1 and has_increase_2)
    
    def _has_conflicting_time(self, sent1: str, sent2: str) -> bool:
        """Check for conflicting temporal claims."""
        # Simple pattern matching for temporal conflicts
        temporal_patterns = [
            ('before', 'after'),
            ('prior', 'subsequent'),
            ('earlier', 'later'),
            ('previous', 'next')
        ]
        
        sent1_lower = sent1.lower()
        sent2_lower = sent2.lower()
        
        for pattern1, pattern2 in temporal_patterns:
            if (pattern1 in sent1_lower and pattern2 in sent2_lower) or \
               (pattern2 in sent1_lower and pattern1 in sent2_lower):
                return True
        
        return False
    
    def _assess_contradiction_severity(
        self,
        similarity: float,
        claim1: Tuple[str, str, str],
        claim2: Tuple[str, str, str]
    ) -> str:
        """Assess severity of contradiction."""
        # Financial keywords indicate higher severity
        financial_keywords = {
            'revenue', 'income', 'profit', 'loss', 'asset', 'liability',
            'cash', 'debt', 'equity', 'earnings', 'dividend'
        }
        
        claim_text = ' '.join(claim1).lower() + ' '.join(claim2).lower()
        
        has_financial = any(keyword in claim_text for keyword in financial_keywords)
        
        if similarity > 0.95 and has_financial:
            return "CRITICAL"
        elif similarity > 0.90 or has_financial:
            return "HIGH"
        elif similarity > 0.85:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_graph_metrics(self) -> Dict[str, Any]:
        """
        Get knowledge graph metrics for analysis.
        
        Returns:
            Dictionary of graph metrics
        """
        if not self.knowledge_graph.nodes():
            return {
                "node_count": 0,
                "edge_count": 0,
                "density": 0.0,
                "avg_degree": 0.0
            }
        
        return {
            "node_count": self.knowledge_graph.number_of_nodes(),
            "edge_count": self.knowledge_graph.number_of_edges(),
            "density": nx.density(self.knowledge_graph),
            "avg_degree": sum(dict(self.knowledge_graph.degree()).values()) / 
                         self.knowledge_graph.number_of_nodes() if self.knowledge_graph.number_of_nodes() > 0 else 0,
            "is_connected": nx.is_weakly_connected(self.knowledge_graph) if self.knowledge_graph.number_of_nodes() > 0 else False
        }


class EnhancedFinancialForensics:
    """
    Enhanced financial forensics with Beneish M-Score calculation.
    Detects earnings manipulation using 8-variable model with 76% accuracy.
    """
    
    def __init__(self):
        """Initialize enhanced financial forensics analyzer."""
        self.hash_chain = ForensicHashChain("financial_forensics")
        logger.info("EnhancedFinancialForensics initialized successfully")
    
    async def calculate_beneish_mscore(
        self,
        current_data: Dict[str, float],
        prior_data: Dict[str, float],
        filing_metadata: Optional[Dict[str, Any]] = None
    ) -> BeneishMScore:
        """
        Calculate Beneish M-Score for earnings manipulation detection.
        
        The Beneish M-Score is an 8-variable model that predicts earnings manipulation
        with 76% accuracy. Score > -2.22 indicates likely manipulation.
        
        Args:
            current_data: Current period financial data
            prior_data: Prior period financial data
            filing_metadata: Optional filing metadata for context
            
        Returns:
            BeneishMScore with manipulation probability
        """
        logger.info("Calculating Beneish M-Score")
        
        # Validate required fields
        required_fields = [
            'receivables', 'sales', 'cogs', 'current_assets', 'ppe',
            'total_assets', 'depreciation', 'sga', 'debt', 'income_continuing',
            'cash_flow'
        ]
        
        missing_current = [f for f in required_fields if f not in current_data]
        missing_prior = [f for f in required_fields if f not in prior_data]
        
        if missing_current or missing_prior:
            logger.warning(
                f"Missing fields - Current: {missing_current}, Prior: {missing_prior}"
            )
            # Return conservative high-risk score
            return BeneishMScore(
                score=0.0,
                probability=0.5,
                manipulation_flag=True,
                risk_level="UNKNOWN",
                components={},
                interpretation="Insufficient data for M-Score calculation"
            )
        
        try:
            # 1. Days Sales in Receivables Index (DSRI)
            dsri = self._safe_divide(
                current_data['receivables'] / current_data['sales'],
                prior_data['receivables'] / prior_data['sales']
            )
            
            # 2. Gross Margin Index (GMI)
            current_gm = (current_data['sales'] - current_data['cogs']) / current_data['sales']
            prior_gm = (prior_data['sales'] - prior_data['cogs']) / prior_data['sales']
            gmi = self._safe_divide(prior_gm, current_gm)
            
            # 3. Asset Quality Index (AQI)
            current_aqi_num = 1 - (current_data['current_assets'] + current_data['ppe']) / current_data['total_assets']
            prior_aqi_num = 1 - (prior_data['current_assets'] + prior_data['ppe']) / prior_data['total_assets']
            aqi = self._safe_divide(current_aqi_num, prior_aqi_num)
            
            # 4. Sales Growth Index (SGI)
            sgi = self._safe_divide(current_data['sales'], prior_data['sales'])
            
            # 5. Depreciation Index (DEPI)
            prior_depr_rate = prior_data['depreciation'] / (prior_data['depreciation'] + prior_data['ppe'])
            current_depr_rate = current_data['depreciation'] / (current_data['depreciation'] + current_data['ppe'])
            depi = self._safe_divide(prior_depr_rate, current_depr_rate)
            
            # 6. SG&A Index (SGAI)
            sgai = self._safe_divide(
                current_data['sga'] / current_data['sales'],
                prior_data['sga'] / prior_data['sales']
            )
            
            # 7. Leverage Index (LVGI)
            current_leverage = current_data['debt'] / current_data['total_assets']
            prior_leverage = prior_data['debt'] / prior_data['total_assets']
            lvgi = self._safe_divide(current_leverage, prior_leverage)
            
            # 8. Total Accruals to Total Assets (TATA)
            tata = (current_data['income_continuing'] - current_data['cash_flow']) / \
                   current_data['total_assets']
            
            # Calculate M-Score using Beneish (1999) coefficients
            m_score = (
                -4.84 +
                0.92 * dsri +
                0.528 * gmi +
                0.404 * aqi +
                0.892 * sgi +
                0.115 * depi -
                0.172 * sgai +
                4.679 * tata -
                0.327 * lvgi
            )
            
            # Calculate manipulation probability (logistic function)
            probability = 1 / (1 + np.exp(-m_score))
            
            # Determine manipulation flag (threshold: -2.22)
            manipulation_flag = m_score > -2.22
            
            # Assess risk level
            if m_score > -1.78:
                risk_level = "CRITICAL"
            elif m_score > -2.22:
                risk_level = "HIGH"
            elif m_score > -2.76:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            # Build components dictionary
            components = {
                'DSRI': float(dsri),
                'GMI': float(gmi),
                'AQI': float(aqi),
                'SGI': float(sgi),
                'DEPI': float(depi),
                'SGAI': float(sgai),
                'LVGI': float(lvgi),
                'TATA': float(tata)
            }
            
            # Generate interpretation
            interpretation = self._generate_mscore_interpretation(
                m_score,
                components,
                manipulation_flag
            )
            
            result = BeneishMScore(
                score=float(m_score),
                probability=float(probability),
                manipulation_flag=manipulation_flag,
                risk_level=risk_level,
                components=components,
                interpretation=interpretation
            )
            
            # Log to integrity chain
            await self.hash_chain.add_evidence(
                data={
                    "action": "calculate_beneish_mscore",
                    "m_score": float(m_score),
                    "manipulation_flag": manipulation_flag,
                    "risk_level": risk_level,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                integrity_level=IntegrityLevel.CRITICAL
            )
            
            logger.info(
                f"M-Score: {m_score:.3f}, Risk: {risk_level}, "
                f"Manipulation: {manipulation_flag}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating M-Score: {e}", exc_info=True)
            return BeneishMScore(
                score=0.0,
                probability=0.5,
                manipulation_flag=True,
                risk_level="ERROR",
                components={},
                interpretation=f"Error in calculation: {str(e)}"
            )
    
    def _safe_divide(self, numerator: float, denominator: float) -> float:
        """Safe division with zero handling."""
        if denominator == 0 or np.isnan(denominator) or np.isinf(denominator):
            return 1.0  # Neutral value for ratios
        result = numerator / denominator
        if np.isnan(result) or np.isinf(result):
            return 1.0
        return result
    
    def _generate_mscore_interpretation(
        self,
        m_score: float,
        components: Dict[str, float],
        manipulation_flag: bool
    ) -> str:
        """Generate human-readable interpretation of M-Score."""
        lines = []
        
        if manipulation_flag:
            lines.append(
                f"⚠️ HIGH RISK: M-Score of {m_score:.3f} exceeds manipulation threshold (-2.22)"
            )
        else:
            lines.append(
                f"✓ LOW RISK: M-Score of {m_score:.3f} below manipulation threshold"
            )
        
        lines.append("\nKey Indicators:")
        
        # Analyze DSRI (Days Sales in Receivables Index)
        if components['DSRI'] > 1.031:
            lines.append(
                f"  • DSRI ({components['DSRI']:.3f}): Receivables growing faster than sales - "
                "possible revenue inflation"
            )
        
        # Analyze GMI (Gross Margin Index)
        if components['GMI'] > 1.014:
            lines.append(
                f"  • GMI ({components['GMI']:.3f}): Deteriorating gross margins - "
                "poor future prospects"
            )
        
        # Analyze AQI (Asset Quality Index)
        if components['AQI'] > 1.039:
            lines.append(
                f"  • AQI ({components['AQI']:.3f}): Increased deferred costs - "
                "potential asset overstatement"
            )
        
        # Analyze SGI (Sales Growth Index)
        if components['SGI'] > 1.134:
            lines.append(
                f"  • SGI ({components['SGI']:.3f}): High sales growth - "
                "pressure to manipulate earnings"
            )
        
        # Analyze TATA (Total Accruals)
        if components['TATA'] > 0.018:
            lines.append(
                f"  • TATA ({components['TATA']:.3f}): High accruals - "
                "earnings may be inflated"
            )
        
        return '\n'.join(lines)


class AdvancedForensicAnalyzer:
    """
    Integrated advanced forensic analyzer combining all enhancement modules.
    Provides unified interface for contradiction detection and financial forensics.
    """
    
    def __init__(self):
        """Initialize advanced forensic analyzer."""
        self.contradiction_detector = None
        self.financial_forensics = EnhancedFinancialForensics()
        self.hash_chain = ForensicHashChain("advanced_forensics")
        
        # Initialize contradiction detector if dependencies available
        if NETWORKX_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.contradiction_detector = SemanticContradictionGraph()
            except Exception as e:
                logger.warning(f"Could not initialize contradiction detector: {e}")
        else:
            logger.warning(
                "Contradiction detection unavailable - install networkx and sentence-transformers"
            )
        
        logger.info("AdvancedForensicAnalyzer initialized")
    
    async def analyze_filing(
        self,
        filing_text: str,
        current_financials: Optional[Dict[str, float]] = None,
        prior_financials: Optional[Dict[str, float]] = None,
        cik: str = "UNKNOWN",
        filing_type: str = "UNKNOWN"
    ) -> AdvancedForensicResult:
        """
        Perform comprehensive advanced forensic analysis.
        
        Args:
            filing_text: Full filing text content
            current_financials: Current period financial data
            prior_financials: Prior period financial data
            cik: Company CIK
            filing_type: Filing type (10-K, 10-Q, etc.)
            
        Returns:
            AdvancedForensicResult with all findings
        """
        logger.info(f"Starting advanced forensic analysis for CIK {cik}")
        
        contradictions = []
        graph_metrics = {}
        
        # 1. Semantic Contradiction Detection
        if self.contradiction_detector:
            try:
                await self.contradiction_detector.build_filing_graph(
                    filing_text,
                    section_name=filing_type
                )
                
                contradictions = await self.contradiction_detector.detect_contradictions(
                    threshold=0.85
                )
                
                graph_metrics = self.contradiction_detector.get_graph_metrics()
                
            except Exception as e:
                logger.error(f"Contradiction detection failed: {e}", exc_info=True)
        
        # 2. Beneish M-Score Analysis
        beneish_analysis = None
        if current_financials and prior_financials:
            try:
                beneish_analysis = await self.financial_forensics.calculate_beneish_mscore(
                    current_financials,
                    prior_financials
                )
            except Exception as e:
                logger.error(f"Beneish M-Score calculation failed: {e}", exc_info=True)
        
        # 3. Calculate Overall Risk Score
        overall_risk = self._calculate_overall_risk(
            contradictions,
            beneish_analysis
        )
        
        # 4. Identify Critical Findings
        critical_findings = self._identify_critical_findings(
            contradictions,
            beneish_analysis
        )
        
        # 5. Create result
        result = AdvancedForensicResult(
            timestamp=datetime.now(timezone.utc).isoformat(),
            cik=cik,
            filing_type=filing_type,
            contradictions=contradictions,
            beneish_analysis=beneish_analysis,
            graph_metrics=graph_metrics,
            overall_risk_score=overall_risk,
            critical_findings=critical_findings,
            evidence_chain_hash=self.hash_chain.blocks[-1].current_hash if self.hash_chain.blocks else ""
        )
        
        # 6. Log to integrity chain
        await self.hash_chain.add_evidence(
            data={
                "action": "analyze_filing",
                "cik": cik,
                "filing_type": filing_type,
                "contradictions_found": len(contradictions),
                "beneish_flag": beneish_analysis.manipulation_flag if beneish_analysis else None,
                "overall_risk": overall_risk,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            integrity_level=IntegrityLevel.CRITICAL
        )
        
        logger.info(
            f"Advanced analysis complete - Risk: {overall_risk:.2%}, "
            f"Contradictions: {len(contradictions)}, "
            f"Critical Findings: {len(critical_findings)}"
        )
        
        return result
    
    def _calculate_overall_risk(
        self,
        contradictions: List[ContradictionDetection],
        beneish_analysis: Optional[BeneishMScore]
    ) -> float:
        """Calculate overall risk score from all analyses."""
        risk_components = []
        
        # Contradiction risk
        if contradictions:
            critical_count = sum(1 for c in contradictions if c.severity == "CRITICAL")
            high_count = sum(1 for c in contradictions if c.severity == "HIGH")
            
            contradiction_risk = min(
                (critical_count * 0.3 + high_count * 0.15) / max(len(contradictions), 1),
                1.0
            )
            risk_components.append(contradiction_risk)
        
        # Beneish M-Score risk
        if beneish_analysis:
            risk_components.append(beneish_analysis.probability)
        
        # Overall risk is weighted average
        if risk_components:
            return sum(risk_components) / len(risk_components)
        else:
            return 0.0
    
    def _identify_critical_findings(
        self,
        contradictions: List[ContradictionDetection],
        beneish_analysis: Optional[BeneishMScore]
    ) -> List[str]:
        """Identify critical findings requiring immediate attention."""
        findings = []
        
        # Critical contradictions
        critical_contradictions = [
            c for c in contradictions if c.severity == "CRITICAL"
        ]
        
        if critical_contradictions:
            findings.append(
                f"🚨 {len(critical_contradictions)} CRITICAL contradictions detected in filing"
            )
        
        # High-risk M-Score
        if beneish_analysis and beneish_analysis.manipulation_flag:
            findings.append(
                f"🚨 Beneish M-Score ({beneish_analysis.score:.3f}) indicates likely earnings manipulation"
            )
        
        # Multiple high-severity contradictions
        high_contradictions = [
            c for c in contradictions if c.severity in ["CRITICAL", "HIGH"]
        ]
        
        if len(high_contradictions) >= 5:
            findings.append(
                f"⚠️ {len(high_contradictions)} high-severity contradictions suggest systematic issues"
            )
        
        return findings
    
    async def verify_integrity(self) -> bool:
        """
        Verify integrity of all analysis chains.
        
        Returns:
            True if all chains are valid
        """
        chains_to_verify = [self.hash_chain]
        
        if self.contradiction_detector:
            chains_to_verify.append(self.contradiction_detector.hash_chain)
        
        chains_to_verify.append(self.financial_forensics.hash_chain)
        
        all_valid = True
        for chain in chains_to_verify:
            is_valid = await chain.verify_chain()
            if not is_valid:
                logger.critical(f"Chain integrity violation: {chain.chain_id}")
                all_valid = False
        
        return all_valid


# Backward compatibility exports
__all__ = [
    'SemanticContradictionGraph',
    'EnhancedFinancialForensics',
    'AdvancedForensicAnalyzer',
    'ContradictionDetection',
    'BeneishMScore',
    'AdvancedForensicResult'
]

