import json
import sys
from jsonschema import validate, Draft7Validator, ValidationError

def main(schema_path="schema.json", output_path="output.json"):
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    with open(output_path, encoding="utf-8") as f:
        output = json.load(f)

    print("Loaded schema and output.")
    print("Validating...")

    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(output), key=lambda e: e.path)

    if not errors:
        print("Validation successful. output.json conforms to schema.json.")
    else:
        print(f"Validation failed with {len(errors)} error(s):\n")
        for err in errors:
            print(f"- {list(err.path)}: {err.message}")
        sys.exit(1)

if __name__ == "__main__":
    main()
