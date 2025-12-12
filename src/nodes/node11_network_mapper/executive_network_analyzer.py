"""
NODE 11: Executive Network Mapper
=================================

Relationship/network analysis for detecting:
- Board interlocks (shared directors across companies)
- Shared advisors (same law firm, auditor, compensation consultant)
- Revolving door patterns (executives moving between companies)
- Coordinated trading activity across connected executives

Note: This implementation uses in-memory graph structures.
For production, integrate with Neo4j using neo4j-driver.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Set, Tuple
from enum import Enum
from collections import defaultdict
import hashlib
import logging

logger = logging.getLogger(__name__)


class NetworkAlertType(Enum):
    BOARD_INTERLOCK = "Board Interlock"
    SHARED_ADVISOR = "Shared Advisor"
    REVOLVING_DOOR = "Revolving Door"
    COORDINATED_ACTIVITY = "Coordinated Trading Activity"


class AdvisorType(Enum):
    LEGAL = "Legal"
    ACCOUNTING = "Accounting"
    COMPENSATION = "Compensation Consultant"
    INVESTMENT_BANK = "Investment Bank"
    OTHER = "Other"


@dataclass
class Person:
    """Executive or director."""
    person_id: str
    name: str
    positions: List[Dict[str, Any]] = field(default_factory=list)
    advisors: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Company:
    """Company entity."""
    cik: str
    name: str
    ticker: Optional[str] = None


@dataclass
class Position:
    """Position/role at a company."""
    person_id: str
    company_cik: str
    title: str
    is_director: bool
    is_officer: bool
    start_date: Optional[date] = None
    end_date: Optional[date] = None


@dataclass
class Advisor:
    """Shared advisor entity."""
    advisor_id: str
    name: str
    advisor_type: AdvisorType


@dataclass
class NetworkAlert:
    """Alert for network relationship findings."""
    alert_type: NetworkAlertType
    involved_parties: List[Dict[str, Any]]
    connection_path: List[str]
    connection_strength: float
    risk_indicators: List[str]
    correlated_transactions: Optional[List[Dict[str, Any]]] = None
    evidence_hash: str = ""
    severity: str = "MEDIUM"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_type": self.alert_type.value,
            "involved_parties": self.involved_parties,
            "connection_path": self.connection_path,
            "connection_strength": round(self.connection_strength, 3),
            "risk_indicators": self.risk_indicators,
            "severity": self.severity
        }


@dataclass
class Node11Output:
    """Output from Node 11 analysis."""
    persons_analyzed: int
    companies_analyzed: int
    relationships_found: int
    alerts: List[NetworkAlert]
    board_interlocks: int
    shared_advisors: int
    revolving_doors: int
    coordinated_activities: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "persons_analyzed": self.persons_analyzed,
                "companies_analyzed": self.companies_analyzed,
                "relationships_found": self.relationships_found,
                "board_interlocks": self.board_interlocks,
                "shared_advisors": self.shared_advisors,
                "revolving_doors": self.revolving_doors,
                "coordinated_activities": self.coordinated_activities
            },
            "alerts": [a.to_dict() for a in self.alerts],
            "timestamp": self.timestamp.isoformat()
        }


class ExecutiveNetworkAnalyzer:
    """
    Executive Network Mapper.
    
    Builds and analyzes relationship graphs to detect:
    1. Board interlocks - Shared directors across companies
    2. Shared advisors - Same professional service providers
    3. Revolving door - Executive movement patterns
    4. Coordinated activity - Suspicious trading correlations
    """
    
    def __init__(self):
        # In-memory graph storage
        self.persons: Dict[str, Person] = {}
        self.companies: Dict[str, Company] = {}
        self.positions: List[Position] = []
        self.advisors: Dict[str, Advisor] = {}
        
        # Relationship indices
        self._person_companies: Dict[str, Set[str]] = defaultdict(set)  # person_id -> company_ciks
        self._company_persons: Dict[str, Set[str]] = defaultdict(set)  # company_cik -> person_ids
        self._company_advisors: Dict[str, Set[str]] = defaultdict(set)  # company_cik -> advisor_ids
        self._advisor_companies: Dict[str, Set[str]] = defaultdict(set)  # advisor_id -> company_ciks
    
    def load_executives(self, executives: List[Dict[str, Any]]) -> None:
        """
        Load executive/director data into the network.
        
        Args:
            executives: List of executive records with positions
        """
        for exec_data in executives:
            person_id = exec_data.get('person_id') or exec_data.get('id')
            if not person_id:
                continue
            
            person = Person(
                person_id=person_id,
                name=exec_data.get('name', 'Unknown'),
                positions=exec_data.get('positions', []),
                advisors=exec_data.get('advisors', [])
            )
            self.persons[person_id] = person
            
            # Index positions
            for pos in person.positions:
                company_cik = pos.get('company_cik') or pos.get('cik')
                if company_cik:
                    self._person_companies[person_id].add(company_cik)
                    self._company_persons[company_cik].add(person_id)
                    
                    # Add position record
                    self.positions.append(Position(
                        person_id=person_id,
                        company_cik=company_cik,
                        title=pos.get('title', ''),
                        is_director=pos.get('is_director', False),
                        is_officer=pos.get('is_officer', False),
                        start_date=pos.get('start_date'),
                        end_date=pos.get('end_date')
                    ))
            
            # Index advisors
            for adv in person.advisors:
                advisor_id = adv.get('advisor_id')
                if advisor_id:
                    if advisor_id not in self.advisors:
                        self.advisors[advisor_id] = Advisor(
                            advisor_id=advisor_id,
                            name=adv.get('advisor_name', 'Unknown'),
                            advisor_type=AdvisorType(adv.get('advisor_type', 'Other'))
                        )
                    
                    # Link to companies through person
                    for cik in self._person_companies[person_id]:
                        self._company_advisors[cik].add(advisor_id)
                        self._advisor_companies[advisor_id].add(cik)
        
        logger.info(f"[NODE 11] Loaded {len(self.persons)} executives, {len(self.positions)} positions")
    
    def analyze(
        self,
        form4_trades: Optional[List[Dict[str, Any]]] = None
    ) -> Node11Output:
        """
        Run complete network analysis.
        
        Args:
            form4_trades: Optional Form 4 trades for coordinated activity detection
            
        Returns:
            Node11Output with all analysis results
        """
        logger.info("[NODE 11] Analyzing executive network")
        
        alerts = []
        
        # Detect board interlocks
        interlock_alerts = self.detect_board_interlocks()
        alerts.extend(interlock_alerts)
        
        # Detect shared advisors
        advisor_alerts = self.detect_shared_advisors()
        alerts.extend(advisor_alerts)
        
        # Detect revolving door patterns
        revolving_alerts = self.detect_revolving_door()
        alerts.extend(revolving_alerts)
        
        # Detect coordinated trading
        if form4_trades:
            coord_alerts = self.detect_coordinated_activity(form4_trades)
            alerts.extend(coord_alerts)
        
        return Node11Output(
            persons_analyzed=len(self.persons),
            companies_analyzed=len(set(
                cik for ciks in self._person_companies.values() for cik in ciks
            )),
            relationships_found=len(self.positions),
            alerts=alerts,
            board_interlocks=len([a for a in alerts if a.alert_type == NetworkAlertType.BOARD_INTERLOCK]),
            shared_advisors=len([a for a in alerts if a.alert_type == NetworkAlertType.SHARED_ADVISOR]),
            revolving_doors=len([a for a in alerts if a.alert_type == NetworkAlertType.REVOLVING_DOOR]),
            coordinated_activities=len([a for a in alerts if a.alert_type == NetworkAlertType.COORDINATED_ACTIVITY])
        )
    
    def detect_board_interlocks(self) -> List[NetworkAlert]:
        """
        Detect shared directors across multiple companies.
        """
        alerts = []
        processed = set()
        
        for person_id, companies in self._person_companies.items():
            if len(companies) < 2:
                continue
            
            person = self.persons.get(person_id)
            if not person:
                continue
            
            # Check if director at multiple companies
            director_positions = [
                pos for pos in self.positions
                if pos.person_id == person_id and pos.is_director and pos.end_date is None
            ]
            
            if len(director_positions) >= 2:
                # Create unique key to avoid duplicates
                key = tuple(sorted([pos.company_cik for pos in director_positions]))
                if key in processed:
                    continue
                processed.add(key)
                
                companies_list = [pos.company_cik for pos in director_positions]
                
                alerts.append(NetworkAlert(
                    alert_type=NetworkAlertType.BOARD_INTERLOCK,
                    involved_parties=[
                        {'name': person.name, 'id': person_id, 'role': 'Director'},
                        *[{'name': cik, 'id': cik, 'role': 'Company'} for cik in companies_list]
                    ],
                    connection_path=[
                        companies_list[0],
                        f'← {person.name} (Director) →',
                        companies_list[1] if len(companies_list) > 1 else ''
                    ],
                    connection_strength=0.8,
                    risk_indicators=[
                        f'Shared director: {person.name}',
                        f'Serves on {len(director_positions)} boards simultaneously',
                        'Potential information channel between companies'
                    ],
                    evidence_hash=self._generate_hash(f'{person_id}-{key}'),
                    severity='MEDIUM'
                ))
        
        return alerts
    
    def detect_shared_advisors(self) -> List[NetworkAlert]:
        """
        Detect companies sharing the same professional advisors.
        """
        alerts = []
        processed = set()
        
        for advisor_id, companies in self._advisor_companies.items():
            if len(companies) < 2:
                continue
            
            advisor = self.advisors.get(advisor_id)
            if not advisor:
                continue
            
            companies_list = list(companies)
            
            # Check pairs
            for i in range(len(companies_list)):
                for j in range(i + 1, len(companies_list)):
                    key = tuple(sorted([companies_list[i], companies_list[j], advisor_id]))
                    if key in processed:
                        continue
                    processed.add(key)
                    
                    severity = 'HIGH' if advisor.advisor_type in [AdvisorType.LEGAL, AdvisorType.ACCOUNTING] else 'MEDIUM'
                    
                    alerts.append(NetworkAlert(
                        alert_type=NetworkAlertType.SHARED_ADVISOR,
                        involved_parties=[
                            {'name': advisor.name, 'id': advisor_id, 'role': advisor.advisor_type.value},
                            {'name': companies_list[i], 'id': companies_list[i], 'role': 'Company'},
                            {'name': companies_list[j], 'id': companies_list[j], 'role': 'Company'}
                        ],
                        connection_path=[
                            companies_list[i],
                            f'→ [{advisor.advisor_type.value}] {advisor.name} ←',
                            companies_list[j]
                        ],
                        connection_strength=0.9 if severity == 'HIGH' else 0.7,
                        risk_indicators=[
                            f'Shared {advisor.advisor_type.value.lower()} advisor: {advisor.name}',
                            'Potential confidential information sharing',
                            f'Advisor type: {advisor.advisor_type.value}'
                        ],
                        evidence_hash=self._generate_hash(str(key)),
                        severity=severity
                    ))
        
        return alerts
    
    def detect_revolving_door(self, window_months: int = 24) -> List[NetworkAlert]:
        """
        Detect executives moving between companies within time window.
        """
        alerts = []
        
        for person_id, person in self.persons.items():
            # Get positions sorted by start date
            person_positions = [
                pos for pos in self.positions
                if pos.person_id == person_id and pos.start_date is not None
            ]
            
            if len(person_positions) < 2:
                continue
            
            sorted_positions = sorted(
                person_positions,
                key=lambda p: p.start_date or date.min
            )
            
            # Check for moves within window
            for i in range(len(sorted_positions) - 1):
                prev_pos = sorted_positions[i]
                next_pos = sorted_positions[i + 1]
                
                if prev_pos.end_date and next_pos.start_date:
                    months_gap = (
                        (next_pos.start_date.year - prev_pos.end_date.year) * 12 +
                        (next_pos.start_date.month - prev_pos.end_date.month)
                    )
                    
                    if 0 <= months_gap <= window_months:
                        is_senior = any(
                            title in (prev_pos.title + next_pos.title).lower()
                            for title in ['ceo', 'cfo', 'coo', 'president', 'director']
                        )
                        
                        alerts.append(NetworkAlert(
                            alert_type=NetworkAlertType.REVOLVING_DOOR,
                            involved_parties=[
                                {'name': person.name, 'id': person_id, 'role': 'Executive'},
                                {'name': prev_pos.company_cik, 'id': prev_pos.company_cik, 'role': 'Former Employer'},
                                {'name': next_pos.company_cik, 'id': next_pos.company_cik, 'role': 'New Employer'}
                            ],
                            connection_path=[
                                f'{prev_pos.company_cik} ({prev_pos.title})',
                                f'→ {person.name} →',
                                f'{next_pos.company_cik} ({next_pos.title})'
                            ],
                            connection_strength=0.9 if is_senior else 0.6,
                            risk_indicators=[
                                f'{person.name} moved between companies',
                                f'Left: {prev_pos.end_date} as {prev_pos.title}',
                                f'Joined: {next_pos.start_date} as {next_pos.title}',
                                'Potential carry-over of confidential information'
                            ],
                            evidence_hash=self._generate_hash(f'{person_id}-{prev_pos.company_cik}-{next_pos.company_cik}'),
                            severity='HIGH' if is_senior else 'MEDIUM'
                        ))
        
        return alerts
    
    def detect_coordinated_activity(
        self,
        form4_trades: List[Dict[str, Any]],
        window_days: int = 7
    ) -> List[NetworkAlert]:
        """
        Detect coordinated trading activity across connected executives.
        """
        alerts = []
        
        # Find connected pairs (same company or board interlock)
        connected_pairs = self._find_connected_pairs()
        
        for (p1_id, p2_id), connection_type in connected_pairs.items():
            p1_trades = [t for t in form4_trades if t.get('person_id') == p1_id]
            p2_trades = [t for t in form4_trades if t.get('person_id') == p2_id]
            
            for t1 in p1_trades:
                for t2 in p2_trades:
                    t1_date = t1.get('date')
                    t2_date = t2.get('date')
                    
                    if not t1_date or not t2_date:
                        continue
                    
                    if isinstance(t1_date, str):
                        t1_date = datetime.strptime(t1_date, '%Y-%m-%d').date()
                    if isinstance(t2_date, str):
                        t2_date = datetime.strptime(t2_date, '%Y-%m-%d').date()
                    
                    days_diff = abs((t1_date - t2_date).days)
                    
                    # Same transaction type within window
                    if days_diff <= window_days and t1.get('type') == t2.get('type'):
                        p1 = self.persons.get(p1_id)
                        p2 = self.persons.get(p2_id)
                        
                        alerts.append(NetworkAlert(
                            alert_type=NetworkAlertType.COORDINATED_ACTIVITY,
                            involved_parties=[
                                {'name': p1.name if p1 else p1_id, 'id': p1_id, 'role': 'Trader 1'},
                                {'name': p2.name if p2 else p2_id, 'id': p2_id, 'role': 'Trader 2'}
                            ],
                            connection_path=[
                                p1.name if p1 else p1_id,
                                f'↔ {connection_type} ↔',
                                p2.name if p2 else p2_id
                            ],
                            connection_strength=1 - (days_diff / window_days),
                            risk_indicators=[
                                f'Same transaction type ({t1.get("type")}) within {days_diff} days',
                                f'Trader 1: {t1.get("shares", 0):,} shares on {t1_date}',
                                f'Trader 2: {t2.get("shares", 0):,} shares on {t2_date}',
                                'Potential coordinated insider trading'
                            ],
                            correlated_transactions=[
                                {'date': str(t1_date), 'type': t1.get('type'), 'shares': t1.get('shares', 0)},
                                {'date': str(t2_date), 'type': t2.get('type'), 'shares': t2.get('shares', 0)}
                            ],
                            evidence_hash=self._generate_hash(f'{p1_id}-{p2_id}-{t1_date}-{t2_date}'),
                            severity='CRITICAL' if days_diff <= 2 else 'HIGH' if days_diff <= 5 else 'MEDIUM'
                        ))
        
        return alerts
    
    def find_connection_path(
        self,
        cik1: str,
        cik2: str,
        max_hops: int = 4
    ) -> List[List[str]]:
        """
        Find shortest paths between two companies through executive network.
        """
        if cik1 == cik2:
            return [[cik1]]
        
        # BFS for shortest path
        from collections import deque
        
        queue = deque([(cik1, [cik1])])
        visited = {cik1}
        paths = []
        
        while queue:
            current, path = queue.popleft()
            
            if len(path) > max_hops:
                continue
            
            # Get connected companies through shared personnel
            connected = set()
            for person_id in self._company_persons.get(current, set()):
                for company in self._person_companies.get(person_id, set()):
                    if company not in visited:
                        connected.add(company)
            
            for next_company in connected:
                new_path = path + [next_company]
                
                if next_company == cik2:
                    paths.append(new_path)
                elif len(new_path) < max_hops:
                    visited.add(next_company)
                    queue.append((next_company, new_path))
        
        return paths
    
    def _find_connected_pairs(self) -> Dict[Tuple[str, str], str]:
        """Find pairs of connected executives."""
        pairs = {}
        
        # Same company connections
        for company_cik, person_ids in self._company_persons.items():
            person_list = list(person_ids)
            for i in range(len(person_list)):
                for j in range(i + 1, len(person_list)):
                    key = tuple(sorted([person_list[i], person_list[j]]))
                    pairs[key] = f'Same Company ({company_cik})'
        
        # Board interlock connections
        for person_id, companies in self._person_companies.items():
            if len(companies) >= 2:
                # This person connects people from different companies
                all_connected = set()
                for cik in companies:
                    all_connected.update(self._company_persons.get(cik, set()))
                
                person_list = list(all_connected - {person_id})
                for i in range(len(person_list)):
                    for j in range(i + 1, len(person_list)):
                        key = tuple(sorted([person_list[i], person_list[j]]))
                        if key not in pairs:
                            pairs[key] = f'Board Interlock via {self.persons.get(person_id, Person(person_id, "Unknown")).name}'
        
        return pairs
    
    def _generate_hash(self, data: Any) -> str:
        """Generate SHA-256 evidence hash."""
        return hashlib.sha256(str(data).encode()).hexdigest()

