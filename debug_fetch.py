import requests
import traceback

def debug_fetch():
    url = "https://api.fda.gov/drug/event.json"
    params = {
        'search': 'patient.drug.medicinalproduct:"aspirin"',
        'limit': 1
    }
    print(f"Connecting to {url}...")
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:100]}...")
    except Exception:
        traceback.print_exc()

if __name__ == "__main__":
    debug_fetch()
