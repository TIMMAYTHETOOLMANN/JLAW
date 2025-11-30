"""
Input Validation Module for JLAW Forensics
==========================================

Validates all inputs to the forensic analysis system:
- CIK number format
- Date ranges
- Filing types
- Company names

Ensures consistent, validated inputs across all analysis runs.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    normalized_value: Optional[str] = None


class InputValidator:
    """
    Validates and normalizes all forensic analysis inputs.
    
    Ensures:
    - CIK numbers are properly formatted (10 digits, zero-padded)
    - Date ranges are valid and logical
    - Filing types are supported SEC forms
    - Company names are sanitized
    """
    
    # Supported SEC filing types
    SUPPORTED_FILING_TYPES = {
        # Annual/Quarterly Reports
        '10-K', '10-K/A', '10-K405', '10-KSB', '10-KT',
        '10-Q', '10-Q/A', '10-QSB', '10-QT',
        
        # Current Reports
        '8-K', '8-K/A', '8-K12B', '8-K12G3',
        
        # Insider Trading (Section 16)
        '3', '4', '5',
        '3/A', '4/A', '5/A',
        
        # Beneficial Ownership
        'SC 13D', 'SC 13D/A',
        'SC 13G', 'SC 13G/A',
        '13F-HR', '13F-HR/A',
        
        # Proxy Statements
        'DEF 14A', 'DEFA14A', 'DEFM14A',
        'PRE 14A', 'PREM14A',
        
        # Registration Statements
        'S-1', 'S-1/A', 'S-3', 'S-3/A', 'S-4', 'S-8',
        
        # Prospectus
        '424A', '424B1', '424B2', '424B3', '424B4', '424B5',
        
        # Annual Reports
        '20-F', '40-F', '6-K',
        
        # NT (Notification of Late Filing)
        'NT 10-K', 'NT 10-Q',
        
        # Other Common Forms
        'ARS', 'SD', '144', '11-K',
    }
    
    # CIK pattern: 1-10 digits
    CIK_PATTERN = re.compile(r'^\d{1,10}$')
    
    # Date pattern: YYYY-MM-DD
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    @classmethod
    def validate_cik(cls, cik: str) -> ValidationResult:
        """
        Validate and normalize CIK number.
        
        Args:
            cik: CIK number (can be with or without leading zeros)
            
        Returns:
            ValidationResult with normalized 10-digit zero-padded CIK
        """
        errors = []
        warnings = []
        
        # Remove any non-digit characters
        cleaned_cik = re.sub(r'\D', '', str(cik))
        
        if not cleaned_cik:
            errors.append("CIK cannot be empty")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        if len(cleaned_cik) > 10:
            errors.append(f"CIK too long: {len(cleaned_cik)} digits (max 10)")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Normalize to 10 digits with leading zeros
        normalized_cik = cleaned_cik.zfill(10)
        
        if cleaned_cik != str(cik).strip():
            warnings.append(f"CIK was normalized from '{cik}' to '{normalized_cik}'")
        
        return ValidationResult(
            is_valid=True,
            errors=errors,
            warnings=warnings,
            normalized_value=normalized_cik
        )
    
    @classmethod
    def validate_date(cls, date_str: str) -> ValidationResult:
        """
        Validate date string.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            
        Returns:
            ValidationResult with normalized date
        """
        errors = []
        warnings = []
        
        if not cls.DATE_PATTERN.match(date_str):
            errors.append(f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        try:
            parsed_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Check if date is in reasonable range
            if parsed_date.year < 1993:
                warnings.append(f"Date {date_str} is before SEC EDGAR (1993)")
            
            if parsed_date > datetime.now():
                warnings.append(f"Date {date_str} is in the future")
            
            return ValidationResult(
                is_valid=True,
                errors=errors,
                warnings=warnings,
                normalized_value=date_str
            )
            
        except ValueError as e:
            errors.append(f"Invalid date: {e}")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
    
    @classmethod
    def validate_date_range(
        cls, 
        start_date: str, 
        end_date: str
    ) -> ValidationResult:
        """
        Validate date range.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        # Validate individual dates
        start_result = cls.validate_date(start_date)
        end_result = cls.validate_date(end_date)
        
        if not start_result.is_valid:
            errors.extend([f"Start date: {e}" for e in start_result.errors])
        if not end_result.is_valid:
            errors.extend([f"End date: {e}" for e in end_result.errors])
        
        if errors:
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Check range logic
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        if start_dt > end_dt:
            errors.append(f"Start date ({start_date}) is after end date ({end_date})")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Check range duration
        days = (end_dt - start_dt).days
        if days > 3650:  # ~10 years
            warnings.append(f"Date range spans {days} days (~{days/365:.1f} years). Large analysis.")
        
        warnings.extend(start_result.warnings)
        warnings.extend(end_result.warnings)
        
        return ValidationResult(
            is_valid=True,
            errors=errors,
            warnings=warnings,
            normalized_value=f"{start_date} to {end_date}"
        )
    
    @classmethod
    def validate_filing_types(cls, filing_types: List[str]) -> ValidationResult:
        """
        Validate list of filing types.
        
        Args:
            filing_types: List of SEC filing types
            
        Returns:
            ValidationResult with normalized filing types
        """
        errors = []
        warnings = []
        normalized = []
        
        if not filing_types:
            errors.append("At least one filing type required")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        for filing_type in filing_types:
            # Normalize: uppercase and strip whitespace
            normalized_type = filing_type.upper().strip()
            
            if normalized_type in cls.SUPPORTED_FILING_TYPES:
                normalized.append(normalized_type)
            else:
                # Try exact match with common variations (whitespace normalization)
                cleaned = normalized_type.replace('  ', ' ').strip()
                
                # Try matching with variations
                match_found = None
                
                # Direct variations to try
                variations = [
                    cleaned,
                    cleaned.replace(' ', '-'),  # "10 K" -> "10-K"
                    cleaned.replace('-', ' '),  # Already normalized
                ]
                
                for variation in variations:
                    if variation in cls.SUPPORTED_FILING_TYPES:
                        match_found = variation
                        break
                
                if match_found:
                    normalized.append(match_found)
                    if match_found != normalized_type:
                        warnings.append(
                            f"Filing type '{filing_type}' normalized to '{match_found}'"
                        )
                else:
                    errors.append(f"Unsupported filing type: '{filing_type}'")
        
        if errors:
            # Include list of valid types in error message
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        return ValidationResult(
            is_valid=True,
            errors=errors,
            warnings=warnings,
            normalized_value=','.join(normalized)
        )
    
    @classmethod
    def validate_company_name(cls, company_name: str) -> ValidationResult:
        """
        Validate and sanitize company name.
        
        Args:
            company_name: Company name
            
        Returns:
            ValidationResult with sanitized company name
        """
        errors = []
        warnings = []
        
        if not company_name or not company_name.strip():
            errors.append("Company name cannot be empty")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        # Sanitize: remove dangerous characters
        sanitized = company_name.strip()
        sanitized = re.sub(r'[<>"\'\\/;]', '', sanitized)
        
        if sanitized != company_name:
            warnings.append(f"Company name sanitized from '{company_name}' to '{sanitized}'")
        
        if len(sanitized) > 200:
            errors.append(f"Company name too long: {len(sanitized)} chars (max 200)")
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        return ValidationResult(
            is_valid=True,
            errors=errors,
            warnings=warnings,
            normalized_value=sanitized
        )
    
    @classmethod
    def validate_analysis_config(
        cls,
        company_name: str,
        cik: str,
        start_date: str,
        end_date: str,
        filing_types: List[str]
    ) -> Tuple[bool, List[str], List[str], dict]:
        """
        Validate complete analysis configuration.
        
        Args:
            company_name: Target company name
            cik: CIK number
            start_date: Analysis start date
            end_date: Analysis end date
            filing_types: List of filing types to analyze
            
        Returns:
            Tuple of (is_valid, errors, warnings, normalized_config)
        """
        all_errors = []
        all_warnings = []
        normalized_config = {}
        
        # Validate company name
        company_result = cls.validate_company_name(company_name)
        if not company_result.is_valid:
            all_errors.extend(company_result.errors)
        else:
            normalized_config['company_name'] = company_result.normalized_value
        all_warnings.extend(company_result.warnings)
        
        # Validate CIK
        cik_result = cls.validate_cik(cik)
        if not cik_result.is_valid:
            all_errors.extend(cik_result.errors)
        else:
            normalized_config['cik'] = cik_result.normalized_value
        all_warnings.extend(cik_result.warnings)
        
        # Validate date range
        date_result = cls.validate_date_range(start_date, end_date)
        if not date_result.is_valid:
            all_errors.extend(date_result.errors)
        else:
            normalized_config['start_date'] = start_date
            normalized_config['end_date'] = end_date
        all_warnings.extend(date_result.warnings)
        
        # Validate filing types
        filing_result = cls.validate_filing_types(filing_types)
        if not filing_result.is_valid:
            all_errors.extend(filing_result.errors)
        else:
            normalized_config['filing_types'] = filing_result.normalized_value.split(',')
        all_warnings.extend(filing_result.warnings)
        
        is_valid = len(all_errors) == 0
        
        return is_valid, all_errors, all_warnings, normalized_config
