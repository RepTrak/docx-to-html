import json
from xml.etree import ElementTree as ET

def load_metaprompt(path="metaprompt.xml"):
    """Parse metaprompt.xml and extract prompt components."""
    tree = ET.parse(path)
    root = tree.getroot()
    
    purpose = root.findtext("purpose", default="").strip()
    instructions = [i.text.strip() for i in root.findall(".//instruction") if i.text]
    user_prompt_template = root.findtext("user-prompt", default="").strip()
    
    return purpose, instructions, user_prompt_template

def render_prompt(html_str: str, schema_dict: dict, template: str) -> str:
    """Substitute [[html]] and [[json-schema]] in the prompt template."""
    schema_str = json.dumps(schema_dict, indent=2)
    return template.replace("[[html]]", html_str.strip()).replace("[[json-schema]]", schema_str)

def build_messages(html_path: str, schema_path: str, metaprompt_path: str = "metaprompt.xml"):
    """Build LLM-compatible message list using HTML + schema + metaprompt.xml."""
    # Load inputs
    with open(html_path, encoding="utf-8") as f:
        html_content = f.read()
    with open(schema_path, encoding="utf-8") as f:
        schema = json.load(f)

    # Load template from metaprompt
    purpose, instructions, prompt_template = load_metaprompt(metaprompt_path)

    # Final prompt rendering
    user_prompt = render_prompt(html_content, schema, prompt_template)

    # Construct system + user message list
    messages = [
        {
            "role": "system",
            "content": f"{purpose}\n\nInstructions:\n" + "\n".join(f"- {instr}" for instr in instructions)
        },
        {
            "role": "user",
            "content": user_prompt
        }
    ]
    return messages
