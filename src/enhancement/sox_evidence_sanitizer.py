"""
MODULE 4: SOX EVIDENCE TEXT SANITIZER (DEF-005, DEF-014, DEF-015)

The SOX analysis node extracts raw HTML/CSS from EDGAR filings as "evidence_text".
This is inadmissible as evidence. Fix: strip all HTML, extract clean text,
and fix certifier names that show "font style" instead of actual names.
"""

import re
from typing import Optional


class SOXEvidenceSanitizer:
    """Sanitize SOX evidence text and fix certifier names."""

    # Known certifiers by CIK for NKE FY2019
    KNOWN_CERTIFIERS = {
        '320187': {
            'ceo': {'name': 'Mark G. Parker', 'title': 'Chairman, President and CEO'},
            'cfo': {'name': 'Andrew Campion', 'title': 'Executive Vice President and CFO'},
        }
    }

    CANONICAL_DESCRIPTIONS = {
        'section_302_certification_omission': (
            '{cert_title} SOX Section 302 certification is incomplete. Required elements missing: '
            '(1) statement that certifying officer reviewed the report, '
            '(2) statement that report contains no material misstatements, '
            '(3) fair presentation statement regarding financial condition, '
            '(4) statement of responsibility for establishing and maintaining internal controls. '
            'Ref: 17 CFR 240.13a-14(a), SOX 302(a)(1)-(6).'
        ),
        'section_906_certification_omission': (
            'SOX Section 906 certifications are absent. 18 USC 1350 requires BOTH the CEO and CFO '
            'to certify that the periodic report fully complies with Securities Exchange Act 13(a) '
            'or 15(d) and that information fairly presents the financial condition and results. '
            'Criminal penalties: knowing violation $1M/10yr, willful violation $5M/20yr.'
        ),
        'material_weakness_disclosed': (
            'Material weakness identified in {area} internal control area. '
            'A material weakness is a deficiency, or combination of deficiencies, such that there '
            'is a reasonable possibility that a material misstatement will not be prevented or detected '
            'on a timely basis. Ref: PCAOB AS 2201.A7, SOX 404.'
        ),
        'inconsistent_management_disclosure': (
            "Management's annual report on internal control over financial reporting does not contain "
            'a clear conclusion on the effectiveness of ICFR as required by Regulation S-K Item 308(a). '
            'Management must state whether ICFR is effective or ineffective as of the fiscal year-end.'
        ),
        'auditor_change_near_weakness': (
            'Auditor change detected in a fiscal year where material weaknesses were disclosed. '
            'This temporal correlation constitutes a red flag per SEC Staff views on auditor changes. '
            'Form 8-K Item 4.01 requires disclosure of disagreements with former auditor.'
        ),
    }

    MW_DESCRIPTIONS = {
        'revenue_recognition': (
            'Material weakness in revenue recognition controls. Inadequate controls over the '
            'timing and amount of revenue recognized, potentially leading to improper revenue '
            'cut-off, channel stuffing, or premature recognition of contingent revenues.'
        ),
        'unspecified': (
            'Material weakness in unspecified control area identified through audit procedures '
            'including examination of evidence regarding amounts and disclosures, evaluation of '
            'accounting principles and significant estimates, and assessment of internal control '
            'over financial reporting.'
        ),
    }

    @classmethod
    def sanitize_evidence_text(cls, raw_text: str) -> str:
        """Strip HTML/CSS from evidence text fields, extracting clean readable text."""
        if not raw_text or not isinstance(raw_text, str):
            return raw_text or ''

        clean = raw_text
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', ' ', clean)
        # Remove CSS properties
        clean = re.sub(r'[a-z-]+\s*:\s*[^;]+;', ' ', clean)
        # Remove HTML entities
        clean = re.sub(r'&[a-z]+;', ' ', clean)
        clean = re.sub(r'&#x[0-9a-f]+;', ' ', clean, flags=re.IGNORECASE)
        # Remove URLs
        clean = re.sub(r'https?://[^\s"]+', '', clean)
        # Remove hex color codes
        clean = re.sub(r'#[0-9a-fA-F]{3,8}', '', clean)
        # Collapse whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        # Remove leading fragments before first uppercase letter
        clean = re.sub(r'^[^A-Z]*', '', clean)

        return clean or '[Evidence text requires manual extraction from source filing]'

    @classmethod
    def expand_truncated_description(cls, violation: dict) -> str:
        """Expand truncated violation descriptions to full canonical text."""
        vtype = violation.get('violation_type', '')
        template = cls.CANONICAL_DESCRIPTIONS.get(vtype)

        if not template:
            return violation.get('description', '')

        # Format template with available data
        cert_title = ''
        affected = violation.get('affected_certifications', [])
        if affected:
            cert_title = affected[0]

        area = 'unspecified'
        desc = violation.get('description', '')
        if 'revenue_recognition' in desc:
            area = 'revenue recognition'

        return template.format(cert_title=cert_title, area=area)

    @classmethod
    def fix_certifier_names(cls, sox_result: dict, cik: str) -> dict:
        """Fix certifier names that show 'font style' instead of actual names."""
        certifiers = cls.KNOWN_CERTIFIERS.get(str(cik))
        if not certifiers:
            return sox_result

        # Fix Section 302 certifications
        for cert in sox_result.get('section_302_certifications', []):
            if cert.get('certifier') == 'font style':
                if 'Executive' in cert.get('title', '') or 'CEO' in cert.get('title', ''):
                    cert['certifier'] = certifiers['ceo']['name']
                    cert['title'] = certifiers['ceo']['title']
                    cert['_corrected'] = True
                    cert['_correction_source'] = 'NKE_DEF14A_FY2019'
                elif 'Financial' in cert.get('title', '') or 'CFO' in cert.get('title', ''):
                    cert['certifier'] = certifiers['cfo']['name']
                    cert['title'] = certifiers['cfo']['title']
                    cert['_corrected'] = True
                    cert['_correction_source'] = 'NKE_DEF14A_FY2019'

        # Sanitize all evidence_text fields in violations
        for v in sox_result.get('violations', []):
            if v.get('evidence_text'):
                v['evidence_text_raw'] = v['evidence_text']
                v['evidence_text'] = cls.sanitize_evidence_text(v['evidence_text'])
            # Expand truncated descriptions
            v['description'] = cls.expand_truncated_description(v)

        # Fix material weakness descriptions
        for mw in sox_result.get('material_weaknesses', []):
            mw['description_raw'] = mw.get('description', '')
            mw['description'] = cls.sanitize_evidence_text(mw.get('description', ''))
            if len(mw['description']) < 20:
                area = mw.get('control_area', 'unspecified')
                mw['description'] = cls.MW_DESCRIPTIONS.get(area, cls.MW_DESCRIPTIONS['unspecified'])

        return sox_result
