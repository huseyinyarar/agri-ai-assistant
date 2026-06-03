import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv(override=True)
key = os.getenv('GEMINI_API_KEY')

models_to_test = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash-lite-001"
]

print("--- GOOGLE GEMINI API TESTİ BAŞLIYOR ---")
for model in models_to_test:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    data = json.dumps({"contents":[{"parts":[{"text":"Merhaba, nasılsın?"}]}]}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    try:
        response = urllib.request.urlopen(req)
        print(f"✅ {model}: BAŞARILI (Çalışıyor)")
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode('utf-8')
        try:
            err_json = json.loads(error_msg)
            reason = err_json.get("error", {}).get("message", error_msg)
        except:
            reason = error_msg
        print(f"❌ {model}: HATA {e.code} - {reason[:100]}...")
    except Exception as e:
        print(f"❌ {model}: BEKLENMEYEN HATA - {str(e)}")
