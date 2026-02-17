from fda_chatbot import fetch_adverse_events, extract_adverse_event, save_adverse_event
import os

def test_fetch():
    print("Testing fetch_adverse_events...")
    events = fetch_adverse_events("aspirin")
    if events:
        print(f"Success: Fetched {len(events)} events.")
    else:
        print("Failure: Could not fetch events.")

def test_extract_and_save():
    print("Testing extract_adverse_event...")
    input_text = "I took paracetamol and experienced nausea"
    data = extract_adverse_event(input_text)
    if data:
        print(f"Success: Extracted {data}")
        save_adverse_event(data)
        if os.path.exists("adverse_events.json"):
            print("Success: adverse_events.json created.")
        else:
            print("Failure: adverse_events.json not found.")
    else:
        print("Failure: Could not extract data.")

if __name__ == "__main__":
    test_fetch()
    # test_extract_and_save()
