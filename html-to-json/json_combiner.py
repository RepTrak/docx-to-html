import os
import json

# Define paths
input_dir = "/home/jliu/docx-to-html/data/json_chunks_from_html"
output_path = "/home/jliu/docx-to-html/data/json_final/json_combined_from_html_7_25.json"

all_sections = []

# Iterate over all JSON chunk files
for filename in sorted(os.listdir(input_dir)):
    if filename.endswith(".json"):
        filepath = os.path.join(input_dir, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Remove ```json and ``` markers
        cleaned_lines = [line for line in lines if not line.strip().startswith("```")]

        joined_json = "".join(cleaned_lines)

        try:
            json_data = json.loads(joined_json)
            sections = json_data.get("sections", [])
            all_sections.extend(sections)
        except json.JSONDecodeError as e:
            print(f"\nError decoding {filename}: {e}")
            lineno = e.lineno
            colno = e.colno

            context_range = range(max(0, lineno - 2), min(len(cleaned_lines), lineno + 3))

            for i in context_range:
                prefix = ">>>" if i + 1 == lineno else "   "
                print(f"{prefix} Line {i + 1}: {cleaned_lines[i].rstrip()}")

# Final combined JSON structure
combined = {
    "sections": all_sections
}

# Save to output file
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(combined, f, indent=2)

print(f"\nCombined JSON saved to {output_path}")
