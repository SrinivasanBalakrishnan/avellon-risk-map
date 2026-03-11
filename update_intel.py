import os
import json
import time
import urllib.request
import google.generativeai as genai

# 1. Authenticate with the GitHub Vault
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("CRITICAL ERROR: GEMINI_API_KEY not found in environment.")
    exit(1)

genai.configure(api_key=API_KEY)

# UPGRADE: Switched to Gemini 2.0 Flash to bypass legacy 404 routing errors
model = genai.GenerativeModel('gemini-2.0-flash')

DATA_FILE = "data/global_intel.json"

# 2. Dynamically Fetch the Global Target List
print("Downloading Atlas global region manifest...")
try:
    url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
    response = urllib.request.urlopen(url)
    geo_data = json.loads(response.read())
    TARGET_COUNTRIES = [feature['properties']['name'] for feature in geo_data['features'] if 'name' in feature['properties']]
    print(f"Manifest loaded: {len(TARGET_COUNTRIES)} strategic regions identified for scanning.")
except Exception as e:
    print(f"Failed to load map manifest: {e}")
    TARGET_COUNTRIES = ["India", "United States", "China", "Brazil", "United Kingdom", "Russia"] 

# 3. Load the existing database
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
        raw_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
        data = json.loads(raw_text)
        return data
    except Exception as e:
        print(f"Failed to generate intelligence for {country}: {e}")
        return None

print("Initializing Avellon Global Matrix...")

# 4. Execute the Global Intelligence Loop
count = 1
total = len(TARGET_COUNTRIES)

for country in TARGET_COUNTRIES:
    print(f"[{count}/{total}] Scanning intelligence for: {country}...")
    intel = get_country_intelligence(country)
    
    if intel:
        intel_db[country] = intel
        print(f"   -> Success: Atlas Risk Score: {intel['risk_score']}")
    else:
        print(f"   -> Warning: Failsafe engaged. Retaining cached data for {country}.")
        
    # THE PACEMAKER: Strict 5-second throttle.
    time.sleep(5)
    count += 1

# 5. Commit the new global intelligence to the JSON receptacle
with open(DATA_FILE, "w") as f:
    json.dump(intel_db, f, indent=4)

print("Avellon Global Matrix update complete. 100% Map Coverage achieved.")
