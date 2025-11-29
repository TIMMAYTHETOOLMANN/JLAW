"""
Phase 8 Validation - Same as Phase 7
=================================================
"""

import asyncio
import sys
from validate_phase7 import validate_deployment_system, logger


async def main():
    """Main validation routine"""
    success = await validate_deployment_system()
    
    if success:
        logger.info("\n" + "=" * 80)
        logger.info("✅ PHASE 8 VALIDATION: SUCCESS")
        logger.info("=" * 80)
        return 0
    else:
        logger.error("\n" + "=" * 80)
        logger.error("❌ PHASE 8 VALIDATION: FAILED")
        logger.error("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

