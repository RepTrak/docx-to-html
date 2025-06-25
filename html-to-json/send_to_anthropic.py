import os
import json
import sys
import requests
from json_prompt import build_messages
from validate import main as validate_output

from dotenv import load_dotenv
load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-3-sonnet-20240229"  # or "claude-3-opus-20240229"

def call_anthropic(messages):
    system_prompt = messages[0]["content"]
    user_prompt = messages[1]["content"]

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "system": system_prompt,
        "messages": [
            { "role": "user", "content": user_prompt }
        ]
    }

    response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["content"][0]["text"]

def extract_json_from_markdown(text):
    """Extract JSON from a code block if wrapped in ```json ... ```"""
    if text.strip().startswith("```json"):
        return text.strip().split("```json")[1].split("```")[0].strip()
    return text

def main():
    html_path = "/home/jliu/docx-to-html/data/html_output/svb_qnr_-_main_-_english__february_2024_for_ingestion_cleaned.html"
    schema_path = "schema.json"
    metaprompt_path = "metaprompt.xml"

    print("Building Anthropic prompt...")
    messages = build_messages(html_path, schema_path, metaprompt_path)
    result = call_anthropic(messages)

    try:
        clean_result = extract_json_from_markdown(result)
        data = json.loads(clean_result)
    except json.JSONDecodeError:
        print("Claude returned invalid JSON:")
        print(result)
        sys.exit(1)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Response saved to output.json")
    print("Running validation...")
    validate_output()

if __name__ == "__main__":
    main()
