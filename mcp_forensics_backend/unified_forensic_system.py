"""
Unified Forensic SEC Filing Analysis System - Single Developer Edition
Optimized for point-in-time deep forensic investigation with ML-powered fraud detection
Author: TIMMAYTHETOOLMANN
Date: 2025-11-11
"""

import asyncio
import hashlib
import json
import logging
import sqlite3
import warnings
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

warnings.filterwarnings("ignore")

# Scientific computing

# Async and performance
from functools import lru_cache

import lz4.frame
import numpy as np
import pandas as pd
import spacy

# NLP and ML
import torch
from sentence_transformers import SentenceTransformer
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from textstat import flesch_kincaid_grade, gunning_fog
from transformers import AutoModelForSequenceClassification, AutoTokenizer

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    import subprocess

    subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
    nlp = spacy.load("en_core_web_sm")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(f"forensic_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("FORENSIC_SYSTEM")

# ============================================================================
# CORE DATA STRUCTURES AND ENUMS
# ============================================================================


class Priority(Enum):
    """Investigation priority levels"""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFO = 5


class ViolationType(Enum):
    """Comprehensive violation catalog with penalties"""

    # 15 USC - Securities Laws
    USC_15_77g = ("Registration Requirements", "5 years", Priority.HIGH)
    USC_15_78j_b = ("Anti-Fraud (10b-5)", "20 years", Priority.CRITICAL)
    USC_15_78m = ("Periodic Reporting", "10 years", Priority.HIGH)
    USC_15_78p = ("Insider Trading", "20 years", Priority.CRITICAL)

    # 17 CFR - SEC Regulations
    CFR_17_229_303 = ("MD&A Deficiency", "Civil", Priority.MEDIUM)
    CFR_17_210 = ("Reg S-X Violation", "Civil", Priority.HIGH)
    CFR_17_240_10b5 = ("Rule 10b-5", "25 years via 18 USC 1348", Priority.CRITICAL)
    CFR_17_240_12b25 = ("Late Filing", "Civil", Priority.LOW)

    # 18 USC - Criminal
    USC_18_1001 = ("False Statements", "5 years", Priority.HIGH)
    USC_18_1341 = ("Mail Fraud", "20 years", Priority.CRITICAL)
    USC_18_1343 = ("Wire Fraud", "20 years", Priority.CRITICAL)
    USC_18_1348 = ("Securities Fraud", "25 years", Priority.CRITICAL)
    USC_18_1350 = ("SOX Certification", "20 years", Priority.CRITICAL)
    USC_18_1519 = ("Document Destruction", "20 years", Priority.CRITICAL)


@dataclass
class ForensicEvidence:
    """Immutable forensic evidence container with chain of custody"""

    evidence_id: str = field(
        default_factory=lambda: hashlib.sha256(str(datetime.utcnow()).encode()).hexdigest()[:16]
    )
    collected_at: datetime = field(default_factory=datetime.utcnow)
    source_type: str = ""  # SEC, GovInfo, Trading, etc.
    source_url: str = ""
    content_hash: str = ""
    content: bytes = b""
    metadata: Dict[str, Any] = field(default_factory=dict)
    chain_of_custody: List[Dict] = field(default_factory=list)

    def add_custody_event(self, action: str, actor: str = "SYSTEM") -> None:
        """Add custody chain event"""
        self.chain_of_custody.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": action,
                "actor": actor,
                "hash": hashlib.sha256(self.content).hexdigest()
                if self.content
                else self.content_hash,
            }
        )

    def verify_integrity(self) -> bool:
        """Verify evidence integrity"""
        if self.content:
            current_hash = hashlib.sha256(self.content).hexdigest()
            return current_hash == self.content_hash
        return True


