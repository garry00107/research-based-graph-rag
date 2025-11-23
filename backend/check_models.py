import os
from dotenv import load_dotenv
import requests

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")
if not api_key:
    print("No API Key found")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "application/json"
}

try:
    response = requests.get("https://integrate.api.nvidia.com/v1/models", headers=headers)
    if response.status_code == 200:
        models = response.json().get('data', [])
        print("Available Models:")
        for m in models:
            if 'nvidia' in m['id'] or 'embed' in m['id']:
                print(f"- {m['id']}")
    else:
        print(f"Error: {response.status_code} - {response.text}")
except Exception as e:
    print(f"Error: {e}")
