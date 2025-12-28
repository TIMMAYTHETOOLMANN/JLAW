"""
JLAW Forensic Engine
====================

Master orchestrator for JLAW zero-dollar transaction forensic analysis.

This module implements the complete forensic analysis pipeline per Section 12.1
of JLAW Zero-Dollar Transaction Forensic Specification v1.0.

Pipeline Stages:
    1. SEC EDGAR Form 4 Acquisition
    2. XML Parsing and Normalization
    3. Parallel Module Execution:
        - Temporal Clustering Detection
        - Event Proximity Analysis
        - Beneficial Ownership Chain Resolution
    4. Behavioral Risk Scoring
    5. Prosecutorial Narrative Generation
    6. Evidence Package Creation

Reference:
    - Section 12.1: Master Orchestration Flow
"""

import asyncio
import logging
from datetime import date, datetime
from typing import List, Tuple, Optional
from pathlib import Path

from src.zero_dollar.config import JLAWConfig
from src.zero_dollar.models import (
    Transaction,
    ForensicDossier,
    ProsecutorialNarrative,
    EventProximityFlag,
    OwnershipChain,
    OwnershipNode,
)
from src.zero_dollar.acquisition import (
    SECEdgarAcquisition,
    Form4Filing,
    enrich_with_issuer_metadata,
    calculate_derived_fields,
)
from src.zero_dollar.modules import (
    TemporalClusteringModule,
    TemporalClusteringOutput,
    EventProximityModule,
    EventProximityOutput,
    BeneficialOwnershipModule,
    BehavioralScoringEngine,
)
from src.zero_dollar.evidence import (
    MerkleEvidenceChain,
    create_evidence_artifact,
)
from src.zero_dollar.narrative import ProsecutorialNarrativeGenerator
from .pipeline import PipelineExecutor, PipelineStage


logger = logging.getLogger(__name__)


