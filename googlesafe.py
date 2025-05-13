# safe_browsing.py
import requests
import json

def check_url_google_safe_browsing(api_key, url_to_check):
    url = "https://safebrowsing.googleapis.com/v4/threatMatches:find?key=" + api_key

    payload = {
        "client": {
            "clientId": "yourcompanyname",
            "clientVersion": "1.5.2"
        },
        "threatInfo": {
            "threatTypes": [
                "MALWARE", 
                "SOCIAL_ENGINEERING", 
                "UNWANTED_SOFTWARE", 
                "POTENTIALLY_HARMFUL_APPLICATION"
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url_to_check}]
        }
    }

    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    if response.status_code == 200:
        result = response.json()
        if "matches" in result:
            return f"⚠️ URL is unsafe: {result['matches']}"
        else:
            return "✅ URL is safe (not found in Safe Browsing blacklist)"
    else:
        return f"❌ Error: {response.status_code} - {response.text}"
