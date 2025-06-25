import json

def load_prompt_template(path="prompt.txt"):
    """Load plain-text prompt template with [[html]] and [[json-schema]] placeholders."""
    with open(path, encoding="utf-8") as f:
        return f.read()

def render_prompt(html_str: str, schema_dict: dict, template: str) -> str:
    """Substitute [[html]] and [[json-schema]] in the prompt template."""
    schema_str = json.dumps(schema_dict, indent=2)
    return template.replace("[[html]]", html_str.strip()).replace("[[json-schema]]", schema_str)

def build_messages(html_path: str, schema_path: str, prompt_template_path: str = "prompt.txt"):
    """Build LLM-compatible message list using HTML + schema + text template."""
    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    prompt_template = load_prompt_template(prompt_template_path)
    user_prompt = render_prompt(html_content, schema, prompt_template)

    messages = [
        {
            "role": "system",
            "content": "You are a JSON converter. Only return valid JSON that matches the provided schema."
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]
    return messages
