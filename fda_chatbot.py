import requests
import json
import re
import os
import datetime

# --- Constants ---
OPENFDA_API_URL = "https://api.fda.gov/drug/event.json"
DATA_FILE = "adverse_events.json"

# --- Core Functions ---

def fetch_adverse_events(drug_name):
    """
    Fetches adverse events for a specific drug from the OpenFDA API.
    
    Args:
        drug_name (str): The name of the drug to search for.
        
    Returns:
        listOrNone: A list of adverse event summaries (strings) or None if error/no data.
    """
    print(f"DEBUG: Fetching adverse events for '{drug_name}'...")
    try:
        # Construct query: search for the medicinal product
        # limit=5 to get a snapshot
        params = {
            'search': f'patient.drug.medicinalproduct:"{drug_name}"',
            'limit': 5
        }
        response = requests.get(OPENFDA_API_URL, params=params)
        response.raise_for_status() # Raise error for bad status codes
        
        data = response.json()
        
        if 'results' not in data:
            return None
            
        events = []
        for result in data['results']:
            # Extract reaction(s) from the patient.reaction list
            reactions = [r.get('reactionmeddrapt', 'Unknown') for r in result.get('patient', {}).get('reaction', [])]
            
            # Extract basic implementation
            # safetyreportid is good for unique ID
            report_id = result.get('safetyreportid', 'N/A')
            
            events.append(f"Report {report_id}: {', '.join(reactions)}")
            
        return events

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from OpenFDA: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

def extract_adverse_event(user_input):
    """
    Extracts drug name and adverse reaction from user input using basic NLP/Regex.
    
    Args:
        user_input (str): The user's message.
        
    Returns:
        dictOrNone: A dictionary with 'drug', 'reaction', 'timestamp' keys or None if not found.
    """
    # Regex patterns to capture "took [DRUG] and experienced [REACTION]"
    # This is a basic implementation and can be improved with more patterns or NLP.
    patterns = [
        r"took\s+(?P<drug>.*?)\s+and\s+experienced\s+(?P<reaction>.*)",
        r"took\s+(?P<drug>.*?)\s+and\s+felt\s+(?P<reaction>.*)",
        r"after\s+taking\s+(?P<drug>.*?)\s*,\s*I\s+had\s+(?P<reaction>.*)",
        r"used\s+(?P<drug>.*?)\s+and\s+got\s+(?P<reaction>.*)"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_input, re.IGNORECASE)
        if match:
            return {
                "drug": match.group("drug").strip(),
                "reaction": match.group("reaction").strip(),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    return None

def save_adverse_event(event_data):
    """
    Saves the extracted adverse event to a local JSON file.
    
    Args:
        event_data (dict): The dictionary containing event details.
    """
    try:
        # Load existing data
        if os.path.exists(DATA_FILE):
             with open(DATA_FILE, 'r') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = [] # Handle corrupted/empty file
        else:
            existing_data = []
            
        # Append new event
        existing_data.append(event_data)
        
        # Save back to file
        with open(DATA_FILE, 'w') as f:
            json.dump(existing_data, f, indent=4)
            
        print(f"Successfully saved report: Drug='{event_data['drug']}', Reaction='{event_data['reaction']}'")
        
    except Exception as e:
        print(f"Error saving data: {e}")

def chatbot():
    """
    Main chatbot loop for the command line interface.
    """
    print("--------------------------------------------------")
    print("Welcome to the SafeWatch AI FDA Adverse Event Chatbot!")
    print("--------------------------------------------------")
    print("You can ask me to:")
    print("1. 'Show adverse events for [drug_name]'")
    print("2. Report an event: 'I took [drug] and experienced [reaction]'")
    print("Type 'exit' or 'quit' to stop.")
    print("--------------------------------------------------")

    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['exit', 'quit']:
            print("Chatbot: Goodbye!")
            break
            
        if not user_input:
            continue

        # Feature 1: Query adverse events
        # Regex to capture "Show adverse events for [drug]"
        query_match = re.search(r"show\s+adverse\s+events\s+for\s+(.*)", user_input, re.IGNORECASE)
        if query_match:
            drug_name = query_match.group(1).strip()
            print(f"Chatbot: Searching for adverse events associated with '{drug_name}'...")
            events = fetch_adverse_events(drug_name)
            
            if events:
                print(f"Chatbot: Found {len(events)} recent reports for {drug_name}:")
                for i, event in enumerate(events, 1):
                    print(f"  {i}. {event}")
            else:
                print(f"Chatbot: I couldn't find any specific adverse event reports for '{drug_name}' right now.")
            continue

        # Feature 2: Detect adverse event from user input
        extracted_data = extract_adverse_event(user_input)
        if extracted_data:
            print(f"Chatbot: I detected a potential adverse event.")
            print(f"  Drug detected: {extracted_data['drug']}")
            print(f"  Reaction detected: {extracted_data['reaction']}")
            
            confirm = input("Chatbot: Would you like me to save this report? (yes/no): ").lower()
            if confirm in ['yes', 'y']:
                save_adverse_event(extracted_data)
                print("Chatbot: Report saved.")
            else:
                print("Chatbot: Report discarded.")
            continue
            
        # Fallback response
        print("Chatbot: I didn't quite catch that. Try asking 'Show adverse events for [drug]' or tell me 'I took [drug] and experienced [symptom]'.")

if __name__ == "__main__":
    chatbot()
