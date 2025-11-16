"""
GovInfo API Integration for USC/CFR Statute Retrieval
Handles on-demand caching, 503 retries, and comprehensive statute mapping
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import quote

from forensic_core_architecture import (
    ForensicAPIClient, BlockchainAuditTrail, ChainOfCustody,
    ViolationType, HardFailureException, logger
)

@dataclass 
class StatuteReference:
    """Legal statute reference with enforcement details"""
    title: int
    section: str
    subsection: Optional[str] = None
    usc_or_cfr: str = "USC"  # USC or CFR
    description: str = ""
    criminal_penalty: Optional[str] = None
    civil_penalty: Optional[str] = None
    enforcement_priority: int = 1  # 1=highest, 5=lowest
    
    @property
    def citation(self) -> str:
        """Format legal citation"""
        if self.subsection:
            return f"{self.title} {self.usc_or_cfr} § {self.section}({self.subsection})"
        return f"{self.title} {self.usc_or_cfr} § {self.section}"
    
    @property
    def govinfo_url(self) -> str:
        """Generate GovInfo direct access URL"""
        year = datetime.now().year
        
        if self.usc_or_cfr == "USC":
            # USC granule URL pattern
            granule_id = f"USCODE-{year-1}-title{self.title}-"
            
            # Parse section for proper granule ID
            if "j" in self.section:  # e.g., 78j for 15 USC 78j(b)
                granule_id += f"chap2B-sec{self.section}"
            else:
                granule_id += f"sec{self.section}"
            
            return f"https://www.govinfo.gov/content/pkg/USCODE-{year-1}-title{self.title}/pdf/{granule_id}.pdf"
        
        else:  # CFR
            # Determine volume based on part number
            part = int(self.section.split('.')[0]) if '.' in self.section else int(self.section)
            
            if self.title == 17:  # SEC regulations
                if part <= 40:
                    volume = 1
                elif part <= 199:
                    volume = 2
                elif part <= 239:
                    volume = 3
                else:
                    volume = 4
            else:
                volume = 1  # Default
            
            granule_id = f"CFR-{year}-title{self.title}-vol{volume}-sec{self.section}"
            return f"https://www.govinfo.gov/content/pkg/CFR-{year}-title{self.title}-vol{volume}/pdf/{granule_id}.pdf"

class StatuteMapper:
    """Maps violations to specific USC/CFR statutes"""
    
    # Comprehensive statute database
    STATUTES = {
        # 15 USC - Securities Laws
        ViolationType.USC_15_77g: StatuteReference(
            15, "77g", None, "USC",
            "Securities Act Registration Requirements",
            criminal_penalty="5 years",
            civil_penalty="Disgorgement + penalties",
            enforcement_priority=2
        ),
        ViolationType.USC_15_78j_b: StatuteReference(
            15, "78j", "b", "USC",
            "Anti-fraud provisions (Rule 10b-5 authority)",
            criminal_penalty="20 years",
            civil_penalty="Treble damages",
            enforcement_priority=1
        ),
        ViolationType.USC_15_78m: StatuteReference(
            15, "78m", None, "USC",
            "Periodic reporting requirements (10-K, 10-Q, 8-K)",
            criminal_penalty="10 years",
            civil_penalty="$100,000-$1,000,000",
            enforcement_priority=2
        ),
        
        # 17 CFR - SEC Regulations
        ViolationType.CFR_17_229_303: StatuteReference(
            17, "229.303", None, "CFR",
            "MD&A requirements (Regulation S-K Item 303)",
            criminal_penalty=None,
            civil_penalty="Cease-and-desist + penalties",
            enforcement_priority=3
        ),
        ViolationType.CFR_17_210: StatuteReference(
            17, "210", None, "CFR",
            "Regulation S-X financial statement requirements",
            criminal_penalty=None,
            civil_penalty="Restatement + penalties",
            enforcement_priority=2
        ),
        ViolationType.CFR_17_240_10b5: StatuteReference(
            17, "240.10b-5", None, "CFR",
            "Employment of manipulative and deceptive devices",
            criminal_penalty="25 years (via 18 USC 1348)",
            civil_penalty="Disgorgement + treble damages",
            enforcement_priority=1
        ),
        
        # 18 USC - Criminal Statutes
        ViolationType.USC_18_1001: StatuteReference(
            18, "1001", None, "USC",
            "False statements to federal agency",
            criminal_penalty="5 years",
            civil_penalty=None,
            enforcement_priority=2
        ),
        ViolationType.USC_18_1341: StatuteReference(
            18, "1341", None, "USC",
            "Mail fraud",
            criminal_penalty="20 years (30 if affecting financial institution)",
            civil_penalty="Restitution",
            enforcement_priority=1
        ),
        ViolationType.USC_18_1343: StatuteReference(
            18, "1343", None, "USC",
            "Wire fraud (includes electronic EDGAR filings)",
            criminal_penalty="20 years (30 if affecting financial institution)",
            civil_penalty="Restitution",
            enforcement_priority=1
        ),
        ViolationType.USC_18_1348: StatuteReference(
            18, "1348", None, "USC",
            "Securities fraud (Sarbanes-Oxley)",
            criminal_penalty="25 years",
            civil_penalty="Restitution + forfeiture",
            enforcement_priority=1
        ),
        ViolationType.USC_18_1350: StatuteReference(
            18, "1350", None, "USC",
            "CEO/CFO certification violations",
            criminal_penalty="10 years knowing, 20 years willful",
            civil_penalty="$1M-$5M fines",
            enforcement_priority=1
        ),
        ViolationType.USC_18_1519: StatuteReference(
            18, "1519", None, "USC",
            "Destruction of records in federal investigation",
            criminal_penalty="20 years",
            civil_penalty=None,
            enforcement_priority=1
        ),
        
        # 26 USC - Tax Code
        ViolationType.USC_26_6103: StatuteReference(
            26, "6103", None, "USC",
            "Tax return confidentiality",
            criminal_penalty="5 years",
            civil_penalty="$5,000 per disclosure",
            enforcement_priority=3
        ),
        
        # 31 USC - Money and Finance
        ViolationType.USC_31_5322: StatuteReference(
            31, "5322", None, "USC",
            "Bank Secrecy Act criminal penalties",
            criminal_penalty="10 years + $500,000",
            civil_penalty="Pattern penalties",
            enforcement_priority=2
        ),
        
        # 12 USC - Banking
        ViolationType.USC_12_1817: StatuteReference(
            12, "1817", None, "USC",
            "Bank reporting requirements",
            criminal_penalty="5 years",
            civil_penalty="Regulatory action",
            enforcement_priority=3
        )
    }
    
    @classmethod
    def get_statute(cls, violation_type: ViolationType) -> StatuteReference:
        """Retrieve statute reference for violation type"""
        return cls.STATUTES.get(violation_type)
    
    @classmethod
    def get_criminal_statutes(cls) -> List[StatuteReference]:
        """Get all criminal statute references"""
        return [s for s in cls.STATUTES.values() if s.criminal_penalty]
    
    @classmethod
    def get_priority_statutes(cls, priority: int = 1) -> List[StatuteReference]:
        """Get statutes by enforcement priority"""
        return [s for s in cls.STATUTES.values() if s.enforcement_priority == priority]

class GovInfoClient:
    """GovInfo API client with resilient retry logic"""
    
    BASE_URL = "https://api.govinfo.gov"
    CONTENT_URL = "https://www.govinfo.gov/content/pkg"
    
    def __init__(self, api_key: str, api_client: ForensicAPIClient, audit_trail: BlockchainAuditTrail):
        self.api_key = api_key
        self.client = api_client
        self.audit = audit_trail
        self.cache = {}  # Simple in-memory cache
    
    async def get_statute_text(self, statute: StatuteReference, format: str = "pdf") -> Tuple[bytes, ChainOfCustody]:
        """Retrieve statute text with on-demand generation handling"""
        cache_key = f"{statute.citation}:{format}"
        
        # Check cache first
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if (datetime.now() - cached["timestamp"]).days < 30:
                return cached["content"], cached["custody"]
        
        # Determine package and granule IDs
        package_id, granule_id = self._build_ids(statute)
        
        # Try granule-specific retrieval first
        if granule_id:
            url = f"{self.BASE_URL}/packages/{package_id}/granules/{granule_id}/summary"
        else:
            url = f"{self.BASE_URL}/packages/{package_id}/summary"
        
        url += f"?api_key={self.api_key}"
        
        # Fetch with retry logic for 503 on-demand generation
        content, custody = await self._fetch_with_generation_retry(url, format)
        
        # Cache the result
        self.cache[cache_key] = {
            "content": content,
            "custody": custody,
            "timestamp": datetime.now()
        }
        
        # Log to audit trail
        self.audit.add_entry("STATUTE_RETRIEVED", {
            "citation": statute.citation,
            "format": format,
            "size": len(content),
            "custody_id": custody.evidence_id
        })
        
        return content, custody
    
    def _build_ids(self, statute: StatuteReference) -> Tuple[str, Optional[str]]:
        """Build package and granule IDs for GovInfo"""
        year = datetime.now().year - 1  # Use previous year for stability
        
        if statute.usc_or_cfr == "USC":
            package_id = f"USCODE-{year}-title{statute.title}"
            
            # Build granule ID
            if statute.section == "78j":  # Special handling for complex sections
                granule_id = f"USCODE-{year}-title{statute.title}-chap2B-sec{statute.section}"
            else:
                granule_id = f"USCODE-{year}-title{statute.title}-sec{statute.section}"
            
            return package_id, granule_id
        
        else:  # CFR
            # Determine volume
            part = int(statute.section.split('.')[0]) if '.' in statute.section else 240
            
            if statute.title == 17:
                if part <= 40:
                    volume = 1
                elif part <= 199:
                    volume = 2
                elif part <= 239:
                    volume = 3
                else:
                    volume = 4
            else:
                volume = 1
            
            package_id = f"CFR-{year}-title{statute.title}-vol{volume}"
            granule_id = f"CFR-{year}-title{statute.title}-vol{volume}-sec{statute.section}"
            
            return package_id, granule_id
    
    async def _fetch_with_generation_retry(self, url: str, format: str) -> Tuple[bytes, ChainOfCustody]:
        """Fetch with special handling for 503 on-demand generation"""
        max_generation_attempts = 5
        generation_wait = 35  # seconds, slightly more than Retry-After
        
        for attempt in range(max_generation_attempts):
            try:
                response = await self.client.fetch_with_retry(url, "govinfo")
                data = json.loads(response["content"])
                
                # Get content link based on format
                if format == "pdf":
                    content_url = data.get("download", {}).get("pdfLink")
                elif format == "xml":
                    content_url = data.get("download", {}).get("xmlLink")
                else:
                    content_url = data.get("download", {}).get("txtLink")
                
                if not content_url:
                    raise Exception(f"No {format} link available")
                
                # Fetch actual content
                content_response = await self.client.fetch_with_retry(content_url, "govinfo")
                
                # Create chain of custody
                custody = ChainOfCustody(
                    case_id=f"STATUTE-{datetime.now().strftime('%Y%m%d')}",
                    collected_by={
                        "system": "GovInfoClient",
                        "timestamp": datetime.utcnow().isoformat(),
                        "method": "HTTPS",
                        "url": content_url
                    },
                    initial_hash=content_response["content_hash"]
                )
                
                return content_response["content"], custody
                
            except Exception as e:
                if "503" in str(e) or "Service unavailable" in str(e):
                    if attempt < max_generation_attempts - 1:
                        logger.info(f"GovInfo generating content, waiting {generation_wait}s...")
                        await asyncio.sleep(generation_wait)
                        continue
                raise
        
        raise Exception(f"Failed to retrieve statute after {max_generation_attempts} attempts")
    
    async def search_cfr_updates(self, title: int, part: int,
                                start_date: datetime, end_date: datetime) -> List[Dict]:
        """Search for CFR updates in date range"""
        collection = "CFR"
        
        # Format dates
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        
        url = f"{self.BASE_URL}/collections/{collection}/{start_str}"
        url += f"?offsetMark=*&pageSize=100&api_key={self.api_key}"
        
        results = []
        offset = "*"
        
        while True:
            response = await self.client.fetch_with_retry(
                url.replace("offsetMark=*", f"offsetMark={offset}"),
                "govinfo"
            )
            data = json.loads(response["content"])
            
            # Filter for specific title and part
            for package in data.get("packages", []):
                if f"title{title}" in package.get("packageId", ""):
                    # Check if part matches
                    if f"part{part}" in package.get("title", ""):
                        results.append({
                            "package_id": package["packageId"],
                            "title": package.get("title"),
                            "date_issued": package.get("dateIssued"),
                            "last_modified": package.get("lastModified")
                        })
            
            # Check for more results
            offset = data.get("nextPageOffsetMark")
            if not offset or len(results) >= 100:  # Limit results
                break
        
        return results

class StatuteAnalyzer:
    """Analyze filings for statute violations"""
    
    def __init__(self, govinfo_client: GovInfoClient):
        self.govinfo = govinfo_client
        self.violation_patterns = {
            ViolationType.USC_15_78m: [
                "late filing without NT",
                "missing required disclosure",
                "incomplete financial statements"
            ],
            ViolationType.CFR_17_229_303: [
                "boilerplate MD&A",
                "missing liquidity discussion",
                "no trend analysis"
            ],
            ViolationType.USC_18_1350: [
                "CEO/CFO certification with known issues",
                "certification despite material weakness",
                "false SOX certification"
            ]
        }
    
    async def analyze_for_violations(self, filing_content: str) -> List[Dict]:
        """Analyze filing content for statute violations"""
        violations_found = []
        
        # Check each violation pattern
        for violation_type, patterns in self.violation_patterns.items():
            for pattern in patterns:
                if self._check_pattern(filing_content, pattern):
                    statute = StatuteMapper.get_statute(violation_type)
                    
                    violations_found.append({
                        "violation_type": violation_type.value,
                        "statute": statute.citation,
                        "pattern": pattern,
                        "criminal_penalty": statute.criminal_penalty,
                        "civil_penalty": statute.civil_penalty,
                        "priority": statute.enforcement_priority
                    })
        
        # Sort by priority
        violations_found.sort(key=lambda x: x["priority"])
        
        return violations_found
    
    def _check_pattern(self, content: str, pattern: str) -> bool:
        """Check if pattern indicates violation"""
        # Simplified pattern matching - would use NLP in production
        
        if pattern == "late filing without NT":
            return "NT 10-" not in content and "late fil" in content.lower()
        
        elif pattern == "boilerplate MD&A":
            # Check for generic language
            boilerplate_phrases = [
                "may be adversely affected",
                "could have a material adverse effect",
                "we cannot assure",
                "factors beyond our control"
            ]
            count = sum(1 for phrase in boilerplate_phrases if phrase in content)
            return count >= 3
        
        elif pattern == "missing liquidity discussion":
            return "liquidity" not in content.lower() and "cash flow" in content.lower()
        
        elif pattern == "CEO/CFO certification with known issues":
            return "pursuant to Section 302" in content and "material weakness" in content
        
        return False
    
    async def map_violations_to_statutes(self, violations: List[Dict]) -> Dict:
        """Map violations to comprehensive statute analysis"""
        statute_summary = {
            "total_violations": len(violations),
            "criminal_exposure": [],
            "civil_exposure": [],
            "priority_actions": [],
            "statute_texts": {}
        }
        
        for violation in violations:
            violation_type = ViolationType[violation["violation_type"].replace(" ", "_").upper()]
            statute = StatuteMapper.get_statute(violation_type)
            
            if statute.criminal_penalty:
                statute_summary["criminal_exposure"].append({
                    "statute": statute.citation,
                    "penalty": statute.criminal_penalty,
                    "description": statute.description
                })
            
            if statute.civil_penalty:
                statute_summary["civil_exposure"].append({
                    "statute": statute.citation,
                    "penalty": statute.civil_penalty,
                    "description": statute.description
                })
            
            if statute.enforcement_priority == 1:
                statute_summary["priority_actions"].append({
                    "statute": statute.citation,
                    "action": f"Immediate review required for {statute.description}",
                    "url": statute.govinfo_url
                })
            
            # Retrieve statute text if high priority
            if statute.enforcement_priority <= 2:
                text, custody = await self.govinfo.get_statute_text(statute)
                statute_summary["statute_texts"][statute.citation] = {
                    "size": len(text),
                    "custody_id": custody.evidence_id,
                    "hash": custody.initial_hash
                }
        
        return statute_summary

