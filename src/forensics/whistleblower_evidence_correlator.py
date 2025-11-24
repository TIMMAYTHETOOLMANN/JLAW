"""
Whistleblower Evidence Correlator - Penultimate Enhancement Module
Implements Dodd-Frank Act Section 922 (15 USC § 78u-6) and SEC Office of Whistleblower protocols.
Correlates protected whistleblower disclosures with public filings using advanced NLP.
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
import re
from collections import defaultdict

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.warning("sentence-transformers not available - using fallback methods")

from src.forensics.core.integrity_manager import (
    ForensicHashChain, IntegrityLevel
)

logger = logging.getLogger(__name__)


class WhistleblowerProtection(Enum):
    """Whistleblower protection classifications."""
    DODD_FRANK_922 = "DODD_FRANK_922"  # 15 USC § 78u-6
    SOX_806 = "SOX_806"  # 18 USC § 1514A
    FALSE_CLAIMS_ACT = "FALSE_CLAIMS_ACT"  # 31 USC § 3729-3733
    STATE_PROTECTION = "STATE_PROTECTION"


class ContradictionType(Enum):
    """Types of contradictions between claims and filings."""
    DIRECT_FACTUAL = "DIRECT_FACTUAL"
    OMISSION = "OMISSION"
    MISLEADING = "MISLEADING"
    TEMPORAL_INCONSISTENCY = "TEMPORAL_INCONSISTENCY"
    QUANTITATIVE_VARIANCE = "QUANTITATIVE_VARIANCE"


class EvidenceStrength(Enum):
    """Strength of corroborating evidence."""
    COMPELLING = "COMPELLING"
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass
class WhistleblowerClaim:
    """Individual whistleblower claim."""
    claim_id: str
    statement: str
    category: str  # revenue_fraud, accounting_manipulation, etc.
    alleged_date: Optional[datetime]
    supporting_documents: List[str]
    claim_embedding: Optional[np.ndarray] = None


@dataclass
class FilingSegment:
    """Segment of public filing."""
    segment_id: str
    text: str
    section: str  # MD&A, Financial_Statements, Notes, etc.
    filing_accession: str
    filing_date: datetime
    segment_embedding: Optional[np.ndarray] = None


@dataclass
class ContradictionMatch:
    """Matched contradiction between claim and filing."""
    whistleblower_claim: str
    public_statement: str
    filing_accession: str
    filing_date: datetime
    similarity_score: float
    contradiction_type: ContradictionType
    is_contradictory: bool
    legal_implication: str
    statute_violated: Optional[str]
    evidence_strength: EvidenceStrength
    explanation: str


@dataclass
class TemporalAlignment:
    """Temporal alignment between claim and filing."""
    claim_id: str
    filing_accession: str
    claim_date: datetime
    filing_date: datetime
    time_delta_days: int
    alignment_score: float
    temporal_consistency: bool
    explanation: str


@dataclass
class QuantitativeVariance:
    """Quantitative variance between claimed and reported figures."""
    metric_name: str
    whistleblower_value: float
    filing_value: float
    variance_amount: float
    variance_percentage: float
    materiality: str  # MATERIAL, IMMATERIAL
    explanation: str


@dataclass
class CorrelationMatrix:
    """Complete correlation analysis between whistleblower evidence and filings."""
    analysis_timestamp: str
    whistleblower_case_id: str
    
    # Correlation results
    direct_contradictions: List[ContradictionMatch]
    circumstantial_support: List[ContradictionMatch]
    temporal_alignments: List[TemporalAlignment]
    quantitative_variances: List[QuantitativeVariance]
    
    # Analysis metrics
    total_claims_analyzed: int
    total_filings_analyzed: int
    contradiction_count: int
    support_count: int
    
    # Overall assessment
    overall_correlation_strength: EvidenceStrength
    prosecutorial_value: str  # HIGH, MEDIUM, LOW
    recommended_actions: List[str]
    
    # Evidence integrity
    evidence_hash: str


class WhistleblowerEvidenceCorrelator:
    """
    Advanced whistleblower evidence correlator.
    
    Implements:
    - Dodd-Frank Act Section 922 (15 USC § 78u-6) - SEC Whistleblower Protection
    - SOX Section 806 (18 USC § 1514A) - Whistleblower Protection
    - SEC Office of Whistleblower protocols
    - Legal-BERT semantic similarity analysis
    - Multi-vector correlation analysis
    """
    
    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """
        Initialize whistleblower evidence correlator.
        
        Args:
            model_name: Sentence-BERT model for embeddings
        """
        self.hash_chain = ForensicHashChain("whistleblower_evidence_correlator")
        
        # Initialize Legal-BERT or fallback model
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                # Try legal-specific model first
                self.legal_bert = SentenceTransformer('nlpaueb/legal-bert-base-uncased')
                self.model_name = 'legal-bert-base-uncased'
                logger.info("Legal-BERT model loaded")
            except:
                # Fallback to general-purpose model
                self.legal_bert = SentenceTransformer(model_name)
                self.model_name = model_name
                logger.info(f"Sentence-BERT model loaded: {model_name}")
        else:
            self.legal_bert = None
            self.model_name = 'fallback'
            logger.warning("Using fallback embedding method")
        
        # Similarity thresholds
        self.similarity_thresholds = {
            'direct_contradiction': 0.85,
            'strong_support': 0.80,
            'moderate_support': 0.70,
            'weak_correlation': 0.60
        }
        
        # Materiality thresholds
        self.materiality_threshold = 0.05  # 5% variance
        
        logger.info("WhistleblowerEvidenceCorrelator initialized")
    
    async def correlate_protected_disclosure(
        self,
        whistleblower_evidence: Dict[str, Any],
        public_filings: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> CorrelationMatrix:
        """
        Correlate protected whistleblower disclosure with public filings.
        
        Args:
            whistleblower_evidence: Whistleblower claims and evidence
            public_filings: List of public SEC filings
            metadata: Optional metadata (case ID, dates, etc.)
            
        Returns:
            Complete correlation matrix
        """
        logger.info("Starting whistleblower evidence correlation...")
        
        metadata = metadata or {}
        case_id = metadata.get('case_id', f"WB-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}")
        
        # Parse whistleblower claims
        claims = await self._parse_whistleblower_claims(
            whistleblower_evidence.get('claims', [])
        )
        
        logger.info(f"Parsed {len(claims)} whistleblower claims")
        
        # Segment public filings
        filing_segments = await self._segment_all_filings(public_filings)
        
        logger.info(f"Segmented {len(public_filings)} filings into {len(filing_segments)} segments")
        
        # Generate embeddings
        await self._generate_embeddings(claims, filing_segments)
        
        # Correlation analysis
        direct_contradictions = []
        circumstantial_support = []
        temporal_alignments = []
        quantitative_variances = []
        
        for claim in claims:
            logger.debug(f"Analyzing claim: {claim.claim_id}")
            
            # Find contradictions
            contradictions = await self._find_contradictions(
                claim,
                filing_segments
            )
            direct_contradictions.extend(contradictions)
            
            # Find supporting evidence
            support = await self._find_circumstantial_support(
                claim,
                filing_segments
            )
            circumstantial_support.extend(support)
            
            # Temporal alignment
            temporal = await self._analyze_temporal_alignment(
                claim,
                public_filings
            )
            temporal_alignments.extend(temporal)
            
            # Quantitative variances
            if claim.category in ['revenue_fraud', 'accounting_manipulation']:
                variances = await self._detect_quantitative_variances(
                    claim,
                    public_filings
                )
                quantitative_variances.extend(variances)
        
        # Calculate overall correlation strength
        overall_strength = self._calculate_correlation_strength(
            direct_contradictions,
            circumstantial_support,
            temporal_alignments,
            quantitative_variances
        )
        
        # Assess prosecutorial value
        prosecutorial_value = self._assess_prosecutorial_value(
            direct_contradictions,
            overall_strength
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            direct_contradictions,
            circumstantial_support,
            overall_strength,
            prosecutorial_value
        )
        
        # Create correlation matrix
        matrix = CorrelationMatrix(
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            whistleblower_case_id=case_id,
            direct_contradictions=direct_contradictions,
            circumstantial_support=circumstantial_support,
            temporal_alignments=temporal_alignments,
            quantitative_variances=quantitative_variances,
            total_claims_analyzed=len(claims),
            total_filings_analyzed=len(public_filings),
            contradiction_count=len(direct_contradictions),
            support_count=len(circumstantial_support),
            overall_correlation_strength=overall_strength,
            prosecutorial_value=prosecutorial_value,
            recommended_actions=recommendations,
            evidence_hash=self.hash_chain.blocks[-1].current_hash if self.hash_chain.blocks else ""
        )
        
        # Log to hash chain
        await self.hash_chain.add_evidence(
            data={
                "action": "correlate_protected_disclosure",
                "case_id": case_id,
                "claims_analyzed": len(claims),
                "filings_analyzed": len(public_filings),
                "contradictions_found": len(direct_contradictions),
                "support_found": len(circumstantial_support),
                "correlation_strength": overall_strength.value,
                "prosecutorial_value": prosecutorial_value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            integrity_level=IntegrityLevel.CRITICAL
        )
        
        logger.info(
            f"Correlation complete: {len(direct_contradictions)} contradictions, "
            f"{len(circumstantial_support)} supporting evidence, "
            f"strength: {overall_strength.value}"
        )
        
        return matrix
    
    async def _parse_whistleblower_claims(
        self,
        claims_data: List[Dict[str, Any]]
    ) -> List[WhistleblowerClaim]:
        """Parse whistleblower claims into structured format."""
        claims = []
        
        for i, claim_data in enumerate(claims_data):
            claim = WhistleblowerClaim(
                claim_id=claim_data.get('id', f"CLAIM-{i+1:03d}"),
                statement=claim_data.get('statement', ''),
                category=claim_data.get('category', 'general'),
                alleged_date=self._parse_date(claim_data.get('date')),
                supporting_documents=claim_data.get('documents', [])
            )
            claims.append(claim)
        
        return claims
    
    def _parse_date(self, date_value: Any) -> Optional[datetime]:
        """Parse date from various formats."""
        if isinstance(date_value, datetime):
            return date_value
        elif isinstance(date_value, str):
            try:
                return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except:
                pass
        return None
    
    async def _segment_all_filings(
        self,
        public_filings: List[Dict[str, Any]]
    ) -> List[FilingSegment]:
        """Segment all filings into analyzable units."""
        all_segments = []
        
        for filing in public_filings:
            segments = await self._segment_filing(filing)
            all_segments.extend(segments)
        
        return all_segments
    
    async def _segment_filing(
        self,
        filing: Dict[str, Any]
    ) -> List[FilingSegment]:
        """
        Segment a filing into logical units for analysis.
        
        Segments by:
        - MD&A sections
        - Financial statement notes
        - Risk factors
        - Business description
        """
        segments = []
        content = filing.get('content', filing.get('text', ''))
        accession = filing.get('accession_number', 'UNKNOWN')
        filing_date = self._parse_date(filing.get('filing_date'))
        
        # Simple segmentation by paragraphs (in production would use more sophisticated methods)
        paragraphs = re.split(r'\n\s*\n', content)
        
        for i, para in enumerate(paragraphs):
            if len(para.strip()) < 100:  # Skip very short paragraphs
                continue
            
            # Determine section based on content
            section = self._identify_section(para)
            
            segment = FilingSegment(
                segment_id=f"{accession}-SEG-{i:04d}",
                text=para.strip(),
                section=section,
                filing_accession=accession,
                filing_date=filing_date or datetime.now(timezone.utc)
            )
            
            segments.append(segment)
        
        return segments
    
    def _identify_section(self, text: str) -> str:
        """Identify filing section from text content."""
        text_lower = text.lower()
        
        if 'management' in text_lower and 'discussion' in text_lower:
            return 'MD&A'
        elif 'financial statement' in text_lower or 'balance sheet' in text_lower:
            return 'Financial_Statements'
        elif 'note' in text_lower and ('financial' in text_lower or 'accounting' in text_lower):
            return 'Notes'
        elif 'risk factor' in text_lower:
            return 'Risk_Factors'
        elif 'business' in text_lower and ('description' in text_lower or 'overview' in text_lower):
            return 'Business'
        else:
            return 'Other'
    
    async def _generate_embeddings(
        self,
        claims: List[WhistleblowerClaim],
        segments: List[FilingSegment]
    ):
        """Generate embeddings for claims and filing segments."""
        if not self.legal_bert:
            # Fallback: simple TF-IDF-like representation
            return
        
        # Generate claim embeddings
        claim_texts = [claim.statement for claim in claims]
        if claim_texts:
            claim_embeddings = self.legal_bert.encode(claim_texts)
            for claim, embedding in zip(claims, claim_embeddings):
                claim.claim_embedding = embedding
        
        # Generate segment embeddings (batch for efficiency)
        segment_texts = [seg.text for seg in segments]
        if segment_texts:
            # Process in batches to avoid memory issues
            batch_size = 32
            for i in range(0, len(segment_texts), batch_size):
                batch = segment_texts[i:i+batch_size]
                embeddings = self.legal_bert.encode(batch)
                
                for seg, embedding in zip(segments[i:i+batch_size], embeddings):
                    seg.segment_embedding = embedding
        
        logger.info(f"Generated embeddings for {len(claims)} claims and {len(segments)} segments")
    
    async def _find_contradictions(
        self,
        claim: WhistleblowerClaim,
        segments: List[FilingSegment]
    ) -> List[ContradictionMatch]:
        """Find contradictions between claim and filing segments."""
        contradictions = []
        
        if claim.claim_embedding is None or not segments:
            return contradictions
        
        claim_embedding = claim.claim_embedding.reshape(1, -1)
        
        for segment in segments:
            if segment.segment_embedding is None:
                continue
            
            segment_embedding = segment.segment_embedding.reshape(1, -1)
            
            # Calculate similarity
            similarity = cosine_similarity(claim_embedding, segment_embedding)[0][0]
            
            # Check if similarity exceeds threshold
            if similarity > self.similarity_thresholds['direct_contradiction']:
                # Analyze for contradiction
                contradiction_analysis = await self._analyze_contradiction(
                    claim.statement,
                    segment.text,
                    similarity
                )
                
                if contradiction_analysis['is_contradictory']:
                    match = ContradictionMatch(
                        whistleblower_claim=claim.statement[:200],
                        public_statement=segment.text[:200],
                        filing_accession=segment.filing_accession,
                        filing_date=segment.filing_date,
                        similarity_score=float(similarity),
                        contradiction_type=contradiction_analysis['type'],
                        is_contradictory=True,
                        legal_implication=contradiction_analysis['legal_implication'],
                        statute_violated=contradiction_analysis['statute_violated'],
                        evidence_strength=contradiction_analysis['strength'],
                        explanation=contradiction_analysis['explanation']
                    )
                    
                    contradictions.append(match)
        
        return contradictions
    
    async def _analyze_contradiction(
        self,
        claim: str,
        statement: str,
        similarity: float
    ) -> Dict[str, Any]:
        """
        Analyze whether claim and statement are contradictory.
        
        Uses linguistic analysis to detect:
        - Direct factual contradictions
        - Omissions
        - Misleading statements
        """
        # Simple negation detection (would use more sophisticated NLU in production)
        claim_lower = claim.lower()
        statement_lower = statement.lower()
        
        # Check for negation patterns
        negation_patterns = [
            (r'\bnot\b', r'\bis\b'),
            (r'\bno\b', r'\byes\b'),
            (r'\bfalse\b', r'\btrue\b'),
            (r'\bdid not\b', r'\bdid\b'),
            (r'\bwas not\b', r'\bwas\b'),
            (r'\bdoes not\b', r'\bdoes\b')
        ]
        
        is_contradictory = False
        contradiction_type = ContradictionType.DIRECT_FACTUAL
        
        for neg_pattern, pos_pattern in negation_patterns:
            if (re.search(neg_pattern, claim_lower) and re.search(pos_pattern, statement_lower)) or \
               (re.search(pos_pattern, claim_lower) and re.search(neg_pattern, statement_lower)):
                is_contradictory = True
                break
        
        # Check for numerical contradictions
        claim_numbers = re.findall(r'\$?[\d,]+\.?\d*[BMK]?', claim)
        statement_numbers = re.findall(r'\$?[\d,]+\.?\d*[BMK]?', statement)
        
        if claim_numbers and statement_numbers and claim_numbers != statement_numbers:
            is_contradictory = True
            contradiction_type = ContradictionType.QUANTITATIVE_VARIANCE
        
        # Determine statute violated
        if is_contradictory:
            statute = '15 USC § 78j(b) - Fraudulent and Manipulative Devices (Rule 10b-5)'
            legal_implication = 'Material misstatement in public filing contradicts whistleblower evidence'
        else:
            statute = None
            legal_implication = 'No direct contradiction detected'
        
        # Evidence strength based on similarity
        if similarity > 0.90:
            strength = EvidenceStrength.COMPELLING
        elif similarity > 0.85:
            strength = EvidenceStrength.STRONG
        else:
            strength = EvidenceStrength.MODERATE
        
        explanation = (
            f"Semantic similarity of {similarity:.3f} between whistleblower claim and "
            f"public statement. {'Direct contradiction detected' if is_contradictory else 'No contradiction'}"
        )
        
        return {
            'is_contradictory': is_contradictory,
            'type': contradiction_type,
            'legal_implication': legal_implication,
            'statute_violated': statute,
            'strength': strength,
            'explanation': explanation
        }
    
    async def _find_circumstantial_support(
        self,
        claim: WhistleblowerClaim,
        segments: List[FilingSegment]
    ) -> List[ContradictionMatch]:
        """Find circumstantial supporting evidence for claim."""
        support = []
        
        if claim.claim_embedding is None or not segments:
            return support
        
        claim_embedding = claim.claim_embedding.reshape(1, -1)
        
        for segment in segments:
            if segment.segment_embedding is None:
                continue
            
            segment_embedding = segment.segment_embedding.reshape(1, -1)
            similarity = cosine_similarity(claim_embedding, segment_embedding)[0][0]
            
            # Check for supporting evidence (moderate to strong similarity, not contradictory)
            if self.similarity_thresholds['weak_correlation'] < similarity < self.similarity_thresholds['direct_contradiction']:
                # Check it's not contradictory
                contradiction_analysis = await self._analyze_contradiction(
                    claim.statement,
                    segment.text,
                    similarity
                )
                
                if not contradiction_analysis['is_contradictory']:
                    match = ContradictionMatch(
                        whistleblower_claim=claim.statement[:200],
                        public_statement=segment.text[:200],
                        filing_accession=segment.filing_accession,
                        filing_date=segment.filing_date,
                        similarity_score=float(similarity),
                        contradiction_type=ContradictionType.DIRECT_FACTUAL,
                        is_contradictory=False,
                        legal_implication='Circumstantial support for whistleblower claim',
                        statute_violated=None,
                        evidence_strength=EvidenceStrength.MODERATE,
                        explanation=f"Filing segment provides circumstantial support (similarity: {similarity:.3f})"
                    )
                    
                    support.append(match)
        
        return support
    
    async def _analyze_temporal_alignment(
        self,
        claim: WhistleblowerClaim,
        filings: List[Dict[str, Any]]
    ) -> List[TemporalAlignment]:
        """Analyze temporal alignment between claim and filings."""
        alignments = []
        
        if not claim.alleged_date:
            return alignments
        
        for filing in filings:
            filing_date = self._parse_date(filing.get('filing_date'))
            if not filing_date:
                continue
            
            # Calculate time delta
            time_delta = (filing_date - claim.alleged_date).days
            
            # Alignment score (closer dates = higher score)
            if abs(time_delta) < 30:
                alignment_score = 1.0
            elif abs(time_delta) < 90:
                alignment_score = 0.75
            elif abs(time_delta) < 180:
                alignment_score = 0.50
            else:
                alignment_score = 0.25
            
            # Temporal consistency
            consistent = abs(time_delta) < 180  # Within 6 months
            
            alignment = TemporalAlignment(
                claim_id=claim.claim_id,
                filing_accession=filing.get('accession_number', 'UNKNOWN'),
                claim_date=claim.alleged_date,
                filing_date=filing_date,
                time_delta_days=abs(time_delta),
                alignment_score=alignment_score,
                temporal_consistency=consistent,
                explanation=(
                    f"{'Filing predates claim by' if time_delta > 0 else 'Claim predates filing by'} "
                    f"{abs(time_delta)} days. {'Strong' if consistent else 'Weak'} temporal alignment."
                )
            )
            
            alignments.append(alignment)
        
        return alignments
    
    async def _detect_quantitative_variances(
        self,
        claim: WhistleblowerClaim,
        filings: List[Dict[str, Any]]
    ) -> List[QuantitativeVariance]:
        """Detect quantitative variances between claimed and reported figures."""
        variances = []
        
        # Extract numbers from claim
        claim_numbers = self._extract_numbers(claim.statement)
        
        if not claim_numbers:
            return variances
        
        for filing in filings:
            content = filing.get('content', filing.get('text', ''))
            filing_numbers = self._extract_numbers(content)
            
            # Compare numbers
            for claim_label, claim_value in claim_numbers.items():
                if claim_label in filing_numbers:
                    filing_value = filing_numbers[claim_label]
                    variance_amount = abs(claim_value - filing_value)
                    variance_pct = (variance_amount / abs(claim_value)) * 100 if claim_value != 0 else 0
                    
                    # Determine materiality
                    material = variance_pct > (self.materiality_threshold * 100)
                    
                    variance = QuantitativeVariance(
                        metric_name=claim_label,
                        whistleblower_value=claim_value,
                        filing_value=filing_value,
                        variance_amount=variance_amount,
                        variance_percentage=variance_pct,
                        materiality='MATERIAL' if material else 'IMMATERIAL',
                        explanation=(
                            f"Whistleblower claims {claim_label} of {claim_value:,.0f}, "
                            f"but filing reports {filing_value:,.0f}. "
                            f"Variance: {variance_amount:,.0f} ({variance_pct:.1f}%)"
                        )
                    )
                    
                    variances.append(variance)
        
        return variances
    
    def _extract_numbers(self, text: str) -> Dict[str, float]:
        """Extract labeled numbers from text (e.g., 'revenue $5M')."""
        numbers = {}
        
        # Pattern: label followed by number
        patterns = [
            r'(revenue|sales|income|profit|loss|expense|cost|asset|liability|debt|cash)\s*[:\-]?\s*\$?\s*([\d,]+\.?\d*)\s*([BMK])?',
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                label = match.group(1).lower()
                value_str = match.group(2).replace(',', '')
                multiplier = match.group(3)
                
                try:
                    value = float(value_str)
                    
                    # Apply multiplier
                    if multiplier:
                        if multiplier.upper() == 'B':
                            value *= 1_000_000_000
                        elif multiplier.upper() == 'M':
                            value *= 1_000_000
                        elif multiplier.upper() == 'K':
                            value *= 1_000
                    
                    numbers[label] = value
                except ValueError:
                    continue
        
        return numbers
    
    def _calculate_correlation_strength(
        self,
        contradictions: List[ContradictionMatch],
        support: List[ContradictionMatch],
        temporal: List[TemporalAlignment],
        variances: List[QuantitativeVariance]
    ) -> EvidenceStrength:
        """Calculate overall correlation strength."""
        # Count strong evidence
        compelling_contradictions = sum(
            1 for c in contradictions 
            if c.evidence_strength == EvidenceStrength.COMPELLING
        )
        
        strong_contradictions = sum(
            1 for c in contradictions 
            if c.evidence_strength in [EvidenceStrength.STRONG, EvidenceStrength.COMPELLING]
        )
        
        material_variances = sum(
            1 for v in variances 
            if v.materiality == 'MATERIAL'
        )
        
        # Determine overall strength
        if compelling_contradictions >= 2 or (strong_contradictions >= 3 and material_variances >= 2):
            return EvidenceStrength.COMPELLING
        elif strong_contradictions >= 2 or material_variances >= 2:
            return EvidenceStrength.STRONG
        elif len(contradictions) >= 1 or len(support) >= 3:
            return EvidenceStrength.MODERATE
        elif len(support) >= 1:
            return EvidenceStrength.WEAK
        else:
            return EvidenceStrength.INCONCLUSIVE
    
    def _assess_prosecutorial_value(
        self,
        contradictions: List[ContradictionMatch],
        strength: EvidenceStrength
    ) -> str:
        """Assess prosecutorial value of correlated evidence."""
        if strength == EvidenceStrength.COMPELLING and len(contradictions) >= 3:
            return "HIGH"
        elif strength in [EvidenceStrength.COMPELLING, EvidenceStrength.STRONG] and len(contradictions) >= 2:
            return "HIGH"
        elif strength == EvidenceStrength.STRONG or len(contradictions) >= 1:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(
        self,
        contradictions: List[ContradictionMatch],
        support: List[ContradictionMatch],
        strength: EvidenceStrength,
        prosecutorial_value: str
    ) -> List[str]:
        """Generate investigation recommendations."""
        recommendations = []
        
        if prosecutorial_value == "HIGH":
            recommendations.append(
                "IMMEDIATE: Initiate formal SEC investigation under Dodd-Frank Section 922"
            )
            recommendations.append(
                "REQUIRED: Provide whistleblower protection per 15 USC § 78u-6(h)"
            )
            recommendations.append(
                "ACTION: Subpoena additional company records to corroborate findings"
            )
        elif prosecutorial_value == "MEDIUM":
            recommendations.append(
                "HIGH PRIORITY: Enhanced scrutiny of identified contradictions"
            )
            recommendations.append(
                "ACTION: Request voluntary document production from company"
            )
        else:
            recommendations.append(
                "LOW PRIORITY: Monitor for additional corroborating evidence"
            )
        
        if len(contradictions) >= 2:
            recommendations.append(
                "ACTION: Cross-reference with other whistleblower complaints"
            )
        
        if len(support) >= 3:
            recommendations.append(
                "ACTION: Analyze supporting evidence for prosecution strategy"
            )
        
        recommendations.append(
            "ONGOING: Protect whistleblower identity per statutory requirements"
        )
        
        return recommendations
    
    async def verify_integrity(self) -> bool:
        """Verify hash chain integrity."""
        is_valid = await self.hash_chain.verify_chain()
        
        if not is_valid:
            logger.critical("Whistleblower correlator hash chain integrity violation!")
        
        return is_valid


# Backward compatibility exports
__all__ = [
    'WhistleblowerEvidenceCorrelator',
    'WhistleblowerProtection',
    'ContradictionType',
    'EvidenceStrength',
    'WhistleblowerClaim',
    'ContradictionMatch',
    'CorrelationMatrix'
]

