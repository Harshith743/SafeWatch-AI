import os
import traceback
from dotenv import load_dotenv
from urllib.parse import urlparse, quote_plus
from sqlalchemy import create_engine

load_dotenv()

raw_url = os.environ.get("DATABASE_URL")
if raw_url:
    fixed_url = raw_url.replace("[iAM#@R5hu743]", "iAM%23%40R5hu743")
    print("Using fixed URL format:", fixed_url)
    
    try:
        engine = create_engine(fixed_url)
        with engine.connect() as conn:
            print("SUCCESS: Connected to DB!")
    except Exception as e:
        print("Failed to connect:")
        traceback.print_exc()

