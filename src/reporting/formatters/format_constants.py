"""
Format Constants - Phase 4 Enhanced Reporting
=============================================

Reusable formatting elements for DOJ-grade forensic output.

This module provides:
- Typography hierarchy (dividers, breaks)
- Severity indicators (visual bars)
- Status markers (Unicode symbols)
- Box drawing characters
- Standard widths and spacing
"""

# ═══════════════════════════════════════════════════════════════════════════
# TYPOGRAPHY HIERARCHY
# ═══════════════════════════════════════════════════════════════════════════

# Standard width for all formatted output
STANDARD_WIDTH = 80

# Document structure dividers
DOUBLE_LINE = "═" * STANDARD_WIDTH  # Document title level
MAJOR_DIVIDER = "━" * STANDARD_WIDTH  # Major section divider
SUBSECTION_DIVIDER = "─" * STANDARD_WIDTH  # Subsection divider
MINOR_BREAK = "· " * 40  # Minor break (80 chars with spaces)

# ═══════════════════════════════════════════════════════════════════════════
# SEVERITY INDICATORS
# ═══════════════════════════════════════════════════════════════════════════

# Visual severity bars (10 characters each)
SEVERITY_CRITICAL = "▓▓▓▓▓▓▓▓▓▓"    # 100% filled
SEVERITY_HIGH = "▓▓▓▓▓▓▓▓░░"        # 80% filled
SEVERITY_MEDIUM = "▓▓▓▓▓▓░░░░"      # 60% filled
SEVERITY_LOW = "▓▓▓▓░░░░░░"         # 40% filled
SEVERITY_MINIMAL = "▓▓░░░░░░░░"     # 20% filled

# Risk score indicators (3 characters each)
RISK_CRITICAL = "▓▓▓"
RISK_HIGH = "▓▓░"
RISK_MEDIUM = "▓░░"
RISK_LOW = "░░░"

# ═══════════════════════════════════════════════════════════════════════════
# STATUS MARKERS
# ═══════════════════════════════════════════════════════════════════════════

STATUS_COMPLETE = "✓"           # Task complete / requirement met
STATUS_INCOMPLETE = "○"         # Task incomplete / pending
STATUS_FAILED = "✗"             # Task failed / requirement not met
STATUS_KEY_FINDING = "◆"        # Key finding indicator
STATUS_ACTION_REQUIRED = "►"    # Action required indicator
STATUS_WARNING = "⚠"            # Warning indicator
STATUS_AVAILABLE = "✓"          # Resource available
STATUS_UNAVAILABLE = "✗"        # Resource unavailable

# ═══════════════════════════════════════════════════════════════════════════
# BOX DRAWING CHARACTERS
# ═══════════════════════════════════════════════════════════════════════════

# Single line box drawing
BOX_SINGLE_HORIZONTAL = "─"
BOX_SINGLE_VERTICAL = "│"
BOX_SINGLE_TOP_LEFT = "┌"
BOX_SINGLE_TOP_RIGHT = "┐"
BOX_SINGLE_BOTTOM_LEFT = "└"
BOX_SINGLE_BOTTOM_RIGHT = "┘"
BOX_SINGLE_VERTICAL_RIGHT = "├"
BOX_SINGLE_VERTICAL_LEFT = "┤"
BOX_SINGLE_HORIZONTAL_DOWN = "┬"
BOX_SINGLE_HORIZONTAL_UP = "┴"
BOX_SINGLE_CROSS = "┼"

# Double line box drawing
BOX_DOUBLE_HORIZONTAL = "═"
BOX_DOUBLE_VERTICAL = "║"
BOX_DOUBLE_TOP_LEFT = "╔"
BOX_DOUBLE_TOP_RIGHT = "╗"
BOX_DOUBLE_BOTTOM_LEFT = "╚"
BOX_DOUBLE_BOTTOM_RIGHT = "╝"
BOX_DOUBLE_VERTICAL_RIGHT = "╠"
BOX_DOUBLE_VERTICAL_LEFT = "╣"
BOX_DOUBLE_HORIZONTAL_DOWN = "╦"
BOX_DOUBLE_HORIZONTAL_UP = "╩"
BOX_DOUBLE_CROSS = "╬"

# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def create_progress_bar(value: int, total: int, width: int = 20) -> str:
    """
    Generate Unicode progress bar.
    
    Args:
        value: Current value
        total: Maximum value
        width: Width of progress bar in characters
        
    Returns:
        Unicode progress bar string
    """
    if total == 0:
        return '░' * width
    
    filled = min(int((value / total) * width), width)
    return '▓' * filled + '░' * (width - filled)


def get_severity_indicator(severity: str) -> str:
    """
    Get severity indicator bar for a severity level.
    
    Args:
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW, MINIMAL)
        
    Returns:
        Unicode severity bar
    """
    severity_map = {
        'CRITICAL': SEVERITY_CRITICAL,
        'HIGH': SEVERITY_HIGH,
        'MEDIUM': SEVERITY_MEDIUM,
        'LOW': SEVERITY_LOW,
        'MINIMAL': SEVERITY_MINIMAL,
    }
    return severity_map.get(severity.upper(), SEVERITY_MINIMAL)