@dataclass
class FraudIndicator:
    """Enhanced fraud indicator with complete forensic context"""

    indicator_type: str
    severity: float  # 0-1
    confidence: float  # 0-1
    evidence: List[str]
    ml_features: Dict[str, float]
    statute_violations: List[ViolationType]
    similar_cases: List[str]
    detection_method: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    @property
    def risk_score(self) -> float:
        """Composite risk score"""
        base_score = self.severity * self.confidence

        # Boost for criminal violations
        criminal_boost = sum(
            0.2 for v in self.statute_violations if v.value[2] == Priority.CRITICAL
        )

        return min(1.0, base_score + criminal_boost)

    @property
    def max_penalty(self) -> str:
        """Maximum criminal penalty exposure"""
        penalties = []
        for violation in self.statute_violations:
            penalty = violation.value[1]
            if "years" in penalty:
                years = int(penalty.split()[0])
                penalties.append(years)

        if penalties:
            return f"{max(penalties)} years"
        return "Civil penalties only"

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary"""
        return {
            "indicator_type": self.indicator_type,
            "severity": float(self.severity),
            "confidence": float(self.confidence),
            "evidence": list(self.evidence),
            "ml_features": {k: float(v) for k, v in self.ml_features.items()},
            "statute_violations": [v.name for v in self.statute_violations],
            "similar_cases": list(self.similar_cases),
            "detection_method": self.detection_method,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "risk_score": float(self.risk_score),
            "max_penalty": self.max_penalty,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FraudIndicator":
        """Create from dictionary"""
        data = data.copy()
        # Convert violation names back to enum
        if "statute_violations" in data:
            data["statute_violations"] = [
                ViolationType[v] if isinstance(v, str) else v for v in data["statute_violations"]
            ]
        # Convert timestamp string back to datetime
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        # Remove computed properties
        data.pop("risk_score", None)
        data.pop("max_penalty", None)
        return cls(**data)


# ============================================================================
# LOCAL DATABASE FOR EVIDENCE STORAGE
# ============================================================================


class ForensicDatabase:
    """SQLite-based local evidence storage with compression"""

    def __init__(self, db_path: str = "forensic_evidence.db"):
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()

        # Evidence table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evidence (
                evidence_id TEXT PRIMARY KEY,
                collected_at TIMESTAMP,
                source_type TEXT,
                source_url TEXT,
                content_hash TEXT UNIQUE,
                content_compressed BLOB,
                metadata TEXT,
                chain_of_custody TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Analysis results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_results (
                analysis_id TEXT PRIMARY KEY,
                evidence_id TEXT,
                cik TEXT,
                company_name TEXT,
                analysis_type TEXT,
                results TEXT,
                fraud_indicators TEXT,
                risk_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (evidence_id) REFERENCES evidence(evidence_id)
            )
        """)

        # Fraud patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fraud_patterns (
                pattern_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_name TEXT,
                pattern_embedding BLOB,
                description TEXT,
                similar_cases TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_hash ON evidence(content_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_analysis_cik ON analysis_results(cik)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_analysis_risk ON analysis_results(risk_score)"
        )

        self.conn.commit()

    def store_evidence(self, evidence: ForensicEvidence) -> bool:
        """Store evidence with compression"""
        try:
            # Compress content
            compressed = lz4.frame.compress(evidence.content) if evidence.content else b""

            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO evidence 
                (evidence_id, collected_at, source_type, source_url,
                  content_hash, content_compressed, metadata, chain_of_custody)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    evidence.evidence_id,
                    evidence.collected_at,
                    evidence.source_type,
                    evidence.source_url,
                    evidence.content_hash,
                    compressed,
                    json.dumps(evidence.metadata),
                    json.dumps(evidence.chain_of_custody),
                ),
            )
            self.conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to store evidence: {e}")
            return False

    def retrieve_evidence(
        self, evidence_id: str = None, content_hash: str = None
    ) -> Optional[ForensicEvidence]:
        """Retrieve evidence by ID or hash"""
        cursor = self.conn.cursor()

        if evidence_id:
            cursor.execute("SELECT * FROM evidence WHERE evidence_id = ?", (evidence_id,))
        elif content_hash:
            cursor.execute("SELECT * FROM evidence WHERE content_hash = ?", (content_hash,))
        else:
            return None

        row = cursor.fetchone()
        if row:
            # Decompress content
            content = (
                lz4.frame.decompress(row["content_compressed"])
                if row["content_compressed"]
                else b""
            )

            return ForensicEvidence(
                evidence_id=row["evidence_id"],
                collected_at=datetime.fromisoformat(row["collected_at"]),
                source_type=row["source_type"],
                source_url=row["source_url"],
                content_hash=row["content_hash"],
                content=content,
                metadata=json.loads(row["metadata"]),
                chain_of_custody=json.loads(row["chain_of_custody"]),
            )
        return None

    def store_analysis(self, analysis_id: str, evidence_id: str, results: Dict) -> bool:
        """Store analysis results"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO analysis_results 
                (analysis_id, evidence_id, cik, company_name, analysis_type, 
                 results, fraud_indicators, risk_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    analysis_id,
                    evidence_id,
                    results.get("cik", ""),
                    results.get("company_name", ""),
                    results.get("analysis_type", "comprehensive"),
                    json.dumps(results, default=str),
                    json.dumps(
                        [
                            fi.to_dict() if hasattr(fi, "to_dict") else asdict(fi)
                            for fi in results.get("fraud_indicators", [])
                        ],
                        default=str,
                    ),
                    results.get("risk_score", 0.0),
                ),
            )
            self.conn.commit()
            return True

        except Exception as e:
            logger.error(f"Failed to store analysis: {e}")
            logger.exception("Full traceback:")
            return False

    def get_high_risk_companies(self, threshold: float = 0.7) -> List[Dict]:
        """Get companies with high fraud risk"""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT cik, company_name, MAX(risk_score) as max_risk,
                    COUNT(*) as analysis_count
            FROM analysis_results
            WHERE risk_score >= ?
            GROUP BY cik, company_name
            ORDER BY max_risk DESC
        """,
            (threshold,),
        )

        return [dict(row) for row in cursor.fetchall()]


# ============================================================================
# ML-POWERED FRAUD DETECTION ENGINE
# ============================================================================


