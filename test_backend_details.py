
import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/chat"

def test_report(message, description):
    print(f"Testing: {description}")
    print(f"Input: '{message}'")
    try:
        response = requests.post(BASE_URL, json={"message": message})
        data = response.json()
        
        print(f"Response: {data.get('response')}")
        print(f"Saved: {data.get('report_saved')}")
        print(f"Missing: {data.get('missing_info')}")
        print("-" * 20)
        return data
    except Exception as e:
        print(f"Error: {e}")
        return None

# Test 1: Missing Details
print("\n--- Test 1: Missing Age/Gender ---")
data1 = test_report("I took Aspirin and felt dizzy", "Report without age/gender")
if data1 and data1.get('missing_info') == ['age', 'gender']:
    print("[PASS] Correctly asked for missing info")
else:
    print("[FAIL] Did not ask for missing info correctly")

# Test 2: Partial Details (Age only)
print("\n--- Test 2: Partial Details (Age only) ---")
data2 = test_report("I took Tylenol and felt nausea (25 years old)", "Report with age only")
if data2 and data2.get('missing_info') == ['gender']:
    print("[PASS] Correctly asked for gender only")
else:
    print("[FAIL] Logic check for partial info failed (Might need code update if not handled)")
    # Note: My current regex detects age/gender independently, so this should work if regex works.

# Test 3: Full Details
print("\n--- Test 3: Full Details ---")
data3 = test_report("I took Ibuprofen (30yo Male) and had a headache", "Report with all details")
if data3 and data3.get('report_saved') is True:
    print("[PASS] Report saved")
else:
    print("[FAIL] Report not saved")