def get_risk_indicator(risk_score: float) -> str:
    """
    Get risk indicator based on risk score.
    
    Args:
        risk_score: Risk score (0-100)
        
    Returns:
        Unicode risk indicator
    """
    if risk_score >= 80:
        return RISK_CRITICAL
    elif risk_score >= 60:
        return RISK_HIGH
    elif risk_score >= 40:
        return RISK_MEDIUM
    else:
        return RISK_LOW


def create_box_line(
    content: str,
    width: int = STANDARD_WIDTH - 4,
    align: str = 'left',
    padding: int = 1
) -> str:
    """
    Create a boxed line with content.
    
    Args:
        content: Content to display
        width: Width of content area (excluding box chars)
        align: Alignment ('left', 'center', 'right')
        padding: Padding characters on each side
        
    Returns:
        Formatted box line
    """
    available_width = width - (padding * 2)
    
    if align == 'center':
        formatted = content.center(available_width)
    elif align == 'right':
        formatted = content.rjust(available_width)
    else:
        formatted = content.ljust(available_width)
    
    padded = (' ' * padding) + formatted + (' ' * padding)
    return f"{BOX_SINGLE_VERTICAL} {padded} {BOX_SINGLE_VERTICAL}"


def create_box_header(title: str, width: int = STANDARD_WIDTH - 4) -> list:
    """
    Create a box header with title.
    
    Args:
        title: Title text
        width: Width of box
        
    Returns:
        List of lines for box header
    """
    return [
        BOX_SINGLE_TOP_LEFT + (BOX_SINGLE_HORIZONTAL * width) + BOX_SINGLE_TOP_RIGHT,
        create_box_line(title, width, align='left'),
        BOX_SINGLE_VERTICAL_RIGHT + (BOX_SINGLE_HORIZONTAL * width) + BOX_SINGLE_VERTICAL_LEFT,
    ]


def create_box_footer(width: int = STANDARD_WIDTH - 4) -> str:
    """
    Create a box footer.
    
    Args:
        width: Width of box
        
    Returns:
        Box footer line
    """
    return BOX_SINGLE_BOTTOM_LEFT + (BOX_SINGLE_HORIZONTAL * width) + BOX_SINGLE_BOTTOM_RIGHT


def create_double_box_header(title: str, width: int = STANDARD_WIDTH - 4) -> list:
    """
    Create a double-line box header with title.
    
    Args:
        title: Title text
        width: Width of box
        
    Returns:
        List of lines for double box header
    """
    horizontal = BOX_DOUBLE_HORIZONTAL * (width + 2)
    vertical = BOX_DOUBLE_VERTICAL
    
    return [
        BOX_DOUBLE_TOP_LEFT + horizontal + BOX_DOUBLE_TOP_RIGHT,
        f"{vertical}{'': ^{width + 2}}{vertical}",
        f"{vertical} {title.center(width)} {vertical}",
        f"{vertical}{'': ^{width + 2}}{vertical}",
    ]


def create_double_box_footer(width: int = STANDARD_WIDTH - 4) -> str:
    """
    Create a double-line box footer.
    
    Args:
        width: Width of box
        
    Returns:
    Double box footer line
    """
    horizontal = BOX_DOUBLE_HORIZONTAL * (width + 2)
    return BOX_DOUBLE_BOTTOM_LEFT + horizontal + BOX_DOUBLE_BOTTOM_RIGHT


# ═══════════════════════════════════════════════════════════════════════════
# CLASSIFICATION LABELS
# ═══════════════════════════════════════════════════════════════════════════

CLASSIFICATION_CONFIDENTIAL = "CONFIDENTIAL — LAW ENFORCEMENT SENSITIVE"
CLASSIFICATION_DOJ_GRADE = "DOJ-GRADE"
CLASSIFICATION_SEC_REFERRAL = "SEC REFERRAL READY"
CLASSIFICATION_INTERNAL = "INTERNAL USE"

# ═══════════════════════════════════════════════════════════════════════════
# SECTION HEADERS
# ═══════════════════════════════════════════════════════════════════════════

SECTION_1_TITLE = "SECTION 1: EXECUTIVE INTELLIGENCE BRIEFING"
SECTION_2_TITLE = "SECTION 2: VIOLATION ANALYSIS BY CATEGORY"
SECTION_3_TITLE = "SECTION 3: REPORTING PERSON DOSSIERS"
SECTION_4_TITLE = "SECTION 4: EVIDENCE CHAIN & CRYPTOGRAPHIC ATTESTATION"
APPENDIX_A_TITLE = "APPENDIX A: COMPLETE VIOLATION EVIDENCE RECORDS"
APPENDIX_B_TITLE = "APPENDIX B: 15-NODE RECURSIVE ENGINE ANALYSIS MATRIX"
APPENDIX_C_TITLE = "APPENDIX C: RAW SEC FILING INDEX"
APPENDIX_D_TITLE = "APPENDIX D: ALGORITHM EXECUTION LOG"
