# HTML Post-Processing Conventions

This document outlines the conventions used by the HTML post-processing script (`clean_html.py`) to structure and label content for downstream JSON conversion. These conventions ensure consistent and LLM-readable HTML formatting.

---

## 1. **Sections**

- Section headers such as `Section 1000 - Study Intro Text` are wrapped in a `<div class="section" id="section-1000">` block.
- The section ID is auto-generated from the numeric code.
- Detection is based on regex: `Section\s+(\d{3,4})\s*[-–—]?\s*(.*)`

---

## 2. **Questions**

- Questions are wrapped in `<div class="question" data-code="..." data-type="...">`.
- Detection is based on lines like `AGE_ORI [AGE_STANDARD]:` using the pattern `(?P<code>\w+)\s*\[(?P<type>\w+)]\s*:`
- All subsequent content is considered part of the question block until a `===` line is encountered.

---

## 3. **Tables**

- Tables are labeled based on the paragraph that precedes them, detecting keywords like:
  - `VARIABLES TABLE`
  - `COLUMNS TABLE`
- If no match is found, it is labeled as `[TABLE LABEL: OTHER TABLE]`.

---

## 4. **Table Cell Compression**

- Redundant nesting of `<p><b>...</b></p>` inside `<td>` is flattened.
- Consecutive `<p>` elements within a single `<td>` are merged into a single text block.

---

## 5. **Prefix Stripping in Table Variables**

- In tables, variables like `Q305_1` are stripped to `1` if they match the question code pattern.

---

## 6. **Style and Attribute Cleanup**

- Retains only `style="color"` for color-dependent parsing.
- Removes legacy attributes like `width`, `align`, `cellpadding`, etc.
- Removes `lang="en-US"` and `class="western"` from tags to reduce noise.

---

## 7. **Extra Content / Programmer Notes**

- Programmer-facing notes (e.g., "Programmer: Range 0–100") are not discarded.
- These remain within the corresponding question block for JSON transformation under `EXTRA`.

---

## 8. **Miscellaneous Content**

- Any content not matched as part of a question or section is wrapped in `<div class="misc">`.

---

These conventions are enforced in `HTMLCleaner.clean()` and support robust downstream parsing for question/answer extraction and schema validation.