class MLFraudDetector:
    """Advanced ML fraud detection with transformers and traditional ML"""

    def __init__(self, cache_dir: str = "./model_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # Initialize models lazily
        self._finbert = None
        self._sentence_model = None
        self._isolation_forest = None
        self._fraud_patterns = None

    @property
    def finbert(self):
        """Lazy load FinBERT"""
        if self._finbert is None:
            try:
                logger.info("Loading FinBERT model...")
                tokenizer = AutoTokenizer.from_pretrained(
                    "yiyanghkust/finbert-tone", cache_dir=self.cache_dir
                )
                model = AutoModelForSequenceClassification.from_pretrained(
                    "yiyanghkust/finbert-tone", cache_dir=self.cache_dir
                )
                self._finbert = (tokenizer, model)
            except Exception as e:
                logger.warning(f"Failed to load FinBERT: {e}. Using fallback.")
                self._finbert = None
        return self._finbert

    @property
    def sentence_model(self):
        """Lazy load sentence transformer"""
        if self._sentence_model is None:
            logger.info("Loading sentence transformer...")
            self._sentence_model = SentenceTransformer(
                "all-MiniLM-L6-v2",  # Smaller, faster model
                cache_folder=self.cache_dir,
            )
        return self._sentence_model

    @property
    def isolation_forest(self):
        """Lazy load isolation forest"""
        if self._isolation_forest is None:
            self._isolation_forest = IsolationForest(
                contamination=0.1, random_state=42, n_estimators=100, n_jobs=-1
            )
        return self._isolation_forest

    @property
    def fraud_patterns(self) -> Dict[str, np.ndarray]:
        """Load fraud pattern embeddings"""
        if self._fraud_patterns is None:
            patterns = {
                "channel_stuffing": [
                    "accelerated shipments to meet quarterly targets",
                    "unusual spike in quarter-end revenues",
                    "distributors holding excess inventory",
                ],
                "revenue_manipulation": [
                    "premature revenue recognition before delivery",
                    "bill and hold arrangements without business purpose",
                    "round-trip transactions lacking economic substance",
                ],
                "expense_manipulation": [
                    "capitalizing ordinary operating expenses",
                    "understating reserves and allowances",
                    "cookie jar reserves manipulation",
                ],
                "disclosure_fraud": [
                    "omitting material adverse information",
                    "misleading non-GAAP reconciliations",
                    "hiding related party transactions",
                ],
            }

            self._fraud_patterns = {}
            for pattern_type, descriptions in patterns.items():
                embeddings = self.sentence_model.encode(descriptions)
                self._fraud_patterns[pattern_type] = embeddings

        return self._fraud_patterns

    @lru_cache(maxsize=128)
    def analyze_text_complexity(self, text: str) -> Dict[str, float]:
        """Analyze text complexity metrics"""
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 10]
        words = text.split()

        metrics = {
            "flesch_kincaid": flesch_kincaid_grade(text) if len(text) > 100 else 0,
            "gunning_fog": gunning_fog(text) if len(text) > 100 else 0,
            "avg_sentence_length": np.mean([len(s.split()) for s in sentences]) if sentences else 0,
            "unique_word_ratio": len(set(words)) / len(words) if words else 0,
            "hedge_word_ratio": self._count_hedge_words(text) / len(words) if words else 0,
        }

        return metrics

    def _count_hedge_words(self, text: str) -> int:
        """Count hedging/uncertainty words"""
        hedge_words = {
            "may",
            "might",
            "could",
            "possibly",
            "perhaps",
            "appear",
            "suggest",
            "seemingly",
            "arguably",
            "presumably",
            "allegedly",
            "reportedly",
            "uncertain",
            "unclear",
            "ambiguous",
        }

        words_lower = set(text.lower().split())
        return len(words_lower.intersection(hedge_words))

    async def detect_fraud_patterns(self, text: str, metadata: Dict = None) -> List[FraudIndicator]:
        """Detect fraud patterns using ML"""
        indicators = []

        # 1. Text Complexity Analysis
        complexity = self.analyze_text_complexity(text)

        if complexity["flesch_kincaid"] > 16:  # Very complex
            indicators.append(
                FraudIndicator(
                    indicator_type="COMPLEXITY_OBFUSCATION",
                    severity=0.6,
                    confidence=0.8,
                    evidence=[f"FK Grade: {complexity['flesch_kincaid']:.1f}"],
                    ml_features=complexity,
                    statute_violations=[ViolationType.CFR_17_229_303],
                    similar_cases=["Enron", "Wirecard"],
                    detection_method="Text Complexity Analysis",
                )
            )

        # 2. Sentiment Analysis
        sentiment_scores = await self._analyze_sentiment(text[:5000])  # First 5000 chars

        if sentiment_scores["negative"] > 0.6 and complexity["hedge_word_ratio"] > 0.05:
            indicators.append(
                FraudIndicator(
                    indicator_type="NEGATIVE_HEDGED_DISCLOSURE",
                    severity=0.5,
                    confidence=sentiment_scores["negative"],
                    evidence=["High negative sentiment with hedging language"],
                    ml_features=sentiment_scores,
                    statute_violations=[ViolationType.USC_15_78m],
                    similar_cases=["Lehman Brothers"],
                    detection_method="Sentiment Analysis",
                )
            )

        # 3. Pattern Matching
        text_embedding = self.sentence_model.encode([text[:2000]])[0]

        for pattern_type, pattern_embeddings in self.fraud_patterns.items():
            similarities = [
                np.dot(text_embedding, emb) / (np.linalg.norm(text_embedding) * np.linalg.norm(emb))
                for emb in pattern_embeddings
            ]
            max_sim = max(similarities)

            if max_sim > 0.75:  # High similarity
                indicators.append(
                    FraudIndicator(
                        indicator_type=f"PATTERN_{pattern_type.upper()}",
                        severity=0.8,
                        confidence=max_sim,
                        evidence=[f"Matches {pattern_type} pattern"],
                        ml_features={"similarity": max_sim},
                        statute_violations=self._map_pattern_to_violations(pattern_type),
                        similar_cases=self._get_similar_cases(pattern_type),
                        detection_method="Pattern Matching",
                    )
                )

        # 4. Entity Extraction
        doc = nlp(text[:5000])
        entities = {"PERSON": [], "ORG": [], "MONEY": [], "PERCENT": []}

        for ent in doc.ents:
            if ent.label_ in entities:
                entities[ent.label_].append(ent.text)

        # Check for shell company indicators
        if len(entities["ORG"]) > 10 and "subsidiary" in text.lower():
            indicators.append(
                FraudIndicator(
                    indicator_type="COMPLEX_ENTITY_STRUCTURE",
                    severity=0.4,
                    confidence=0.6,
                    evidence=[f"Found {len(entities['ORG'])} organizations"],
                    ml_features={"org_count": len(entities["ORG"])},
                    statute_violations=[ViolationType.USC_15_78j_b],
                    similar_cases=["Parmalat"],
                    detection_method="Entity Analysis",
                )
            )

        return indicators

    async def _analyze_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment using FinBERT"""
        if self.finbert is None:
            # Fallback if model not available
            return {"positive": 0.3, "negative": 0.3, "neutral": 0.4, "volatility": 0.1}

        tokenizer, model = self.finbert

        # Split into sentences
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20][:20]

        sentiments = []
        for sentence in sentences:
            inputs = tokenizer(
                sentence, return_tensors="pt", truncation=True, max_length=512, padding=True
            )

            with torch.no_grad():
                outputs = model(**inputs)
                probs = torch.softmax(outputs.logits, dim=-1).numpy()[0]
                sentiments.append(
                    {
                        "positive": float(probs[0]),
                        "negative": float(probs[1]),
                        "neutral": float(probs[2]),
                    }
                )

        if sentiments:
            df = pd.DataFrame(sentiments)
            return {
                "positive": float(df["positive"].mean()),
                "negative": float(df["negative"].mean()),
                "neutral": float(df["neutral"].mean()),
                "volatility": float(df.std().mean()),
            }

        return {"positive": 0, "negative": 0, "neutral": 1, "volatility": 0}

    def _map_pattern_to_violations(self, pattern: str) -> List[ViolationType]:
        """Map fraud patterns to violations"""
        mapping = {
            "channel_stuffing": [ViolationType.USC_15_78j_b, ViolationType.USC_18_1343],
            "revenue_manipulation": [ViolationType.USC_15_78j_b, ViolationType.USC_18_1348],
            "expense_manipulation": [ViolationType.USC_15_78m, ViolationType.USC_18_1001],
            "disclosure_fraud": [ViolationType.USC_15_78m, ViolationType.CFR_17_229_303],
        }
        return mapping.get(pattern, [ViolationType.USC_15_78j_b])

    def _get_similar_cases(self, pattern: str) -> List[str]:
        """Get similar historical cases"""
        cases = {
            "channel_stuffing": ["Bristol-Myers", "Sunbeam", "Symbol Tech"],
            "revenue_manipulation": ["Enron", "WorldCom", "Luckin Coffee"],
            "expense_manipulation": ["WorldCom", "Waste Management"],
            "disclosure_fraud": ["Theranos", "Nikola", "Wirecard"],
        }
        return cases.get(pattern, ["Unknown"])

    def detect_financial_anomalies(
        self, financials: pd.DataFrame, peer_data: pd.DataFrame = None
    ) -> List[FraudIndicator]:
        """Detect anomalies in financial metrics"""
        indicators = []

        if financials.empty:
            return indicators

        # Key ratios to analyze
        key_metrics = {
            "revenue_growth": lambda df: df["Revenue"].pct_change(),
            "gross_margin": lambda df: (df["Revenue"] - df["COGS"]) / df["Revenue"],
            "operating_margin": lambda df: df["OperatingIncome"] / df["Revenue"],
            "current_ratio": lambda df: df["CurrentAssets"] / df["CurrentLiabilities"],
            "dso": lambda df: (df["Receivables"] / df["Revenue"]) * 365,
        }

        # Calculate metrics
        calculated_metrics = {}
        for metric_name, calc_func in key_metrics.items():
            try:
                calculated_metrics[metric_name] = calc_func(financials)
            except:
                continue

        # 1. Temporal Anomaly Detection
        if len(financials) > 4:
            features = pd.DataFrame(calculated_metrics).fillna(0).values

            if features.shape[0] > 1:
                # Scale features
                scaler = StandardScaler()
                scaled = scaler.fit_transform(features)

                # Detect anomalies
                predictions = self.isolation_forest.fit_predict(scaled)
                anomaly_scores = self.isolation_forest.score_samples(scaled)

                # Flag anomalous periods
                anomaly_periods = np.where(predictions == -1)[0]

                if len(anomaly_periods) > 0:
                    indicators.append(
                        FraudIndicator(
                            indicator_type="TEMPORAL_FINANCIAL_ANOMALY",
                            severity=0.7,
                            confidence=abs(float(anomaly_scores[anomaly_periods].mean())),
                            evidence=[f"Anomalies in periods: {list(anomaly_periods)}"],
                            ml_features={"anomaly_score": float(anomaly_scores.mean())},
                            statute_violations=[ViolationType.USC_15_78m],
                            similar_cases=["Autonomy", "Computer Associates"],
                            detection_method="Isolation Forest",
                        )
                    )

        # 2. Peer Comparison (if available)
        if peer_data is not None and not peer_data.empty:
            for metric_name, values in calculated_metrics.items():
                if metric_name in peer_data.columns:
                    company_value = values.iloc[-1] if hasattr(values, "iloc") else values[-1]
                    peer_mean = peer_data[metric_name].mean()
                    peer_std = peer_data[metric_name].std()

                    if peer_std > 0:
                        z_score = (company_value - peer_mean) / peer_std

                        if abs(z_score) > 3:  # 3 sigma outlier
                            indicators.append(
                                FraudIndicator(
                                    indicator_type=f"PEER_OUTLIER_{metric_name.upper()}",
                                    severity=min(1.0, abs(z_score) / 5),
                                    confidence=0.8,
                                    evidence=[f"Z-score: {z_score:.2f}"],
                                    ml_features={"z_score": z_score, "metric": metric_name},
                                    statute_violations=[ViolationType.USC_15_78j_b],
                                    similar_cases=["Valeant"],
                                    detection_method="Peer Analysis",
                                )
                            )

        # 3. Benford's Law Check
        for column in ["Revenue", "Assets", "Liabilities"]:
            if column in financials.columns:
                values = financials[column].dropna()
                if len(values) > 10:
                    first_digits = [int(str(abs(x))[0]) for x in values if x != 0]
                    if first_digits:
                        observed_freq = (
                            pd.Series(first_digits).value_counts(normalize=True).sort_index()
                        )
                        benford_freq = pd.Series(
                            [np.log10(1 + 1 / d) for d in range(1, 10)], index=range(1, 10)
                        )

                        # Chi-square test
                        chi_stat = sum(
                            (observed_freq.get(i, 0) - benford_freq[i]) ** 2 / benford_freq[i]
                            for i in range(1, 10)
                        )

                        if chi_stat > 15:  # Significant deviation
                            indicators.append(
                                FraudIndicator(
                                    indicator_type=f"BENFORD_VIOLATION_{column.upper()}",
                                    severity=0.6,
                                    confidence=min(1.0, chi_stat / 30),
                                    evidence=[f"Chi-square: {chi_stat:.2f}"],
                                    ml_features={"chi_square": chi_stat},
                                    statute_violations=[ViolationType.USC_18_1001],
                                    similar_cases=["Crazy Eddie"],
                                    detection_method="Benford's Law",
                                )
                            )

        return indicators


# ============================================================================
# SEC EDGAR DATA ACQUISITION
# ============================================================================


class SECDataAcquisition:
    """Optimized SEC EDGAR data acquisition with caching"""

    def __init__(self, database: ForensicDatabase):
        self.db = database
        self.session = None
        self.rate_limit_delay = 0.1  # 10 requests per second
        self.last_request_time = 0

    async def __aenter__(self):
        """Async context manager entry"""
        import os

        timeout = aiohttp.ClientTimeout(total=30)
        headers = {
            "User-Agent": os.environ.get(
                "SEC_USER_AGENT", "Forensic Analysis System forensic@investigation.local"
            ),
            "Accept": "application/json",
        }
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def _rate_limit(self):
        """Enforce SEC rate limits"""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = asyncio.get_event_loop().time()

    async def get_company_filings(self, cik: str, form_types: List[str] = None) -> List[Dict]:
        """Get company filing metadata"""
        # Normalize CIK
        cik = str(cik).zfill(10)

        # Check cache first
        cache_key = f"filings_{cik}_{form_types}"
        cached = self.db.retrieve_evidence(evidence_id=cache_key)

        if cached and (datetime.utcnow() - cached.collected_at).days < 1:
            return json.loads(cached.content.decode())

        # Fetch from SEC
        await self._rate_limit()

        url = f"https://data.sec.gov/submissions/CIK{cik}.json"

        async with self.session.get(url) as response:
            if response.status != 200:
                logger.error(f"SEC API error: {response.status}")
                return []

            data = await response.json()

        # Parse filings
        filings = []
        recent = data.get("filings", {}).get("recent", {})

        for i in range(len(recent.get("form", []))):
            form = recent["form"][i]

            if form_types and form not in form_types:
                continue

            filing = {
                "cik": cik,
                "form_type": form,
                "filing_date": recent["filingDate"][i],
                "report_date": recent.get("reportDate", [None] * len(recent["form"]))[i],
                "accession_number": recent["accessionNumber"][i],
                "file_number": recent.get("fileNumber", [None] * len(recent["form"]))[i],
                "size": recent.get("size", [0] * len(recent["form"]))[i],
            }

            filings.append(filing)

        # Cache results
        evidence = ForensicEvidence(
            evidence_id=cache_key,
            source_type="SEC_METADATA",
            source_url=url,
            content=json.dumps(filings).encode(),
            content_hash=hashlib.sha256(json.dumps(filings).encode()).hexdigest(),
        )
        self.db.store_evidence(evidence)

        return filings

    async def download_filing(
        self, accession_number: str, cik: str = None
    ) -> Optional[ForensicEvidence]:
        """Download filing content"""
        # Check if already downloaded
        acc_clean = accession_number.replace("-", "")
        cached = self.db.retrieve_evidence(evidence_id=acc_clean)

        if cached:
            logger.info(f"Using cached filing: {accession_number}")
            return cached

        # Download from SEC
        await self._rate_limit()

        # Extract CIK from accession number if not provided
        # Accession format: 0000320187-19-000010
        if not cik and len(accession_number.split("-")) >= 2:
            cik = accession_number.split("-")[0]

        if not cik:
            logger.error(f"Cannot determine CIK for accession: {accession_number}")
            return None

        # Remove leading zeros from CIK for URL
        cik_no_leading = str(int(cik))

        # SEC EDGAR URL format: /Archives/edgar/data/{cik}/{accession_no_dashes}/{accession_with_dashes}.txt
        url = f"https://www.sec.gov/Archives/edgar/data/{cik_no_leading}/{acc_clean}/{accession_number}.txt"

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    # Try alternative index.html format
                    url_alt = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik_no_leading}&accession_number={accession_number}&xbrl_type=v"
                    async with self.session.get(url_alt) as response2:
                        if response2.status != 200:
                            logger.error(
                                f"Failed to download filing {accession_number}: {response.status} (tried {url})"
                            )
                            return None
                        content = await response2.read()
                else:
                    content = await response.read()
        except Exception as e:
            logger.error(f"Exception downloading filing {accession_number}: {e}")
            return None

        # Create evidence record
        evidence = ForensicEvidence(
            evidence_id=acc_clean,
            source_type="SEC_FILING",
            source_url=url,
            content=content,
            content_hash=hashlib.sha256(content).hexdigest(),
            metadata={
                "accession_number": accession_number,
                "download_time": datetime.utcnow().isoformat(),
            },
        )

        evidence.add_custody_event("DOWNLOADED", "SEC_EDGAR")

        # Store in database
        self.db.store_evidence(evidence)

        return evidence


# ============================================================================
# UNIFIED FORENSIC INVESTIGATION ORCHESTRATOR
# ============================================================================


class ForensicInvestigator:
    """Main investigation orchestrator - single point of control"""

    def __init__(self, db_path: str = "forensic_evidence.db"):
        self.db = ForensicDatabase(db_path)
        self.ml_detector = MLFraudDetector()
        self.sec_client = None
        self.investigation_id = None
        self.results = {}

    async def investigate_company(
        self, cik: str, years_back: int = 3, forms: List[str] = None, max_filings: int = 20
    ) -> Dict[str, Any]:
        """Execute comprehensive forensic investigation

        Args:
            cik: Company CIK number
            years_back: Years of history to analyze
            forms: List of form types to analyze
            max_filings: Maximum number of filings to analyze (default 20)
        """

        self.investigation_id = hashlib.sha256(f"{cik}_{datetime.utcnow()}".encode()).hexdigest()[
            :16
        ]

        logger.info(f"Starting investigation {self.investigation_id} for CIK {cik}")

        start_time = datetime.utcnow()

        # Default forms to analyze
        if forms is None:
            forms = ["10-K", "10-Q", "8-K", "DEF 14A", "10-K/A", "10-Q/A"]

        self.results = {
            "investigation_id": self.investigation_id,
            "cik": cik,
            "start_time": start_time.isoformat(),
            "forms_analyzed": forms,
            "years_back": years_back,
            "filings_analyzed": 0,
            "fraud_indicators": [],
            "risk_score": 0.0,
            "criminal_exposure": [],
            "civil_exposure": [],
            "executive_summary": "",
            "recommendations": [],
        }

        try:
            async with SECDataAcquisition(self.db) as sec_client:
                self.sec_client = sec_client

                # 1. Get filing metadata
                logger.info("Fetching filing metadata...")
                filings = await sec_client.get_company_filings(cik, forms)

                # Filter by date
                cutoff_date = datetime.now() - timedelta(days=years_back * 365)
                recent_filings = [
                    f
                    for f in filings
                    if datetime.strptime(f["filing_date"], "%Y-%m-%d") >= cutoff_date
                ]

                logger.info(f"Found {len(recent_filings)} filings to analyze")

                # Apply user-specified limit
                filings_to_analyze = recent_filings[:max_filings]
                self.results["filings_analyzed"] = len(filings_to_analyze)

                logger.info(
                    f"Analyzing {len(filings_to_analyze)} filings (user limit: {max_filings})"
                )

                # 2. Analyze each filing
                for filing in filings_to_analyze:
                    await self._analyze_filing(filing)

                # 3. Detect patterns across filings
                self._detect_cross_filing_patterns(recent_filings)

                # 4. Calculate final risk score
                self._calculate_risk_score()

                # 5. Generate recommendations
                self._generate_recommendations()

                # 6. Create executive summary
                self._create_executive_summary()

                # 7. Store results
                self.db.store_analysis(
                    self.investigation_id, self.results.get("primary_evidence_id", ""), self.results
                )

        except Exception as e:
            logger.error(f"Investigation failed: {e}")
            self.results["error"] = str(e)

        self.results["end_time"] = datetime.utcnow().isoformat()
        self.results["duration_seconds"] = (datetime.utcnow() - start_time).total_seconds()

        logger.info(f"Investigation complete. Risk score: {self.results['risk_score']:.2%}")

        return self.results

    async def _analyze_filing(self, filing: Dict):
        """Analyze individual filing"""
        try:
            # Download filing
            cik = filing.get("cik") or self.results.get("cik")
            evidence = await self.sec_client.download_filing(filing["accession_number"], cik=cik)

            if not evidence:
                return

            # Store as primary evidence if first filing
            if not self.results.get("primary_evidence_id"):
                self.results["primary_evidence_id"] = evidence.evidence_id

            # Extract text content
            text = evidence.content.decode("utf-8", errors="ignore")

            # ML fraud detection
            fraud_indicators = await self.ml_detector.detect_fraud_patterns(
                text[:50000],  # Analyze first 50k chars
                metadata=filing,
            )

            # Add filing context to indicators
            for indicator in fraud_indicators:
                indicator.evidence.append(
                    f"Filing: {filing['form_type']} on {filing['filing_date']}"
                )

            self.results["fraud_indicators"].extend(fraud_indicators)

            # Check for specific red flags
            self._check_filing_red_flags(filing, text)

        except Exception as e:
            logger.error(f"Failed to analyze filing {filing['accession_number']}: {e}")

    def _check_filing_red_flags(self, filing: Dict, text: str):
        """Check for specific red flag conditions"""

        # Late filing without NT
        if filing.get("report_date"):
            filing_date = datetime.strptime(filing["filing_date"], "%Y-%m-%d")
            report_date = datetime.strptime(filing["report_date"], "%Y-%m-%d")
            delay_days = (filing_date - report_date).days

            # Check deadlines by form type
            deadlines = {"10-K": 90, "10-Q": 45, "8-K": 4}

            form_base = filing["form_type"].replace("/A", "")
            if form_base in deadlines and delay_days > deadlines[form_base]:
                if "NT" not in filing["form_type"]:
                    self.results["fraud_indicators"].append(
                        FraudIndicator(
                            indicator_type="LATE_FILING_NO_NT",
                            severity=0.5,
                            confidence=1.0,
                            evidence=[f"Filed {delay_days} days late without NT"],
                            ml_features={"delay_days": delay_days},
                            statute_violations=[ViolationType.CFR_17_240_12b25],
                            similar_cases=["Multiple SEC enforcement actions"],
                            detection_method="Filing Analysis",
                        )
                    )

        # Amendment red flags
        if "/A" in filing["form_type"]:
            # Check for restatement language
            if any(word in text.lower() for word in ["restatement", "restated", "restate"]):
                self.results["fraud_indicators"].append(
                    FraudIndicator(
                        indicator_type="RESTATEMENT",
                        severity=0.8,
                        confidence=0.9,
                        evidence=["Filing contains restatement"],
                        ml_features={"has_restatement": 1},
                        statute_violations=[ViolationType.USC_15_78m, ViolationType.USC_18_1350],
                        similar_cases=["Hertz", "GE"],
                        detection_method="Keyword Detection",
                    )
                )

        # 8-K specific checks
        if "8-K" in filing["form_type"]:
            critical_items = {
                "1.01": ("Bankruptcy", ViolationType.USC_15_78m),
                "2.04": ("Triggering Events", ViolationType.USC_15_78m),
                "4.01": ("Auditor Change", ViolationType.CFR_17_229_303),
                "4.02": ("Non-Reliance on Financials", ViolationType.USC_18_1350),
                "5.02": ("Officer Departure", ViolationType.USC_15_78m),
            }

            for item_code, (description, violation) in critical_items.items():
                if f"Item {item_code}" in text or f"ITEM {item_code}" in text:
                    self.results["fraud_indicators"].append(
                        FraudIndicator(
                            indicator_type=f"8K_CRITICAL_{description.upper().replace(' ', '_')}",
                            severity=0.7,
                            confidence=1.0,
                            evidence=[f"8-K Item {item_code}: {description}"],
                            ml_features={"item_code": item_code},
                            statute_violations=[violation],
                            similar_cases=["Various"],
                            detection_method="8-K Analysis",
                        )
                    )

    def _detect_cross_filing_patterns(self, filings: List[Dict]):
        """Detect patterns across multiple filings"""

        if len(filings) < 2:
            return

        # Sort by date
        filings_sorted = sorted(filings, key=lambda x: x["filing_date"])

        # 1. Amendment frequency
        amendment_count = sum(1 for f in filings if "/A" in f["form_type"])
        if amendment_count > 3:
            self.results["fraud_indicators"].append(
                FraudIndicator(
                    indicator_type="EXCESSIVE_AMENDMENTS",
                    severity=0.6,
                    confidence=0.8,
                    evidence=[f"{amendment_count} amendments in {len(filings)} filings"],
                    ml_features={"amendment_ratio": amendment_count / len(filings)},
                    statute_violations=[ViolationType.USC_15_78m],
                    similar_cases=["Under Armour"],
                    detection_method="Pattern Analysis",
                )
            )

        # 2. Filing velocity changes
        filing_dates = [datetime.strptime(f["filing_date"], "%Y-%m-%d") for f in filings_sorted]
        if len(filing_dates) > 5:
            # Calculate filing intervals
            intervals = [
                (filing_dates[i + 1] - filing_dates[i]).days for i in range(len(filing_dates) - 1)
            ]

            # Check for clustering (many filings in short period)
            short_intervals = [i for i in intervals if i < 7]
            if len(short_intervals) > 3:
                self.results["fraud_indicators"].append(
                    FraudIndicator(
                        indicator_type="FILING_CLUSTER",
                        severity=0.5,
                        confidence=0.7,
                        evidence=[f"{len(short_intervals)} filings within 7 days"],
                        ml_features={"cluster_count": len(short_intervals)},
                        statute_violations=[ViolationType.USC_15_78j_b],
                        similar_cases=["Various pre-bankruptcy filings"],
                        detection_method="Temporal Analysis",
                    )
                )

    def _calculate_risk_score(self):
        """Calculate overall risk score"""

        if not self.results["fraud_indicators"]:
            self.results["risk_score"] = 0.0
            return

        # Weight by severity and confidence
        risk_scores = [indicator.risk_score for indicator in self.results["fraud_indicators"]]

        # Use max and mean combination
        if risk_scores:
            max_risk = max(risk_scores)
            mean_risk = np.mean(risk_scores)

            # Weighted combination (emphasize max)
            self.results["risk_score"] = 0.7 * max_risk + 0.3 * mean_risk

        # Identify criminal vs civil exposure
        for indicator in self.results["fraud_indicators"]:
            for violation in indicator.statute_violations:
                penalty = violation.value[1]
                priority = violation.value[2]

                if "years" in penalty and priority == Priority.CRITICAL:
                    self.results["criminal_exposure"].append(
                        {
                            "statute": violation.name,
                            "description": violation.value[0],
                            "max_penalty": penalty,
                        }
                    )
                elif priority in [Priority.HIGH, Priority.MEDIUM]:
                    self.results["civil_exposure"].append(
                        {
                            "statute": violation.name,
                            "description": violation.value[0],
                            "penalty": penalty,
                        }
                    )

        # Remove duplicates
        self.results["criminal_exposure"] = list(
            {v["statute"]: v for v in self.results["criminal_exposure"]}.values()
        )

        self.results["civil_exposure"] = list(
            {v["statute"]: v for v in self.results["civil_exposure"]}.values()
        )

    def _generate_recommendations(self):
        """Generate actionable recommendations"""

        recommendations = []
        risk_score = self.results["risk_score"]

        if risk_score > 0.8:
            recommendations.append(
                {
                    "priority": "IMMEDIATE",
                    "action": "Legal Counsel Consultation",
                    "reason": "Critical fraud indicators detected with criminal exposure",
                    "timeline": "Within 24 hours",
                }
            )

            recommendations.append(
                {
                    "priority": "IMMEDIATE",
                    "action": "Evidence Preservation",
                    "reason": "Secure all related documents and communications",
                    "timeline": "Immediately",
                }
            )

        if risk_score > 0.6:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "action": "SEC Whistleblower Evaluation",
                    "reason": f"Risk score {risk_score:.1%} qualifies for potential whistleblower award",
                    "timeline": "Within 1 week",
                }
            )

            recommendations.append(
                {
                    "priority": "HIGH",
                    "action": "Forensic Accounting Review",
                    "reason": "Deep dive into financial statements and disclosures",
                    "timeline": "Within 2 weeks",
                }
            )

        if self.results["criminal_exposure"]:
            recommendations.append(
                {
                    "priority": "CRITICAL",
                    "action": "Criminal Defense Attorney",
                    "reason": f"Potential exposure to {len(self.results['criminal_exposure'])} criminal statutes",
                    "timeline": "Immediately",
                }
            )

        if any("RESTATEMENT" in ind.indicator_type for ind in self.results["fraud_indicators"]):
            recommendations.append(
                {
                    "priority": "HIGH",
                    "action": "Analyze Restatement Impact",
                    "reason": "Quantify financial impact and identify responsible parties",
                    "timeline": "Within 1 week",
                }
            )

        self.results["recommendations"] = recommendations

    def _create_executive_summary(self):
        """Create executive summary"""

        risk_score = self.results["risk_score"]

        # Risk level classification
        if risk_score > 0.8:
            risk_level = "CRITICAL"
        elif risk_score > 0.6:
            risk_level = "HIGH"
        elif risk_score > 0.4:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Build summary
        summary_parts = [
            f"Investigation {self.investigation_id} completed.",
            f"Risk Level: {risk_level} ({risk_score:.1%} confidence).",
            f"Analyzed {self.results['filings_analyzed']} filings over {self.results['years_back']} years.",
            f"Identified {len(self.results['fraud_indicators'])} fraud indicators.",
        ]

        # Add top risks
        if self.results["fraud_indicators"]:
            top_risks = sorted(
                self.results["fraud_indicators"], key=lambda x: x.risk_score, reverse=True
            )[:3]

            risk_types = [r.indicator_type for r in top_risks]
            summary_parts.append(f"Primary concerns: {', '.join(risk_types)}.")

        # Add exposure summary
        if self.results["criminal_exposure"]:
            max_penalty = max(
                int(e["max_penalty"].split()[0])
                for e in self.results["criminal_exposure"]
                if "years" in e["max_penalty"]
            )
            summary_parts.append(f"Criminal exposure: up to {max_penalty} years.")

        # Add urgent action if needed
        if risk_score > 0.8:
            summary_parts.append(
                "IMMEDIATE ACTION REQUIRED - Consult legal counsel within 24 hours."
            )

        self.results["executive_summary"] = " ".join(summary_parts)

    def generate_report(self, output_path: str = None) -> str:
        """Generate formatted investigation report"""

        if output_path is None:
            output_path = f"investigation_{self.investigation_id}.json"

        # Convert fraud indicators to serializable format
        results_copy = self.results.copy()
        results_copy["fraud_indicators"] = [
            {
                "type": ind.indicator_type,
                "severity": ind.severity,
                "confidence": ind.confidence,
                "risk_score": ind.risk_score,
                "evidence": ind.evidence,
                "max_penalty": ind.max_penalty,
                "detection_method": ind.detection_method,
            }
            for ind in self.results["fraud_indicators"]
        ]

        # Save report
        with open(output_path, "w") as f:
            json.dump(results_copy, f, indent=2, default=str)

        logger.info(f"Report saved to {output_path}")

        return output_path


# ============================================================================
# MAIN EXECUTION
# ============================================================================


async def main():
    """Main execution function"""

    # Example investigation
    investigator = ForensicInvestigator()

    # Investigate a company (example CIK)
    cik = "0001318605"  # Tesla

    results = await investigator.investigate_company(
        cik=cik, years_back=2, forms=["10-K", "10-Q", "8-K"]
    )

    # Generate report
    report_path = investigator.generate_report()

    # Print summary
    print("\n" + "=" * 60)
    print("FORENSIC INVESTIGATION COMPLETE")
    print("=" * 60)
    print(f"Investigation ID: {results['investigation_id']}")
    print(f"Company CIK: {results['cik']}")
    print(f"Risk Score: {results['risk_score']:.1%}")
    print(f"Fraud Indicators: {len(results['fraud_indicators'])}")
    print(f"Criminal Exposure: {len(results['criminal_exposure'])} statutes")
    print(f"Civil Exposure: {len(results['civil_exposure'])} statutes")
    print("\nExecutive Summary:")
    print(results["executive_summary"])
    print(f"\nFull report: {report_path}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
