# docx-to-html
Converting `.docx` files to structured `.html` for JSON transformation.

This project aims to preserve key hierarchy information from text such as:

- **Text hierarchy** (headings, bold/italic text)  
- **Tables with labeled structure**  
- **Question and response formatting**  
- **Style-based information** (such as text color used to infer question code vs. type)

---

## Step 1: Conversion

LibreOffice is used to convert `.docx` files to `.html`. This process is automated through a Docker-based Python wrapper that runs LibreOffice inside a container.

- All `.docx` files located in `/home/jliu/docx-to-html/data/docx_input` will be converted.
- The resulting `.html` files are saved to `/home/jliu/docx-to-html/data/html_output`.

An API wrapper for LibreOffice is currently in development for enhanced control over conversion formats.

> Requires: Docker installed and user added to the `docker` group.

Running Python 3.12.0

---

**Step 2: Post-processing**

The `clean_html.py` script post-processes the obtained `.html` file by removing extraneous formatting and using standardized conventions to structure the content:

- **Strip extraneous inline styles** (retaining only `color`)
- **Remove deprecated HTML attributes** and empty tags
- **Wrap each question** in a `<div class="question">` with `data-code` and `data-type` attributes
- **Tag unlabeled or out-of-place content** as `MISC`
- **Extract and label tables** as `VARIABLES TABLE`, `COLUMNS TABLE`, or `OTHER TABLE`
- **Normalize question variable names** in tables (e.g., `Q320_1` → `1`)
- **Preserve Programmer Notes** and associate them with the correct question as `EXTRA`

The result is a `.html` file that can be interpreted by an LLM to produce a valid JSON schema.

---

**Pandoc (Optional)**

Though not currently used in the pipeline, pandoc is a backup tool to convert .docx to .html. 

To manually install Pandoc 3.1.13:

```bash
cd /usr/local/bin
curl -LO https://github.com/jgm/pandoc/releases/download/3.1.13/pandoc-3.1.13-linux-amd64.tar.gz
tar -xzf pandoc-3.1.13-linux-amd64.tar.gz
cp -r pandoc-3.1.13/bin/* /usr/local/bin/
rm -rf pandoc-3.1.13*
```
verify with pandoc --version