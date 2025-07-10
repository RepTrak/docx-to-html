import os
import json
from anthropic import Anthropic
from json_prompt import build_messages
from jsonschema import Draft7Validator

input_folder = "/home/jliu/docx-to-html/data/html_chunks_cleaned"
output_folder = "/home/jliu/docx-to-html/data/json_chunks"
schema_path = '/home/jliu/docx-to-html/html-to-json/schema.json'
os.makedirs(output_folder, exist_ok=True)

model = "claude-3-haiku-20240307"
anthropic = Anthropic()

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
        with open(input_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        messages = build_messages(html_content, schema_path)

        response = anthropic.messages.create(
            model=model,
            messages=messages,
            max_tokens=4096,
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
