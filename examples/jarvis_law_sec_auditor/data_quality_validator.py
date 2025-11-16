"""
JARVIS:LAW - STRICT VALIDATION SYSTEM
Zero tolerance for N/A, True/False, or missing data
"""

class DataQualityError(Exception):
    """Raised when extracted data fails quality standards"""
    pass

def validate_transaction(transaction: dict) -> bool:
    """
    Validate transaction has ALL required fields with REAL data.
    Returns True only if ALL fields are present and valid.
    Raises DataQualityError if any field is missing or invalid.
    """
    required_fields = {
        'transaction_date': 'Transaction Date',
        'security_title': 'Security Title',
        'transaction_code': 'Transaction Code',
        'shares': 'Share Count',
        'price_per_share': 'Price Per Share',
        'acquired_disposed': 'Acquired/Disposed Flag',
        'shares_owned_after': 'Shares Owned After Transaction'
    }
    
    missing = []
    invalid = []
    
    for field, display_name in required_fields.items():
        if field not in transaction:
            missing.append(display_name)
        else:
            value = transaction[field]
            
            # Check for unacceptable values
            if value in [None, 'N/A', 'Unknown', '', 'null']:
                invalid.append(f"{display_name}: '{value}'")
            
            # Check for boolean contamination
            if isinstance(value, bool) or value in ['True', 'False', 'true', 'false']:
                invalid.append(f"{display_name}: Boolean value '{value}' is unacceptable")
            
            # Specific validations
            if field == 'transaction_date':
                # Must be valid date format YYYY-MM-DD
                import re
                if not re.match(r'\d{4}-\d{2}-\d{2}', str(value)):
                    invalid.append(f"{display_name}: Invalid date format '{value}'")
            
            elif field == 'transaction_code':
                # Must be valid SEC code
                valid_codes = ['P', 'S', 'A', 'D', 'F', 'I', 'M', 'X', 'G', 'J']
                if value not in valid_codes:
                    invalid.append(f"{display_name}: Invalid code '{value}'")
            
            elif field in ['shares', 'shares_owned_after']:
                # Must be numeric
                try:
                    float(str(value).replace(',', ''))
                except:
                    invalid.append(f"{display_name}: Non-numeric value '{value}'")
            
            elif field == 'acquired_disposed':
                # Must be A or D
                if value not in ['A', 'D']:
                    invalid.append(f"{display_name}: Must be 'A' or 'D', got '{value}'")
    
    if missing or invalid:
        errors = []
        if missing:
            errors.append(f"MISSING FIELDS: {', '.join(missing)}")
        if invalid:
            errors.append(f"INVALID DATA: {', '.join(invalid)}")
        
        raise DataQualityError('\n'.join(errors))
    
    return True

def validate_reporting_owner(owner: dict) -> bool:
    """Validate reporting owner has clean, extracted data"""
    if not owner:
        raise DataQualityError("Reporting owner data is completely missing")
    
    # Name must NOT contain HTML tags
    name = owner.get('name', '')
    if '<' in name or '>' in name or 'sup' in name or 'table' in name:
        raise DataQualityError(f"Reporting owner name contains HTML garbage: {name[:100]}")
    
    # Relationship must be specific, not boolean
    relationship = owner.get('relationship', {})
    if isinstance(relationship, dict):
        for key, value in relationship.items():
            if isinstance(value, bool):
                raise DataQualityError(f"Relationship field '{key}' is boolean ({value}). Need specific roles/titles.")
    
    # Must have actual CIK if available
    if owner.get('cik') in [None, 'N/A', 'Unknown', '']:
        # CIK might be legitimately unavailable, but flag it
        pass
    
    return True

def validate_complete_filing(profile: dict) -> tuple[bool, list]:
    """
    Validate entire filing extraction.
    Returns (is_valid, error_list)
    """
    errors = []
    
    try:
        validate_reporting_owner(profile.get('reporting_owner'))
    except DataQualityError as e:
        errors.append(f"REPORTING OWNER ERROR: {e}")
    
    # Validate each transaction
    transactions = profile.get('transactions', [])
    if not transactions:
        errors.append("NO TRANSACTIONS DETECTED - File may not have been properly parsed")
    
    valid_transaction_count = 0
    for i, trans in enumerate(transactions, 1):
        try:
            validate_transaction(trans)
            valid_transaction_count += 1
        except DataQualityError as e:
            errors.append(f"TRANSACTION #{i} INVALID:\n{e}")
    
    # If no valid transactions, this is a hard fail
    if valid_transaction_count == 0 and len(transactions) > 0:
        errors.append(f"CRITICAL: 0/{len(transactions)} transactions have valid data")
    
    return (len(errors) == 0, errors)

def generate_error_report(filing_data: dict, errors: list) -> str:
    """Generate error report when extraction fails quality standards"""
    report = []
    report.append("="*100)
    report.append("JARVIS:LAW EXTRACTION FAILURE REPORT")
    report.append("="*100)
    report.append("\n** DATA QUALITY STANDARDS NOT MET **")
    report.append("\nThis filing failed forensic-grade extraction validation.")
    report.append("Reports are only generated when ALL required fields contain REAL data.")
    report.append("\nFiling Information:")
    report.append(f"  Accession: {filing_data.get('accession_number', 'Unknown')}")
    report.append(f"  Date: {filing_data.get('filing_date', 'Unknown')}")
    report.append(f"  Form: {filing_data.get('form_type', 'Unknown')}")
    
    report.append(f"\n{'='*100}")
    report.append(f"VALIDATION ERRORS ({len(errors)} total)")
    report.append(f"{'='*100}")
    
    for i, error in enumerate(errors, 1):
        report.append(f"\nError #{i}:")
        report.append(f"  {error}")
    
    report.append(f"\n{'='*100}")
    report.append("REQUIRED ACTIONS:")
    report.append("="*100)
    report.append("\n1. Verify source document is XML (not HTML render)")
    report.append("2. Enhance parser to extract from proper XML elements")
    report.append("3. Implement field-specific extraction logic")
    report.append("4. Re-run extraction after parser enhancement")
    
    report.append("\n\nNO REPORT GENERATED - EXTRACTION QUALITY INSUFFICIENT")
    report.append("="*100 + "\n")
    
    return '\n'.join(report)

# Export
__all__ = [
    'validate_transaction',
    'validate_reporting_owner',
    'validate_complete_filing',
    'generate_error_report',
    'DataQualityError'
]

