import os
import json
import time
import google.generativeai as genai

# 1. Authenticate with Vault
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("CRITICAL ERROR: GEMINI_API_KEY not found.")
    exit(1)

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-8b') # High-volume enterprise model

DATA_FILE = "data/global_intel.json"
RAW_DATA_FILE = "outputs/raw_intel.json"

# 2. Load the Harvester's Raw Data
try:
    with open(RAW_DATA_FILE, "r") as f:
        raw_intel = json.load(f)
except FileNotFoundError:
    print("CRITICAL ERROR: Harvester data not found. Run fetch_alerts.py first.")
    exit(1)

# 3. Load Existing Failsafe Database
try:
    with open(DATA_FILE, "r") as f:
        intel_db = json.load(f)
except FileNotFoundError:
    intel_db = {}

def generate_strategic_brief(country, data):
    headlines_text = " | ".join(data['headlines']) if data['headlines'] else "No breaking alerts."
    sentiment = data['nlp_sentiment']
    
    prompt = f"""
    You are an elite geopolitical risk analyst for Avellon Intelligence.
    Analyze the following real-time data for {country}:
    
    - LIVE HEADLINES: {headlines_text}
    - NLP SENTIMENT SCORE: {sentiment} (Scale: -1.0 is extreme crisis, +1.0 is highly stable)
    
    Based ONLY on this factual data, generate a strategic briefing.
    You MUST respond ONLY with a valid JSON object. Do not use markdown blocks.
    
    Structure strictly like this:
    {{
        "geo_posture": "1-2 precise sentences analyzing geopolitical/diplomatic events based on the headlines.",
        "biz_opportunities": "1-2 precise sentences analyzing economic realities or supply chain risks.",
        "risk_score": <Calculate an integer between 1 and 100. Use the NLP Sentiment Score to heavily influence this. A highly negative sentiment means a score below 40. A highly positive sentiment means a score above 70.>
    }}
    """
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip().removeprefix('```json').removesuffix('```').strip()
        return json.loads(raw_text)
    except Exception as e:
        print(f"   -> Gemini failed for {country}: {e}")
        return None

print("Initializing Avellon Synthesizer...")

# 4. The Synthesis Loop
count = 1
total = len(raw_intel)

for country, data in raw_intel.items():
    print(f"[{count}/{total}] Synthesizing: {country}...")
    
    if data['headlines']:
        intel = generate_strategic_brief(country, data)
        if intel:
            intel_db[country] = intel
            print(f"   -> Success. Atlas Risk Score: {intel['risk_score']}")
        else:
            print("   -> Warning: Retaining cached data.")
    else:
        print("   -> No news detected. Retaining baseline cached data.")
        
    time.sleep(6) # The API Pacemaker
    count += 1

# 5. Commit to Final Receptacle
os.makedirs("data", exist_ok=True)
with open(DATA_FILE, "w") as f:
    json.dump(intel_db, f, indent=4)

print("Synthesis complete. Avellon Atlas matrix updated.")
