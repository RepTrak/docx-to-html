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
MODEL = "claude-3-haiku-20240307"

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
    data = response.json()

    return data["content"][0]["text"], data.get("usage", {})

def extract_json_from_markdown(text):
    """Extract JSON from a code block if wrapped in ```json ... ```"""
    if text.strip().startswith("```json"):
        return text.strip().split("```json")[1].split("```")[0].strip()
    return text

def main():
    html_path = "/home/jliu/docx-to-html/data/html_output/svb_qnr_-_main_-_english__february_2024_for_ingestion_cleaned.html"
    schema_path = "schema.json"
    prompt_template_path = "prompt.txt"

    print("Building Anthropic prompt...")
    messages = build_messages(html_path, schema_path, prompt_template_path)
    result, usage = call_anthropic(messages)

    clean_result = extract_json_from_markdown(result)

    # Derive filename and output folder
    html_filename = os.path.basename(html_path).replace("_cleaned.html", "")
    output_dir = "/home/jliu/docx-to-html/data/json_final"
    os.makedirs(output_dir, exist_ok=True)

    try:
        data = json.loads(clean_result)
        final_path = os.path.join(output_dir, f"{html_filename}_valid.json")
        with open(final_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Parsed JSON saved to: {final_path}")
        print("Running validation...")
        validate_output(schema_path=schema_path, output_path=final_path)
    except json.JSONDecodeError:
        final_path = os.path.join(output_dir, f"{html_filename}_invalid.json")
        with open(final_path, "w", encoding="utf-8") as f:
            f.write(clean_result)
        print("Claude returned invalid JSON.")
        print(f"Raw output saved to: {final_path}")

    print("\n Claude usage report:")
    print(f" - Input tokens:  {usage.get('input_tokens', 'N/A')}")
    print(f" - Output tokens: {usage.get('output_tokens', 'N/A')}")

if __name__ == "__main__":
    main()
