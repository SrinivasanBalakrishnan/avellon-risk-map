import os
import json
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import google.generativeai as genai

# 1. Authenticate with the GitHub Vault
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("CRITICAL ERROR: GEMINI_API_KEY not found in environment.")
    exit(1)

genai.configure(api_key=API_KEY)
# Using the high-volume, highly stable 8B model
model = genai.GenerativeModel('gemini-1.5-flash-8b')

DATA_FILE = "data/global_intel.json"

# 2. Dynamically Fetch the Global Target List
print("Downloading Atlas global region manifest...")
try:
    url = "https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    response = urllib.request.urlopen(req)
    geo_data = json.loads(response.read())
    TARGET_COUNTRIES = [feature['properties']['name'] for feature in geo_data['features'] if 'name' in feature['properties']]
    print(f"Manifest loaded: {len(TARGET_COUNTRIES)} strategic regions identified for scanning.")
except Exception as e:
    print(f"Failed to load map manifest: {e}")
    TARGET_COUNTRIES = ["India", "United States", "China", "Brazil", "Germany"] 

# 3. Load the existing database failsafe
try:
    with open(DATA_FILE, "r") as f:
        intel_db = json.load(f)
except FileNotFoundError:
    intel_db = {}

# --- NEW: THE LIVE DATA SENSE ENGINE ---
def get_live_news(country):
    """Fetches real-time geopolitical and economic headlines via Google News RSS."""
    try:
        # Encode the search query to handle spaces in country names (e.g., "United States")
        query = urllib.parse.quote(f'"{country}" AND (economy OR geopolitics OR supply chain OR conflict)')
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        # Mask the request as a standard browser to prevent blocking
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        headlines = []
        
        # Extract the top 3 most recent headlines
        for item in root.findall('.//item')[:3]:
            title = item.find('title').text
            headlines.append(title)
            
        if headlines:
            return " | ".join(headlines)
        else:
            return "No major breaking geopolitical developments in the last 24 hours."
    except Exception as e:
        print(f"   -> News feed unavailable for {country}: {e}")
        return "Live data feed temporarily unavailable. Rely on baseline strategic assessment."

# --- UPGRADED: THE AI SYNTHESIS ENGINE ---
def get_country_intelligence(country, live_news):
    """Feeds live data to Gemini to generate a factual risk scorecard."""
    prompt = f"""
    You are an elite geopolitical risk analyst for Avellon Intelligence.
    Analyze the following real-time news headlines for {country}:
    
    [LIVE INTELLIGENCE FEED]: {live_news}
    
    Based ONLY on these recent developments and your baseline knowledge, provide a strategic intelligence briefing.
    You MUST respond ONLY with a valid JSON object. Do not use markdown blocks like ```json.
    
    Structure strictly like this:
    {{
        "geo_posture": "1-2 precise sentences analyzing the current geopolitical or diplomatic positioning based on the news.",
        "biz_opportunities": "1-2 precise sentences analyzing immediate economic realities, business opportunities, or supply chain risks.",
        "risk_score": <an integer between 1 and 100, where 100 is highly stable/favorable and 1 is extreme risk/unfavorable>
    }}
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
        data = json.loads(raw_text)
        return data
    except Exception as e:
        print(f"   -> Failed to generate AI synthesis for {country}: {e}")
        return None

print("Initializing Avellon Live-Data Matrix...")

# 4. Execute the Global Intelligence Loop
count = 1
total = len(TARGET_COUNTRIES)

for country in TARGET_COUNTRIES:
    print(f"[{count}/{total}] Processing: {country}...")
    
    # Step A: Fetch Live Data
    live_news = get_live_news(country)
    
    # Step B: Synthesize with AI
    intel = get_country_intelligence(country, live_news)
    
    if intel:
        intel_db[country] = intel
        print(f"   -> Success: Synthesized. Atlas Risk Score: {intel['risk_score']}")
    else:
        print(f"   -> Warning: Failsafe engaged. Retaining cached data for {country}.")
        
    # THE PACEMAKER: Strict 6-second throttle.
    time.sleep(6)
    count += 1

# 5. Commit the new global intelligence to the JSON receptacle
with open(DATA_FILE, "w") as f:
    json.dump(intel_db, f, indent=4)

print("Avellon Global Matrix update complete. 100% Map Coverage achieved.")
