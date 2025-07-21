# use this to test connection to anthropic API

import os
import requests
from dotenv import load_dotenv

load_dotenv()
headers = {
    "x-api-key": os.getenv("ANTHROPIC_API_KEY"),
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

payload = {
    "model": "claude-3-5-haiku-20241022", # 8k tokens
    # "claude-3-haiku-20240307" # 4k tokens
    # "claude-sonnet-4-20250514" # 16k tokens
    
    "max_tokens": 64,
    "system": "test",
    "messages": [{"role": "user", "content": "hi"}]
}

res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
print(res.status_code, res.text)