class JLAWForensicEngine:
    """
    Master orchestrator for JLAW zero-dollar transaction forensic analysis.
    
    Coordinates complete pipeline execution from SEC EDGAR acquisition through
    prosecutorial narrative generation and evidence packaging.
    """
    
    def __init__(self, config: JLAWConfig):
        """
        Initialize JLAW forensic engine.
        
        Args:
            config: JLAW configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize modules
        self.temporal_module = TemporalClusteringModule()
        self.event_module = EventProximityModule()
        self.ownership_module = BeneficialOwnershipModule()
        self.scoring_engine = BehavioralScoringEngine()
        self.narrative_generator = ProsecutorialNarrativeGenerator(config)
        self.evidence_chain = MerkleEvidenceChain()
    
    async def analyze_issuer(
        self,
        issuer_cik: str,
        analysis_window: Tuple[date, date],
        issuer_name: Optional[str] = None,
        issuer_ticker: Optional[str] = None,
    ) -> ForensicDossier:
        """
        Execute full forensic analysis for specified issuer.
        
        Pipeline:
            1. Acquire Form 4 filings from SEC EDGAR
            2. Parse and normalize transaction data
            3. Execute parallel anomaly detection modules
            4. Synthesize behavioral risk assessment
            5. Generate prosecutorial narrative
            6. Package evidence with cryptographic attestation
        
        Args:
            issuer_cik: SEC CIK of issuer company
            analysis_window: Tuple of (start_date, end_date)
            issuer_name: Name of issuer (optional, will be fetched if not provided)
            issuer_ticker: Stock ticker (optional)
            
        Returns:
            ForensicDossier with complete analysis results
        """
        self.logger.info(
            f"Starting forensic analysis for CIK {issuer_cik} "
            f"({analysis_window[0]} to {analysis_window[1]})"
        )
        
        # Initialize pipeline executor
        pipeline = PipelineExecutor(issuer_cik=issuer_cik)
        
        try:
            # Stage 1: Acquire Form 4 filings
            pipeline.start_stage(PipelineStage.ACQUISITION)
            filings = await self.acquire_form4_filings(
                issuer_cik=issuer_cik,
                start_date=analysis_window[0],
                end_date=analysis_window[1],
            )
            pipeline.complete_stage(
                PipelineStage.ACQUISITION,
                data={'filing_count': len(filings)}
            )
            
            # Stage 2: Parse Form 4 filings
            pipeline.start_stage(PipelineStage.PARSING)
            transactions = await self.parse_form4_filings(filings)
            
            # Enrich with issuer metadata if not provided
            if not issuer_name and transactions:
                issuer_name = transactions[0].issuer_name
            if not issuer_ticker:
                issuer_ticker = None  # Could fetch from company tickers API
            
            pipeline.complete_stage(
                PipelineStage.PARSING,
                data={'transaction_count': len(transactions)}
            )
            
            # Check if we have zero-dollar transactions
            zero_dollar_txns = [t for t in transactions if t.is_zero_dollar]
            if not zero_dollar_txns:
                self.logger.info(f"No zero-dollar transactions found for CIK {issuer_cik}")
                pipeline.skip_stage(PipelineStage.TEMPORAL_ANALYSIS, "No zero-dollar transactions")
                pipeline.skip_stage(PipelineStage.EVENT_ANALYSIS, "No zero-dollar transactions")
                pipeline.skip_stage(PipelineStage.OWNERSHIP_ANALYSIS, "No zero-dollar transactions")
                pipeline.skip_stage(PipelineStage.SCORING, "No zero-dollar transactions")
                pipeline.skip_stage(PipelineStage.NARRATIVE, "No zero-dollar transactions")
                pipeline.skip_stage(PipelineStage.PACKAGING, "No zero-dollar transactions")
                pipeline.complete_pipeline()
                
                return self.create_null_dossier(
                    issuer_cik=issuer_cik,
                    issuer_name=issuer_name or f"CIK-{issuer_cik}",
                    issuer_ticker=issuer_ticker,
                    analysis_window=analysis_window,
                    total_transactions=len(transactions),
                )
            
            # Stage 3-5: Execute parallel modules
            temporal_output, event_output, ownership_chain = await self._execute_parallel_modules(
                pipeline=pipeline,
                transactions=zero_dollar_txns,
                issuer_cik=issuer_cik,
                analysis_window=analysis_window,
            )
            
            # Stage 6: Behavioral risk scoring
            pipeline.start_stage(PipelineStage.SCORING)
            
            # Group transactions by reporting person (use first for demo)
            reporting_person_cik = zero_dollar_txns[0].reporting_person_cik
            reporting_person_name = zero_dollar_txns[0].reporting_person_name
            
            assessment = self.scoring_engine.calculate_assessment(
                reporting_person_cik=reporting_person_cik,
                reporting_person_name=reporting_person_name,
                issuer_cik=issuer_cik,
                issuer_name=issuer_name or f"CIK-{issuer_cik}",
                transactions=transactions,
                temporal_output=temporal_output,
                event_flags=event_output.flags,
                ownership_chain=ownership_chain,
            )
            
            pipeline.complete_stage(
                PipelineStage.SCORING,
                data={'risk_score': assessment.risk_score, 'risk_level': assessment.risk_level}
            )
            
            # Stage 7: Generate prosecutorial narrative
            pipeline.start_stage(PipelineStage.NARRATIVE)
            
            narrative = self.narrative_generator.generate(
                assessment=assessment,
                temporal=temporal_output,
                events=event_output.flags,
                ownership=ownership_chain,
                transactions=zero_dollar_txns,
            )
            
            pipeline.complete_stage(PipelineStage.NARRATIVE)
            
            # Stage 8: Package evidence
            pipeline.start_stage(PipelineStage.PACKAGING)
            
            # Create evidence artifacts for Form 4 filings
            for filing in filings[:10]:  # Limit to first 10 for demo
                artifact = create_evidence_artifact(
                    artifact_type="form4_filing",
                    source_url=f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={issuer_cik}",
                    content=str(filing.to_dict()),
                    accession_number=filing.accession_number,
                )
                self.evidence_chain.add_artifact(artifact)
            
            # Get Merkle root
            merkle_root = self.evidence_chain.get_merkle_root()
            
            pipeline.complete_stage(
                PipelineStage.PACKAGING,
                data={'evidence_count': len(self.evidence_chain.artifacts)}
            )
            
            # Create forensic dossier
            dossier = ForensicDossier(
                case_id=self._generate_case_id(issuer_cik, analysis_window),
                issuer_cik=issuer_cik,
                issuer_name=issuer_name or f"CIK-{issuer_cik}",
                issuer_ticker=issuer_ticker,
                analysis_period=analysis_window,
                total_transactions_analyzed=len(transactions),
                zero_dollar_transactions=len(zero_dollar_txns),
                temporal_analysis=temporal_output,
                event_proximity_analysis=event_output.flags,
                ownership_chain_analysis=ownership_chain,
                risk_assessment=assessment,
                prosecutorial_narrative=narrative,
                merkle_root_hash=merkle_root,
                generated_timestamp=datetime.utcnow(),
                system_version="1.0.0",
            )
            
            pipeline.complete_pipeline()
            
            self.logger.info(f"Forensic analysis complete: {dossier.case_id}")
            self.logger.info(f"\n{pipeline.get_summary()}")
            
            return dossier
            
        except Exception as e:
            self.logger.error(f"Forensic analysis failed: {e}", exc_info=True)
            if pipeline.state.current_stage:
                pipeline.fail_stage(pipeline.state.current_stage, str(e))
            pipeline.complete_pipeline()
            raise
    
    async def acquire_form4_filings(
        self,
        issuer_cik: str,
        start_date: date,
        end_date: date,
    ) -> List[Form4Filing]:
        """
        Acquire Form 4 filings from SEC EDGAR.
        
        Args:
            issuer_cik: SEC CIK of issuer
            start_date: Analysis start date
            end_date: Analysis end date
            
        Returns:
            List of Form4Filing objects
        """
        self.logger.info(f"Acquiring Form 4 filings for CIK {issuer_cik}")
        
        # Initialize acquisition client
        acquisition = SECEdgarAcquisition(
            user_agent=self.config.sec_user_agent,
            cache_enabled=self.config.enable_caching,
            cache_directory=str(self.config.cache_directory),
        )
        
        # Acquire filings
        filings = await acquisition.acquire_form4_filings(
            issuer_cik=issuer_cik,
            start_date=start_date,
            end_date=end_date,
        )
        
        self.logger.info(f"Acquired {len(filings)} Form 4 filings")
        return filings
    
    async def parse_form4_filings(
        self,
        filings: List[Form4Filing],
    ) -> List[Transaction]:
        """
        Parse Form 4 filings into Transaction objects.
        
        Args:
            filings: List of Form4Filing objects
            
        Returns:
            List of Transaction objects
        """
        self.logger.info(f"Parsing {len(filings)} Form 4 filings")
        
        transactions = []
        for filing in filings:
            # Each filing may contain multiple transactions
            for txn_data in filing.transactions:
                # Convert filing data to Transaction object
                transaction = Transaction(
                    accession_number=filing.accession_number,
                    issuer_cik=filing.issuer_cik,
                    issuer_name=filing.issuer_name,
                    reporting_person_cik=filing.reporting_person_cik,
                    reporting_person_name=filing.reporting_person_name,
                    transaction_date=txn_data.get('transaction_date'),
                    filing_date=filing.filing_date,
                    transaction_code=txn_data.get('transaction_code', ''),
                    shares=txn_data.get('shares', 0),
                    price_per_share=txn_data.get('price_per_share'),
                    transaction_acquired_disposed=txn_data.get('acquired_disposed', ''),
                    shares_owned_following=txn_data.get('shares_owned_following', 0),
                    direct_indirect=txn_data.get('direct_indirect', 'D'),
                    nature_of_ownership=txn_data.get('nature_of_ownership', ''),
                )
                transactions.append(transaction)
        
        self.logger.info(f"Parsed {len(transactions)} transactions")
        return transactions
    
    async def _execute_parallel_modules(
        self,
        pipeline: PipelineExecutor,
        transactions: List[Transaction],
        issuer_cik: str,
        analysis_window: Tuple[date, date],
    ) -> Tuple[TemporalClusteringOutput, EventProximityOutput, OwnershipChain]:
        """
        Execute temporal, event, and ownership modules in parallel.
        
        Args:
            pipeline: Pipeline executor for stage tracking
            transactions: List of zero-dollar transactions
            issuer_cik: Issuer CIK
            analysis_window: Analysis date range
            
        Returns:
            Tuple of (temporal_output, event_output, ownership_chain)
        """
        if not self.config.parallel_execution:
            # Sequential execution
            return await self._execute_sequential_modules(
                pipeline, transactions, issuer_cik, analysis_window
            )
        
        self.logger.info("Executing parallel module analysis")
        
        # Start all three stages
        pipeline.start_stage(PipelineStage.TEMPORAL_ANALYSIS)
        pipeline.start_stage(PipelineStage.EVENT_ANALYSIS)
        pipeline.start_stage(PipelineStage.OWNERSHIP_ANALYSIS)
        
        # Execute in parallel
        temporal_task = asyncio.create_task(
            self._execute_temporal_analysis(transactions, issuer_cik, analysis_window)
        )
        event_task = asyncio.create_task(
            self._execute_event_analysis(transactions, issuer_cik)
        )
        ownership_task = asyncio.create_task(
            self._execute_ownership_analysis(transactions)
        )
        
        # Await all tasks
        temporal_output = await temporal_task
        event_output = await event_task
        ownership_chain = await ownership_task
        
        # Mark stages complete
        pipeline.complete_stage(PipelineStage.TEMPORAL_ANALYSIS)
        pipeline.complete_stage(PipelineStage.EVENT_ANALYSIS)
        pipeline.complete_stage(PipelineStage.OWNERSHIP_ANALYSIS)
        
        return temporal_output, event_output, ownership_chain
    
    async def _execute_sequential_modules(
        self,
        pipeline: PipelineExecutor,
        transactions: List[Transaction],
        issuer_cik: str,
        analysis_window: Tuple[date, date],
    ) -> Tuple[TemporalClusteringOutput, EventProximityOutput, OwnershipChain]:
        """Execute modules sequentially."""
        pipeline.start_stage(PipelineStage.TEMPORAL_ANALYSIS)
        temporal_output = await self._execute_temporal_analysis(
            transactions, issuer_cik, analysis_window
        )
        pipeline.complete_stage(PipelineStage.TEMPORAL_ANALYSIS)
        
        pipeline.start_stage(PipelineStage.EVENT_ANALYSIS)
        event_output = await self._execute_event_analysis(transactions, issuer_cik)
        pipeline.complete_stage(PipelineStage.EVENT_ANALYSIS)
        
        pipeline.start_stage(PipelineStage.OWNERSHIP_ANALYSIS)
        ownership_chain = await self._execute_ownership_analysis(transactions)
        pipeline.complete_stage(PipelineStage.OWNERSHIP_ANALYSIS)
        
        return temporal_output, event_output, ownership_chain
    
    async def _execute_temporal_analysis(
        self,
        transactions: List[Transaction],
        issuer_cik: str,
        analysis_window: Tuple[date, date],
    ) -> TemporalClusteringOutput:
        """Execute temporal clustering analysis."""
        self.logger.info("Executing temporal clustering analysis")
        
        # Group by reporting person (use first for demo)
        reporting_person_cik = transactions[0].reporting_person_cik
        
        output = self.temporal_module.analyze_transactions(
            transactions=transactions,
            reporting_person_cik=reporting_person_cik,
            issuer_cik=issuer_cik,
        )
        
        self.logger.info(f"Temporal analysis complete: {output.cluster_count} clusters detected")
        return output
    
    async def _execute_event_analysis(
        self,
        transactions: List[Transaction],
        issuer_cik: str,
    ) -> EventProximityOutput:
        """Execute event proximity analysis."""
        self.logger.info("Executing event proximity analysis")
        
        output = await self.event_module.analyze_transactions(
            transactions=transactions,
            issuer_cik=issuer_cik,
        )
        
        self.logger.info(f"Event analysis complete: {len(output.flags)} flags detected")
        return output
    
    async def _execute_ownership_analysis(
        self,
        transactions: List[Transaction],
    ) -> OwnershipChain:
        """Execute beneficial ownership chain analysis."""
        self.logger.info("Executing ownership chain analysis")
        
        # Use first transaction for demo
        if not transactions:
            return OwnershipChain(
                reporting_person_cik=transactions[0].reporting_person_cik,
                entities=[],
                control_assessments=[],
                chain_depth=0,
                total_entities=0,
            )
        
        chain = await self.ownership_module.analyze_ownership(
            transaction=transactions[0],
        )
        
        self.logger.info(f"Ownership analysis complete: {len(chain.entities)} entities")
        return chain
    
    def create_null_dossier(
        self,
        issuer_cik: str,
        issuer_name: str,
        issuer_ticker: Optional[str],
        analysis_window: Tuple[date, date],
        total_transactions: int,
    ) -> ForensicDossier:
        """
        Create null dossier when no zero-dollar transactions found.
        
        Args:
            issuer_cik: Issuer CIK
            issuer_name: Issuer name
            issuer_ticker: Issuer ticker
            analysis_window: Analysis date range
            total_transactions: Total transactions analyzed
            
        Returns:
            ForensicDossier with null findings
        """
        self.logger.info("Creating null dossier (no zero-dollar transactions)")
        
        # Create empty outputs
        from src.zero_dollar.models import (
            BehavioralScoreComponents,
            BehavioralRiskAssessment,
        )
        from decimal import Decimal
        
        temporal_output = TemporalClusteringOutput(
            reporting_person_cik="N/A",
            issuer_cik=issuer_cik,
            analysis_period=analysis_window,
            clusters_detected=[],
            total_anomaly_score=Decimal("0"),
            escalation_recommendation="NONE",
        )
        
        score_components = BehavioralScoreComponents(
            magnitude_score=0.0,
            frequency_score=0.0,
            timing_score=0.0,
            filing_compliance_score=0.0,
            entity_complexity_score=0.0,
        )
        
        assessment = BehavioralRiskAssessment(
            assessment_id=self._generate_case_id(issuer_cik, analysis_window),
            reporting_person_cik="N/A",
            reporting_person_name="N/A",
            issuer_cik=issuer_cik,
            issuer_name=issuer_name,
            assessment_date=datetime.utcnow(),
            score_components=score_components,
            zero_dollar_transaction_count=0,
            total_transaction_count=total_transactions,
            temporal_clusters_detected=0,
            recommendation="No zero-dollar transactions detected. No enforcement action recommended.",
            next_steps=["Continue routine Form 4 monitoring"],
        )
        
        narrative = ProsecutorialNarrative(
            narrative_id=f"NULL-{issuer_cik}",
            case_id=assessment.assessment_id,
            generated_timestamp=datetime.utcnow(),
            subject_identification=f"Issuer: {issuer_name} (CIK: {issuer_cik})",
            factual_summary="No zero-dollar transactions detected during analysis period.",
            anomaly_analysis="No anomalies detected.",
            violation_analysis="No violations detected.",
            damage_estimation="No damages estimated.",
            enforcement_recommendation="No enforcement action recommended.",
            evidence_summary="No zero-dollar transaction evidence.",
        )
        
        ownership_chain = OwnershipChain(
            reporting_person_cik="N/A",
            entities=[],
            control_assessments=[],
            chain_depth=0,
            total_entities=0,
        )
        
        return ForensicDossier(
            case_id=self._generate_case_id(issuer_cik, analysis_window),
            issuer_cik=issuer_cik,
            issuer_name=issuer_name,
            issuer_ticker=issuer_ticker,
            analysis_period=analysis_window,
            total_transactions_analyzed=total_transactions,
            zero_dollar_transactions=0,
            temporal_analysis=temporal_output,
            event_proximity_analysis=[],
            ownership_chain_analysis=ownership_chain,
            risk_assessment=assessment,
            prosecutorial_narrative=narrative,
            merkle_root_hash="0" * 64,  # Null hash
        )
    
    def _generate_case_id(
        self,
        issuer_cik: str,
        analysis_window: Tuple[date, date],
    ) -> str:
        """Generate unique case ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        return f"CASE-{issuer_cik}-{analysis_window[0].strftime('%Y%m%d')}-{timestamp}"
