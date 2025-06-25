import os
import json
import requests
import sys
from json_prompt import build_messages
from validate import main as validate_output

GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # or hardcode for testing
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "mixtral-8x7b-32768"

def call_groq(messages):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 4096,
    }

    response = requests.post(GROQ_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]

def extract_json_from_markdown(text):
    """Extract JSON from a code block if wrapped in ```json ... ```"""
    if text.strip().startswith("```json"):
        return text.strip().split("```json")[1].split("```")[0].strip()
    return text

def main():
    html_path = "/home/jliu/docx-to-html/data/html_output/svb_qnr_-_main_-_english__february_2024_for_ingestion_cleaned.html"
    schema_path = "schema.json"
    metaprompt_path = "metaprompt.xml"

    print(f"Building prompt from:\n- HTML: {html_path}\n- Schema: {schema_path}")
    messages = build_messages(html_path, schema_path, metaprompt_path)

    result = call_groq(messages)

    try:
        clean_result = extract_json_from_markdown(result)
        data = json.loads(clean_result)
    except json.JSONDecodeError as e:
        print("LLM returned invalid JSON:")
        print(result)
        sys.exit(1)

    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print("Response saved to output.json")
    print("Running validation...")
    validate_output()

if __name__ == "__main__":
    main()
