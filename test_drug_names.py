import asyncio
import json
from api.utils import parse_with_llm, parse_message, fetch_adverse_events, fetch_drug_statistics
from dotenv import load_dotenv
import os

load_dotenv()

TEST_CASES = [
    "What are the side effects of Aspirin?",          # Generic, well-known
    "What happens if I take Tylenol?",                # Brand name (Acetaminophen)
    "Side effects of Ibeuprofen",                     # Misspelled generic
    "Side effects of Advill",                         # Misspelled brand name
]

def run_tests():
    print(f"--- SafeWatch AI Drug Name Extraction & FDA Search Test ---\n")
    
    for i, test_case in enumerate(TEST_CASES):
        print(f"Test {i+1}: \"{test_case}\"")
        
        # 1. Test LLM Extraction
        parsed = parse_with_llm(test_case)
        if not parsed:
            print("  LLM Extraction Failed, trying regex fallback...")
            parsed = parse_message(test_case)
            
        print(f"  [Extraction] Intent: {parsed.get('intent')}, Drug: '{parsed.get('drug')}'")
        
        drug_name = parsed.get("drug")
        if not drug_name:
            print("  [Result] FAILED to extract drug name.\n")
            continue
            
        # 2. Test OpenFDA Search
        # OpenFDA handles medicinalproduct search. Let's see if it works as-is.
        events = fetch_adverse_events(drug_name)
        stats = fetch_drug_statistics(drug_name)
        
        if events:
            print(f"  [OpenFDA] SUCCESS - Found {len(events)} recent events.")
        else:
            print(f"  [OpenFDA] NO EVENTS FOUND for drug '{drug_name}' in medicinalproduct field.")
            
        print("-" * 50)

if __name__ == "__main__":
    run_tests()
