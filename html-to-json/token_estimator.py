import os
import json
import requests
from dotenv import load_dotenv
from json_prompt import render_prompt

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-3-haiku-20240307"

def call_claude_estimator(prompt_text):
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": MODEL,
        "max_tokens": 256,  # just want a number
        "system": "You are a precise estimator of JSON output token size.",
        "messages": [{ "role": "user", "content": prompt_text }]
    }

    response = requests.post(ANTHROPIC_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()["content"][0]["text"]

def estimate_tokens(html_path, schema_path, partial_json_path, prompt_template_path):
    with open(html_path, encoding="utf-8") as f:
        html = f.read()

    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    with open(partial_json_path, encoding="utf-8") as f:
        partial_json = f.read()

    with open(prompt_template_path, encoding="utf-8") as f:
        prompt_template = f.read()

    full_prompt = (
        prompt_template
        .replace("[[html]]", html.strip())
        .replace("[[json-schema]]", json.dumps(schema, indent=2))
        .replace("[[partial-json]]", partial_json.strip())
    )

    print("Sending estimation prompt to Claude...")
    result = call_claude_estimator(full_prompt)
    print("\nEstimated total output tokens:", result.strip())

if __name__ == "__main__":
    html_path = "/home/jliu/docx-to-html/data/html_output/svb_qnr_-_main_-_english__february_2024_for_ingestion_cleaned.html"
    schema_path = "schema.json"
    partial_json_path = "/home/jliu/docx-to-html/data/json_final/svb_qnr_-_main_-_english__february_2024_for_ingestion_invalid.json"
    prompt_template_path = "tokenizer_prompt.txt"

    estimate_tokens(html_path, schema_path, partial_json_path, prompt_template_path)
