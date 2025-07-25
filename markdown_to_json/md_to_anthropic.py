import os
import json
from anthropic import Anthropic
from jsonschema import Draft7Validator
from dotenv import load_dotenv
from md_prompt_builder import build_messages  # assumes build_messages(md_path, schema_path, prompt_template_path)

# Load API key from .env file
load_dotenv('/home/jliu/docx-to-html/.env')

# Paths
input_folder = "/home/jliu/docx-to-html/data/markdown_chunks"
output_folder = "/home/jliu/docx-to-html/data/json_chunks_from_markdown"
schema_path = "/home/jliu/docx-to-html/html-to-json/schema.json"  # reuse HTML schema
prompt_template_path = "/home/jliu/docx-to-html/markdown_to_json/md_prompt.txt"

os.makedirs(output_folder, exist_ok=True)

# Initialize Claude
model = "claude-3-5-haiku-20241022"
anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

results = []

def validate_with_schema(schema_path, instance):
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    return errors

for filename in sorted(os.listdir(input_folder)):
    if not filename.endswith(".md"):
        continue

    input_path = os.path.join(input_folder, filename)
    output_path = os.path.join(output_folder, filename.replace(".md", ".json"))

    print(f"\n--- Processing: {filename} ---")
    try:
        prompt_data = build_messages(
            md_path=input_path,
            schema_path=schema_path,
            prompt_template_path=prompt_template_path
        )

        response = anthropic.messages.create(
            model=model,
            messages=prompt_data["messages"],
            system=prompt_data["system"],
            max_tokens=8192,
            temperature=0.0,
        )

        output_text = response.content[0].text.strip()
        usage = response.usage

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output_text)

        try:
            parsed = json.loads(output_text)
            errors = validate_with_schema(schema_path, parsed)
            if not errors:
                print(f"✔ Validated ({usage.input_tokens} in, {usage.output_tokens} out)")
                results.append((filename, "✔", usage.input_tokens, usage.output_tokens))
            else:
                print(f"⚠ Invalid JSON ({usage.input_tokens} in, {usage.output_tokens} out):")
                for err in errors:
                    print(f"  - {list(err.path)}: {err.message}")
                results.append((filename, "⚠ Schema validation failed", usage.input_tokens, usage.output_tokens))
        except Exception as ve:
            print(f"⚠ Invalid JSON ({usage.input_tokens} in, {usage.output_tokens} out): {ve}")
            results.append((filename, f"⚠ {ve}", usage.input_tokens, usage.output_tokens))

    except Exception as e:
        print(f"✖ Error: Failed to process {filename}: {e}")
        results.append((filename, f"✖ {e}", None, None))

# Summary
print("\n=== JSON Extraction Summary ===")
for fname, status, in_tok, out_tok in results:
    token_info = f"({in_tok} in, {out_tok} out)" if in_tok is not None else ""
    print(f"{status:<5} {fname:<50} {token_info}")
