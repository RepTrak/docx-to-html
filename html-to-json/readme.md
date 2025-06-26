the jobs of each file in this folder:

## schema.json
- holds the target JSON schema
- used for validation and prompt injection

## prompt.txt
- contains the prompt instructions with [[html]] and [[json-schema]] placeholders to indicate where in the prompt those pieces will go

## json_prompt.py
- contains build_messages() which loads the prompt with the HTML content and desired JSON schema

## validate.py
- validates output.json by comparing it against schema.json

## send_to_anthropic.py
- calls build_messages() to generate the final prompt
- sends the result to Anthropic using model = "claude-3-haiku-20240307"
- parses and saves the output to output.py
- runs validation using validate.py


