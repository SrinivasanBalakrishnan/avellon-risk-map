import os
import json
import time
import google.generativeai as genai

# 1. Authenticate with the GitHub Vault
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("CRITICAL ERROR: GEMINI_API_KEY not found in environment.")
    exit(1)

genai.configure(api_key=API_KEY)
# Using Gemini 1.5 Flash for enterprise-grade speed and reliability
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Target Acquisition List (Tier 1 Nations for the Prototype)
# We process a strategic batch to respect free-tier API limits. You can expand this later.
TARGET_COUNTRIES = ["India", "United States", "China", "Brazil", "Germany", "Russia", "Saudi Arabia"]

DATA_FILE = "data/global_intel.json"

# 3. Load the existing database to act as a failsafe
try:
    with open(DATA_FILE, "r") as f:
        intel_db = json.load(f)
except FileNotFoundError:
    intel_db = {}

def get_country_intelligence(country):
    prompt = f"""
    You are an elite geopolitical risk analyst for Avellon Intelligence.
    Provide a strategic intelligence briefing for {country}.
    
    You MUST respond ONLY with a valid JSON object. Do not use markdown blocks like ```json.
    
    Structure strictly like this:
    {{
        "geo_posture": "1-2 precise sentences on current geopolitical strategy, military, or diplomatic positioning.",
        "biz_opportunities": "1-2 precise sentences on immediate macro-economic and sector-specific business opportunities or supply chain risks.",
        "risk_score": <an integer between 1 and 100, where 100 is highly stable/favorable and 1 is extreme risk/unfavorable>
    }}
    """
    try:
        response = model.generate_content(prompt)
        # Strip markdown formatting just in case the AI includes it
        raw_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
        data = json.loads(raw_text)
        return data
    except Exception as e:
        print(f"Failed to generate intelligence for {country}: {e}")
        return None

print("Initializing Avellon AI Matrix...")

# 4. Execute the Intelligence Gathering Loop
for country in TARGET_COUNTRIES:
    print(f"Scanning intelligence for: {country}...")
    intel = get_country_intelligence(country)
    
    if intel:
        intel_db[country] = intel
        print(f"Success: {country} updated. Atlas Risk Score: {intel['risk_score']}")
    else:
        print(f"Warning: Failsafe engaged. Retaining cached data for {country}.")
        
    # STRICT THROTTLE: Pausing for 4 seconds to prevent API limit bans
    time.sleep(4)

# 5. Commit the new intelligence to the JSON receptacle
with open(DATA_FILE, "w") as f:
    json.dump(intel_db, f, indent=4)

print("Avellon Global Matrix update complete. Terminal closing.")
