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

## Step 1: Convert `.docx` to `.html`

This pipeline uses **LibreOffice running in Docker** to batch-convert all `.docx` files into `.html`.

- Input: `/home/jliu/docx-to-html/data/docx_input/*.docx`
- Output: `/home/jliu/docx-to-html/data/html_output/*.html`

```bash
# Run the conversion pipeline
./scripts/full_pipeline.py
```
Requirements: 
- Docker installed on your system
- Your user added to the docker group:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

## Step 2: Post-process HTML

The output HTML is cleaned and structured using `scripts/clean_html.py`:
```bash
python3 scripts/clean_html.py
```

This step:
- Removes extraneous inline styles and deprecated attributes
- Wraps each question into:
```html
<div class="Q320_Intro" id="SCREENER">
  <div class="label">...</div>
  <div class="content">...</div>
</div>
```

- Tags non-question content as:
```html
<div class="misc">...</div>
```

- Labels tables as VARIABLES TABLE, COLUMNS TABLE, or OTHER TABLE
- Normalizes table codes (e.g. Q320_1 → 1)
- Preserves programmer notes (PN:) under the corresponding question as EXTRA