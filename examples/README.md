# JLAW Examples

This directory contains example scripts demonstrating various JLAW features.

## SEC EDGAR Bulletproof Client

**File**: `sec_edgar_bulletproof_example.py`

Demonstrates the production-grade SEC EDGAR client with:
- Advanced caching with TTL
- Adaptive rate limiting
- Circuit breaker protection
- Specialized methods for JLAW nodes

**Run in mock mode** (no real API calls):
```bash
SEC_MOCK_MODE=true python examples/sec_edgar_bulletproof_example.py
```

**Run with real API** (requires SEC_USER_AGENT in .env):
```bash
python examples/sec_edgar_bulletproof_example.py
```

For comprehensive documentation, see: [SEC_EDGAR_BULLETPROOF_GUIDE.md](../SEC_EDGAR_BULLETPROOF_GUIDE.md)
