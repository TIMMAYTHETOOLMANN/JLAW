"""
Diagnostic script to find the NoneType comparison error
"""
import sys
import traceback

def diagnose_error():
    """Try to trigger and diagnose the error"""
    print("=" * 60)
    print("Diagnosing: '<' not supported between NoneType and str")
    print("=" * 60)
    print()
    
    # Test 1: Import forensic modules
    print("Test 1: Importing modules...")
    try:
        from unified_forensic_system import ForensicInvestigator, ForensicDatabase
        print("[OK] unified_forensic_system imported successfully")
    except Exception as e:
        print("[ERROR] Error importing unified_forensic_system:")
        traceback.print_exc()
        return
    
    # Test 2: Import web server
    print("\nTest 2: Importing web server...")
    try:
        from forensic_web_server import app
        print("[OK] forensic_web_server imported successfully")
    except Exception as e:
        print("[ERROR] Error importing forensic_web_server:")
        traceback.print_exc()
        return
    
    # Test 3: Create forensic investigator
    print("\nTest 3: Creating ForensicInvestigator...")
    try:
        investigator = ForensicInvestigator()
        print("[OK] ForensicInvestigator created successfully")
    except Exception as e:
        print("[ERROR] Error creating ForensicInvestigator:")
        traceback.print_exc()
        return
    
    # Test 4: Test database
    print("\nTest 4: Testing database...")
    try:
        db = ForensicDatabase()
        print("[OK] ForensicDatabase created successfully")
    except Exception as e:
        print("[ERROR] Error creating ForensicDatabase:")
        traceback.print_exc()
        return
    
    # Test 5: Make a test request to the app
    print("\nTest 5: Making test request to Flask app...")
    try:
        with app.test_client() as client:
            response = client.get('/')
            print(f"[OK] Root endpoint: Status {response.status_code}")
            
            response = client.get('/api/health')
            print(f"[OK] Health endpoint: Status {response.status_code}")
    except Exception as e:
        print("[ERROR] Error making test request:")
        traceback.print_exc()
        return
    
    print("\n" + "=" * 60)
    print("All tests passed! No NoneType comparison error found.")
    print("=" * 60)
    print()
    print("The error may occur during:")
    print("- Actual SEC data retrieval")
    print("- User input processing")
    print("- Forensic analysis computation")
    print()
    print("Recommendation: Check the server logs when making actual requests")

if __name__ == '__main__':
    diagnose_error()

