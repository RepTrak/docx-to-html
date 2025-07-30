# docx-to-html

Converting `.docx` files to structured `.html` using LibreOffice inside a Docker container. Running Python 3.12.0.

This project is designed to preserve key document structures needed for downstream JSON transformation, including:

- **Text hierarchy** (e.g. headings, bold/italic formatting)
- **Structured tables**
- **Question-label conventions**
- **Style-based cues** (e.g. color indicating codes vs. types)

The working test file is:  
`svb_qnr_-_main_-_english__february_2024_for_ingestion.docx`

See [docker-setup.md](docx-to-html/docker-setup.md) for full Docker installation instructions on CentOS Stream 10.  
See [conventions.md](docx-to-html/conventions.md) for encoding rules used in `.docx` formatting.

---

## Step 1: Setting up local folders/files

**Folders needed:**
- `data/docx_input`
  - Stores the original Word questionnaires
- `data/html_output`
  - Stores the converted .html result using LibreOffice
- `data/html_questions`
- `data/html_sections`
  - Holds the extracted sections and questions from the converted .html file in docx-to-html/data/html_output
- `data/json_chunks_from_html`
  - Holds the converted .json chunks using Claude-3.5 Haiku (should be repurposed to hold the converted HTML questions and HTML sections separately)
- `data/json_final`
  - Will contain the final .json output.

**Libraries needed:**
- Install all libraries in requirements-dev.txt
- Install Docker on root to use LibreOffice

**Files needed:**
- `.env` file storing the Anthropic API key as the environment variable `ANTHROPIC_API_KEY`
- `.gitignore` file excluding `data/` and `.env`

## Step 2: Navigating docx-to-html conversion
- `html_splitter` and `chunk_validator` (depreciated): The old method of chunking the .html form of svb and validating that the splitting was done correctly.
- `config.py `: Contains old environment variable names for the folders storing data. Can be depreciated or overhauled as folders will no longer point to my home folder.
- `conversions.py` (depreciated): The old methods of attempting to convert .docx to .html before LibreOffice was used.
- `libre_office_convert.sh`: Converts .docx files into .html using LibreOffice.
- `clean_html.py`: Takes all .html files within a specified folder and dumps cleaned versions into another specified folder. Uncleaned files with the name `{filename}.html` will correspond to their cleaned version, `{filename}_cleaned.html`. 
- `extract_html_questions.py` and `extract_html_sections.py` (**in use**): The current method for extracting questions and sections from the .html file. Requires an **uncleaned** .html file that still contains conventions (i.e., HTML lines to mark questions and sections).
- `full_pipeline.py`: Calls both `libre_office_convert.sh` and `clean_html.py` on an input and output folder. In order to obtain the uncleaned .html file used in the current extraction process, this should be called without `clean_html.py`.

## Step 3: Navigating html-to-json conversion
- `anthropic_diagnostic.py`: Simple test script that calls Claude-3.5 Haiku (or any other Anthropic model) and gets a response. Can be used to make sure your key is valid, servers aren't down, etc.
- `file_debugger.py`, `token_estimator.py`, `test.py`, `tokenizer_prompt.txt` (depreciated): Remnants of debugging that are not useful as corresponding fixes have been made.
- `html_prompt.txt`: The prompt containing instructions to Claude for converting each .html chunk into JSON.
- `questions.json`, `sections.json` (**in use**): The current modified schemas for converting questions specifically and section metadata specifically.
- `schema.json` (depreciated): The old plain Draft7 JSON schema used in .html to .json conversion.
- `html_prompt_builder.py`: Defines `build_messages`, the function that inserts the chosen JSON schema and HTML chunk into `html_prompt.txt` to be sent to Claude.
- `send_to_anthropic.py`: Calls `build_messages` and defines the required paths for building the message. Requires an input folder of all .html chunks and an output folder to hold returned .json chunks. File names are preserved.
- `validate.py`: Used to validate returned JSON against the Draft7 schema (Might be depreciated based on new schemas used).
- `json_combiner.py`: Combines all .json chunks in a specified folder and returns the final output in another specified folder.

## Additional notes (markdown conversion)
- For now, markdown conversion will not be used (.html yielded better results). In any case, `markdown_to_json/` is effectively a simplified copy of `html_to_json/`, just additionally using Turndown to perform the .html to .md conversion. 
