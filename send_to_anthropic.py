import os
import json
from src.llm import LLMClient
from html_prompt_builder import build_messages
from jsonschema import Draft7Validator
from dotenv import load_dotenv

load_dotenv('/Users/acevallos/workspace/docx-to-html/.env')
input_folder = "/Users/acevallos/workspace/docx-to-html/data/html_chunks_cleaned"
output_folder = "/Users/acevallos/workspace/docx-to-html/data/json_chunks_from_html"
schema_path = '/Users/acevallos/workspace/docx-to-html/html-to-json/schema.json'
os.makedirs(output_folder, exist_ok=True)

# Initialize LLM client with retry strategy - API keys will be loaded from config.py
llm_client = LLMClient(
    providers=["anthropic"],  # Can add "openai" for fallback
    retry_attempts=3,
    retry_delay=1.0,
    retry_backoff=2.0
)

results = []

def validate_with_schema(schema_path, instance):
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    return errors

for filename in sorted(os.listdir(input_folder)):
    if not filename.endswith(".html"):
        continue

    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename.replace(".html", ".json"))

    print(f"\n--- Processing: {filename} ---")
    try:
        # Get both messages and system prompt
        prompt_data = build_messages(
            html_path=input_path, 
            schema_path=schema_path,
            prompt_template_path="/Users/acevallos/workspace/docx-to-html/html-to-json/html_prompt.txt"
        )

        # Use the new LLM client
        response = llm_client.completion(
            messages=prompt_data["messages"],
            system=prompt_data["system"],
            model="claude-3-5-haiku-20241022",
            max_tokens=8192,
            temperature=0.0,
            provider="anthropic"  # Can be omitted to allow fallback
        )

        output_text = response["content"]
        usage = response["usage"]

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)

        try:
            parsed = json.loads(output_text)
            errors = validate_with_schema(schema_path, parsed)
            if not errors:
                print(f"✔ Validated ({usage['input_tokens']} in, {usage['output_tokens']} out)")
                results.append((filename, "✔", usage['input_tokens'], usage['output_tokens']))
            else:
                print(f"⚠ Invalid JSON ({usage['input_tokens']} in, {usage['output_tokens']} out):")
                for err in errors:
                    print(f"  - {list(err.path)}: {err.message}")
                results.append((filename, "⚠ Schema validation failed", usage['input_tokens'], usage['output_tokens']))
        except Exception as ve:
            print(f"⚠ Invalid JSON ({usage['input_tokens']} in, {usage['output_tokens']} out): {ve}")
            results.append((filename, f"⚠ {ve}", usage['input_tokens'], usage['output_tokens']))

    except Exception as e:
        print(f"✖ Error: Failed to process {filename}: {e}")
        results.append((filename, f"✖ {e}", None, None))
