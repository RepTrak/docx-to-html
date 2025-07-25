import json

def load_prompt_template(path="md_prompt.txt"):
    """Load plain-text Markdown prompt template with [[markdown]] and [[json-schema]] placeholders."""
    with open(path, encoding="utf-8") as f:
        return f.read()

def render_prompt(md_str: str, schema_dict: dict, template: str) -> str:
    """Substitute [[markdown]] and [[json-schema]] in the prompt template."""
    schema_str = json.dumps(schema_dict, indent=2)
    return template.replace("[[markdown]]", md_str.strip()).replace("[[json-schema]]", schema_str)

def build_messages(md_path: str, schema_path: str, prompt_template_path: str = "md_prompt.txt"):
    """Build LLM-compatible message list using Markdown + schema + prompt template."""
    with open(md_path, encoding="utf-8") as f:
        md_content = f.read()
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    prompt_template = load_prompt_template(prompt_template_path)
    user_prompt = render_prompt(md_content, schema, prompt_template)
    messages = [
        {
            "role": "user",
            "content": user_prompt
        }
    ]

    # Return both messages and system prompt separately
    return {
        "messages": messages,
        "system": "You are a JSON converter. Only return valid JSON that matches the provided schema."
    }
