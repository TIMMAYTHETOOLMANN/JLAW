. """
Quick test to verify the FraudIndicator serialization fix
"""
import json
from datetime import datetime
from unified_forensic_system import FraudIndicator, ViolationType, Priority

# Test creating a FraudIndicator
print("Testing FraudIndicator JSON serialization...")
print("=" * 60)

indicator = FraudIndicator(
    indicator_type="TEST_FRAUD",
    severity=0.8,
    confidence=0.9,
    evidence=["Test evidence 1", "Test evidence 2"],
    ml_features={"score": 0.75, "confidence": 0.85},
    statute_violations=[ViolationType.USC_15_78j_b, ViolationType.USC_18_1348],
    similar_cases=["Case A", "Case B"],
    detection_method="ML_ANALYSIS",
    timestamp=datetime.utcnow()
)

print("\n1. Created FraudIndicator:")
print(f"   Type: {indicator.indicator_type}")
print(f"   Risk Score: {indicator.risk_score:.2f}")
print(f"   Max Penalty: {indicator.max_penalty}")

# Test to_dict() method
print("\n2. Converting to dictionary...")
try:
    indicator_dict = indicator.to_dict()
    print("   ✅ to_dict() successful")
    print(f"   Keys: {list(indicator_dict.keys())}")
except Exception as e:
    print(f"   ❌ to_dict() failed: {e}")
    exit(1)

# Test JSON serialization
print("\n3. Testing JSON serialization...")
try:
    json_str = json.dumps(indicator_dict, indent=2)
    print("   ✅ JSON serialization successful")
    print(f"   JSON length: {len(json_str)} characters")
except Exception as e:
    print(f"   ❌ JSON serialization failed: {e}")
    exit(1)

# Test JSON with list of indicators
print("\n4. Testing list serialization (as used in database)...")
try:
    indicators = [indicator, indicator]
    json_list = json.dumps([ind.to_dict() for ind in indicators])
    print(f"   ✅ List serialization successful")
    print(f"   Serialized {len(indicators)} indicators")
except Exception as e:
    print(f"   ❌ List serialization failed: {e}")
    exit(1)

# Test from_dict() reconstruction
print("\n5. Testing from_dict() reconstruction...")
try:
    reconstructed = FraudIndicator.from_dict(indicator_dict)
    print("   ✅ from_dict() successful")
    print(f"   Type: {reconstructed.indicator_type}")
    print(f"   Violations: {[v.name for v in reconstructed.statute_violations]}")
except Exception as e:
    print(f"   ❌ from_dict() failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("\nThe FraudIndicator serialization fix is working correctly.")
print("The 'Object of type FraudIndicator is not JSON serializable' error is RESOLVED.")

