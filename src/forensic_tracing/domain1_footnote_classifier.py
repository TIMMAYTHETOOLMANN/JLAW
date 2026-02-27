"""
Domain 1: Form 4 Footnote Classification Engine
=================================================

Classifies Form 4 footnotes into 10 forensic risk categories using a
multi-phase approach: regex pattern matching, temporal analysis, entity
extraction, and anomaly scoring.

Based on EDGAR Ownership XML Technical Specification Version 5.1 (Schema X0508).
Footnotes use XML ID/IDREF linking: <footnote id="F1"> through <footnote id="F99">.

Ten categories of footnote content:
  1. Weighted average price explanations
  2. Beneficial ownership chain descriptions
  3. Rule 10b5-1 trading plan references
  4. Tax withholding / net settlement
  5. Vesting schedules and award terms
  6. Gift descriptions
  7. Derivative exercise/conversion terms
  8. Entity transfer explanations
  9. Code J "other" explanations
  10. Continuation footnotes

References:
    - EDGAR Ownership XML Technical Specification v5.1
    - SEC Rule 16a-3(g) (Form 4 reporting requirements)
    - Avci et al. (2024) "Insider Trading by Other Means" Harvard Bus. Law Rev.
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class FootnoteRiskCategory(Enum):
    """Risk classification for footnote content."""
    EXCULPATORY = 'exculpatory'
    LOW_RISK = 'low_risk'
    MEDIUM_RISK = 'medium_risk'
    HIGH_RISK = 'high_risk'
    CRITICAL = 'critical'


class FootnoteType(Enum):
    """Ten categories of Form 4 footnote content."""
    WEIGHTED_AVG_PRICE = 'weighted_average_price'
    BENEFICIAL_OWNERSHIP_CHAIN = 'beneficial_ownership_chain'
    RULE_10B5_1_PLAN = 'rule_10b5_1_plan'
    TAX_WITHHOLDING = 'tax_withholding'
    VESTING_SCHEDULE = 'vesting_schedule'
    GIFT_DESCRIPTION = 'gift_description'
    DERIVATIVE_TERMS = 'derivative_terms'
    ENTITY_TRANSFER = 'entity_transfer'
    CODE_J_EXPLANATION = 'code_j_explanation'
    CONTINUATION = 'continuation'
    UNKNOWN = 'unknown'


@dataclass
class FootnoteClassification:
    """Result of classifying a single Form 4 footnote."""
    footnote_id: str
    raw_text: str
    footnote_type: FootnoteType
    risk_category: FootnoteRiskCategory
    risk_score: float  # 0.0 to 1.0
    signals: List[str] = field(default_factory=list)
    entity_names_extracted: List[str] = field(default_factory=list)
    dates_extracted: List[str] = field(default_factory=list)
    plan_adoption_date: Optional[str] = None
    has_exculpatory_disclaimer: bool = False
    has_pecuniary_interest_disclaimer: bool = False
    is_code_j_without_explanation: bool = False

    def to_dict(self) -> dict:
        return {
            'footnote_id': self.footnote_id,
            'raw_text': self.raw_text[:200] + ('...' if len(self.raw_text) > 200 else ''),
            'footnote_type': self.footnote_type.value,
            'risk_category': self.risk_category.value,
            'risk_score': round(self.risk_score, 3),
            'signals': self.signals,
            'entity_names_extracted': self.entity_names_extracted,
            'dates_extracted': self.dates_extracted,
            'plan_adoption_date': self.plan_adoption_date,
            'has_exculpatory_disclaimer': self.has_exculpatory_disclaimer,
            'has_pecuniary_interest_disclaimer': self.has_pecuniary_interest_disclaimer,
            'is_code_j_without_explanation': self.is_code_j_without_explanation,
        }


class FootnoteClassifier:
    """
    Multi-phase Form 4 footnote classification engine.

    Phase 1: Regex pattern matching to classify by category and initial risk
    Phase 2: Temporal analysis (plan adoption dates vs. material events)
    Phase 3: Entity name extraction for ownership chain mapping
    Phase 4: Anomaly scoring for unusual or complex footnotes
    """

    # Phase 1 patterns: (regex, FootnoteType, base_risk_score)
    TYPE_PATTERNS = [
        # Category 1: Weighted average price
        (r'weighted\s+average', FootnoteType.WEIGHTED_AVG_PRICE, 0.10),
        (r'prices?\s+ranging\s+from', FootnoteType.WEIGHTED_AVG_PRICE, 0.10),
        (r'trade[\s-]by[\s-]trade\s+breakdowns?', FootnoteType.WEIGHTED_AVG_PRICE, 0.10),
        (r'average\s+(?:sale|purchase)\s+price', FootnoteType.WEIGHTED_AVG_PRICE, 0.10),

        # Category 2: Beneficial ownership chain
        (r'beneficially?\s+own(?:s|ed)', FootnoteType.BENEFICIAL_OWNERSHIP_CHAIN, 0.30),
        (r'indirect(?:ly)?\s+(?:own|held|through)', FootnoteType.BENEFICIAL_OWNERSHIP_CHAIN, 0.30),
        (r'except\s+to\s+the\s+extent\s+of\s+(?:his|her|its)\s+pecuniary\s+interest',
         FootnoteType.BENEFICIAL_OWNERSHIP_CHAIN, 0.25),
        (r'disclaims?\s+beneficial\s+ownership', FootnoteType.BENEFICIAL_OWNERSHIP_CHAIN, 0.20),
        (r'sole\s+(?:voting|dispositive)\s+power', FootnoteType.BENEFICIAL_OWNERSHIP_CHAIN, 0.35),
        (r'shared\s+(?:voting|dispositive)\s+power', FootnoteType.BENEFICIAL_OWNERSHIP_CHAIN, 0.35),

        # Category 3: Rule 10b5-1 plan
        (r'10b5[\s-]?1\s+(?:trading\s+)?plan', FootnoteType.RULE_10B5_1_PLAN, 0.15),
        (r'pre[\s-]?arranged\s+trading\s+plan', FootnoteType.RULE_10B5_1_PLAN, 0.15),
        (r'rule\s+10b5[\s-]?1', FootnoteType.RULE_10B5_1_PLAN, 0.15),
        (r'adopted\s+(?:a\s+)?(?:written\s+)?plan', FootnoteType.RULE_10B5_1_PLAN, 0.20),

        # Category 4: Tax withholding
        (r'tax\s+withholding', FootnoteType.TAX_WITHHOLDING, 0.05),
        (r'net\s+settlement', FootnoteType.TAX_WITHHOLDING, 0.05),
        (r'withheld\s+(?:by|to)\s+(?:the\s+)?(?:company|issuer)', FootnoteType.TAX_WITHHOLDING, 0.05),
        (r'satisfy\s+(?:tax|withholding)\s+obligations', FootnoteType.TAX_WITHHOLDING, 0.05),

        # Category 5: Vesting schedule
        (r'vest(?:s|ed|ing)', FootnoteType.VESTING_SCHEDULE, 0.10),
        (r'(?:restricted\s+stock|RSU)\s+(?:unit|award)', FootnoteType.VESTING_SCHEDULE, 0.10),
        (r'performance[\s-]based\s+(?:award|condition)', FootnoteType.VESTING_SCHEDULE, 0.15),
        (r'(?:quarterly|annual|monthly)\s+installments', FootnoteType.VESTING_SCHEDULE, 0.10),

        # Category 6: Gift description
        (r'bona\s+fide\s+gift', FootnoteType.GIFT_DESCRIPTION, 0.30),
        (r'gift(?:ed)?\s+(?:to|for)', FootnoteType.GIFT_DESCRIPTION, 0.35),
        (r'charitable\s+(?:gift|donation|contribution)', FootnoteType.GIFT_DESCRIPTION, 0.25),
        (r'no\s+consideration\s+(?:was\s+)?received', FootnoteType.GIFT_DESCRIPTION, 0.30),

        # Category 7: Derivative terms
        (r'conversion\s+(?:price|ratio|rate)', FootnoteType.DERIVATIVE_TERMS, 0.15),
        (r'exercise\s+price', FootnoteType.DERIVATIVE_TERMS, 0.15),
        (r'option\s+(?:expire|expiration)', FootnoteType.DERIVATIVE_TERMS, 0.15),
        (r'(?:put|call)\s+option', FootnoteType.DERIVATIVE_TERMS, 0.20),
        (r'swap\s+(?:agreement|arrangement)', FootnoteType.DERIVATIVE_TERMS, 0.45),

        # Category 8: Entity transfer
        (r'transferred?\s+to\s+(?:the\s+)?(?:[A-Z][\w\s,\.]+(?:LLC|Trust|LP|Foundation|Inc))',
         FootnoteType.ENTITY_TRANSFER, 0.40),
        (r'distribut(?:ed|ion)\s+(?:from|to|by)', FootnoteType.ENTITY_TRANSFER, 0.40),
        (r'shares?\s+held\s+by\s+(?:[A-Z][\w\s,\.]+(?:LLC|Trust|LP))',
         FootnoteType.ENTITY_TRANSFER, 0.35),

        # Category 9: Code J explanation
        (r'code\s+j', FootnoteType.CODE_J_EXPLANATION, 0.50),
        (r'other(?:\s+type\s+of)?\s+(?:acquisition|disposition)', FootnoteType.CODE_J_EXPLANATION, 0.45),
        (r'(?:deemed|constructive)\s+(?:acquisition|disposition)', FootnoteType.CODE_J_EXPLANATION, 0.50),

        # Category 10: Continuation
        (r'continued?\s+(?:from|in)\s+(?:footnote|note)', FootnoteType.CONTINUATION, 0.20),
        (r'see\s+(?:footnote|note)\s+(?:F?\d+)', FootnoteType.CONTINUATION, 0.20),
    ]

    # Exculpatory signal patterns (reduce risk)
    EXCULPATORY_PATTERNS = [
        r'10b5[\s-]?1\s+(?:trading\s+)?plan',
        r'tax\s+withholding',
        r'net\s+settlement',
        r'automatic\s+(?:vesting|conversion)',
        r'disclaims?\s+beneficial\s+ownership',
        r'pre[\s-]?arranged',
        r'regular\s+(?:quarterly|annual)\s+(?:vesting|award)',
    ]

    # Suspicious signal patterns (increase risk)
    SUSPICIOUS_PATTERNS = [
        (r'(?:late|untimely)\s+fil(?:ed|ing)', 0.20, 'Late filing language detected'),
        (r'code\s+j.*without\b', 0.30, 'Code J without adequate explanation'),
        (r'swap\s+(?:agreement|arrangement|transaction)', 0.25,
         'Swap agreement — economic results comparable to ownership'),
        (r'loan(?:ed)?\s+(?:shares|securities)', 0.25, 'Securities lending arrangement'),
        (r'pledge(?:d)?\s+(?:as\s+)?(?:collateral|security)', 0.20, 'Shares pledged as collateral'),
        (r'forward\s+(?:sale|contract|prepaid)', 0.30,
         'Forward sale contract — pre-arranged monetization'),
        (r'(?:retained|maintained?)\s+(?:economic|pecuniary)\s+interest', 0.25,
         'Retained economic interest after transfer'),
        (r'(?:voting|investment)\s+(?:power|control)\s+(?:retained|maintained)', 0.25,
         'Voting/investment control retained'),
        (r'(?:margin|collateral)\s+(?:account|agreement|call)', 0.20,
         'Margin account or collateral arrangement'),
    ]

    # Date extraction patterns
    DATE_PATTERNS = [
        r'(\d{1,2}/\d{1,2}/\d{2,4})',
        r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]

    # Entity name extraction patterns
    ENTITY_NAME_PATTERNS = [
        r'([A-Z][A-Za-z\s\.]+?)\s+(?:LLC|L\.L\.C\.)',
        r'([A-Z][A-Za-z\s\.]+?)\s+(?:Limited\s+)?Partnership',
        r'(?:the\s+)?([A-Z][A-Za-z\s\.]+?)\s+(?:Revocable\s+)?Trust',
        r'(?:the\s+)?([A-Z][A-Za-z\s\.]+?)\s+Irrevocable\s+Trust',
        r'(?:the\s+)?([A-Z][A-Za-z\s\.]+?)\s+Foundation',
        r'([A-Z][A-Za-z\s\.]+?)\s+GRAT',
        r'([A-Z][A-Za-z\s\.]+?)\s+(?:Holdings?\s+)?(?:Inc|Corp)',
    ]

    @classmethod
    def classify_footnote(cls, footnote_id: str, text: str,
                          transaction_code: str = '') -> FootnoteClassification:
        """
        Classify a single Form 4 footnote through all four phases.

        Args:
            footnote_id: The footnote ID (e.g., "F1")
            text: The footnote text content (up to 1000 chars per spec)
            transaction_code: Associated transaction code (A, M, G, J, S, etc.)

        Returns:
            FootnoteClassification with type, risk, and extracted signals
        """
        if not text or not text.strip():
            return FootnoteClassification(
                footnote_id=footnote_id,
                raw_text='',
                footnote_type=FootnoteType.UNKNOWN,
                risk_category=FootnoteRiskCategory.LOW_RISK,
                risk_score=0.0,
                signals=['Empty footnote'],
            )

        # Phase 1: Pattern matching for type and initial risk
        footnote_type, base_risk = cls._phase1_pattern_match(text)

        # Phase 2: Temporal analysis (extract dates, check for plan adoption)
        dates_found, plan_adoption_date = cls._phase2_temporal(text)

        # Phase 3: Entity name extraction
        entity_names = cls._phase3_entities(text)

        # Phase 4: Anomaly scoring
        signals = []
        risk_score = base_risk

        # Check exculpatory patterns (reduce risk)
        has_exculpatory = False
        for pattern in cls.EXCULPATORY_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                has_exculpatory = True
                risk_score = max(risk_score - 0.10, 0.0)
                break

        # Check pecuniary interest disclaimer
        has_pecuniary_disclaimer = bool(
            re.search(r'except\s+to\s+the\s+extent\s+of.*pecuniary\s+interest',
                       text, re.IGNORECASE)
        )

        # Check suspicious patterns (increase risk)
        for pattern, risk_add, signal_desc in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                risk_score += risk_add
                signals.append(signal_desc)

        # Code J without adequate explanation is a red flag
        is_code_j_no_explanation = False
        if transaction_code.upper() == 'J':
            if footnote_type == FootnoteType.UNKNOWN or len(text.strip()) < 50:
                is_code_j_no_explanation = True
                risk_score += 0.30
                signals.append(
                    'Code J transaction without adequate footnote explanation '
                    '(required by SEC rule)'
                )

        # Length-based anomaly: unusually complex footnotes
        if len(text) > 800:
            risk_score += 0.10
            signals.append(
                f'Unusually long footnote ({len(text)} chars) — may bury critical information'
            )

        # Entity transfer without disclaimer
        if footnote_type == FootnoteType.ENTITY_TRANSFER and not has_pecuniary_disclaimer:
            risk_score += 0.15
            signals.append(
                'Entity transfer footnote lacks pecuniary interest disclaimer'
            )

        # 10b5-1 plan without adoption date
        if footnote_type == FootnoteType.RULE_10B5_1_PLAN and not plan_adoption_date:
            risk_score += 0.10
            signals.append('10b5-1 plan referenced without adoption date')

        # Cap risk score
        risk_score = min(risk_score, 1.0)

        # Determine risk category
        if risk_score >= 0.60:
            risk_category = FootnoteRiskCategory.CRITICAL
        elif risk_score >= 0.40:
            risk_category = FootnoteRiskCategory.HIGH_RISK
        elif risk_score >= 0.20:
            risk_category = FootnoteRiskCategory.MEDIUM_RISK
        elif has_exculpatory:
            risk_category = FootnoteRiskCategory.EXCULPATORY
        else:
            risk_category = FootnoteRiskCategory.LOW_RISK

        return FootnoteClassification(
            footnote_id=footnote_id,
            raw_text=text,
            footnote_type=footnote_type,
            risk_category=risk_category,
            risk_score=risk_score,
            signals=signals,
            entity_names_extracted=entity_names,
            dates_extracted=dates_found,
            plan_adoption_date=plan_adoption_date,
            has_exculpatory_disclaimer=has_exculpatory,
            has_pecuniary_interest_disclaimer=has_pecuniary_disclaimer,
            is_code_j_without_explanation=is_code_j_no_explanation,
        )

    @classmethod
    def classify_all_footnotes(cls, footnotes: dict,
                               transaction_codes: dict = None) -> List[FootnoteClassification]:
        """
        Classify all footnotes from a Form 4 filing.

        Args:
            footnotes: Dict mapping footnote_id -> text (e.g., {"F1": "...", "F2": "..."})
            transaction_codes: Optional dict mapping footnote_id -> transaction_code

        Returns:
            List of FootnoteClassification objects
        """
        results = []
        codes = transaction_codes or {}
        for fid, text in footnotes.items():
            code = codes.get(fid, '')
            results.append(cls.classify_footnote(fid, text, code))
        return results

    @classmethod
    def _phase1_pattern_match(cls, text: str) -> tuple:
        """Phase 1: Classify footnote type via regex patterns."""
        best_type = FootnoteType.UNKNOWN
        best_risk = 0.15  # Default for unknown types

        for pattern, ftype, risk in cls.TYPE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                if risk > best_risk or best_type == FootnoteType.UNKNOWN:
                    best_type = ftype
                    best_risk = risk

        return best_type, best_risk

    @classmethod
    def _phase2_temporal(cls, text: str) -> tuple:
        """Phase 2: Extract dates and identify plan adoption dates."""
        dates_found = []
        for pattern in cls.DATE_PATTERNS:
            dates_found.extend(re.findall(pattern, text))

        # Check for 10b5-1 plan adoption date
        plan_adoption_date = None
        adoption_match = re.search(
            r'(?:adopted|entered\s+into|established)\s+(?:on\s+)?'
            r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2})',
            text, re.IGNORECASE
        )
        if adoption_match:
            plan_adoption_date = adoption_match.group(1)

        return dates_found, plan_adoption_date

    @classmethod
    def _phase3_entities(cls, text: str) -> list:
        """Phase 3: Extract entity names for ownership chain mapping."""
        entities = []
        for pattern in cls.ENTITY_NAME_PATTERNS:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                if len(name) > 2 and name not in entities:
                    entities.append(name)
        return entities

    @classmethod
    def generate_risk_summary(cls, classifications: List[FootnoteClassification]) -> dict:
        """Generate aggregate risk summary from all classified footnotes."""
        if not classifications:
            return {'total': 0, 'risk_distribution': {}, 'highest_risk_footnotes': []}

        risk_dist = {}
        for c in classifications:
            cat = c.risk_category.value
            risk_dist[cat] = risk_dist.get(cat, 0) + 1

        type_dist = {}
        for c in classifications:
            t = c.footnote_type.value
            type_dist[t] = type_dist.get(t, 0) + 1

        high_risk = sorted(
            [c for c in classifications if c.risk_score >= 0.40],
            key=lambda x: x.risk_score,
            reverse=True,
        )

        all_entities = []
        for c in classifications:
            all_entities.extend(c.entity_names_extracted)

        all_signals = []
        for c in classifications:
            all_signals.extend(c.signals)

        code_j_missing = [c for c in classifications if c.is_code_j_without_explanation]

        return {
            'total_footnotes': len(classifications),
            'risk_distribution': risk_dist,
            'type_distribution': type_dist,
            'highest_risk_footnotes': [c.to_dict() for c in high_risk[:10]],
            'all_extracted_entities': list(set(all_entities)),
            'all_signals': all_signals,
            'code_j_missing_explanations': len(code_j_missing),
            'average_risk_score': round(
                sum(c.risk_score for c in classifications) / len(classifications), 3
            ),
        }
