
from fda_chatbot import extract_adverse_event, parse_message
import re

text = "I took Ibuprofen (30yo Male) and had a headache"
print(f"Testing: '{text}'")
result = extract_adverse_event(text)
print(f"Extract result: {result}")
parse_res = parse_message(text)
print(f"Parse result: {parse_res}")

# Double check regex manually
pattern = r"took\s+(?P<drug>.*?)\s+and\s+had\s+(?P<reaction>.*)"
match = re.search(pattern, text, re.IGNORECASE)
print(f"Manual regex match: {match}")
if match:
    print(match.groupdict())
