# HTML Post-Processing Conventions

This document outlines the conventions used by the HTML post-processing script (`clean_html.py`) to structure and label content for downstream JSON conversion. These conventions ensure consistent and LLM-readable HTML formatting.

## 1. Sections

* Section headers such as `Section1000 - Study Intro Text` are wrapped in a `<div class="section" id="section-1000">` block.
* The section ID is auto-generated from the numeric code.
* Detection is based on the regex: `Section\s+(\d{3,4})\s*[-–—]?\s*(.*)`

## 2. Questions

* Each question is wrapped in a top-level div of the form:
```html
<div class="Q320_Intro" id="SCREENER">
  <div class="label">...</div>
  <div class="content">...</div>
</div>
```
* Detection is driven by HTML line markers, not by content patterns:
  A question begins immediately after a line of the form:
```html
<p lang="en-US" class="western" style="line-height:100%; margin-bottom:0in">
```
* The first non-empty paragraph following this line is the question header.
* If it contains a code and a type in brackets (e.g. `Q320_Intro [SCREENER]`), the class and ID are extracted accordingly.
* If there are no brackets, the type defaults to CHOICE.
* The question label block continues until a line containing only `===`.
* The question content block continues until the next HTML line of the same form (`<p lang=...>`) marking the end.

## 3. Tables

* Tables are labeled based on the paragraph that directly precedes them, matching labels such as:
  * VARIABLES TABLE
  * COLUMNS TABLE
* If no match is found, the table is tagged:
```html
[TABLE LABEL: OTHER TABLE]
```

## 4. Table Cell Compression

* Redundant wrapping like `<td><p><b>Text</b></p></td>` is flattened to:
```html
<td><b>Text</b></td>
```
* Multiple `<p>` elements inside a `<td>` are merged into a single string.

## 5. Prefix Stripping in Table Variables

* For any first-column entry like `Q305_1`, the prefix is removed:
```html
Q305_1 → 1
```

## 6. Style and Attribute Cleanup

* Preserved styles: only `style="color"` remains.
* Removed attributes:
  * `width`
  * `align`
  * `cellpadding`
  * `cellspacing`
  * `valign`
  * `height`
  * etc.
* Removed common noise:
  * `lang="en-US"`
  * `class="western"`

## 7. Extra Content / Programmer Notes

* Programmer-facing notes (e.g., `Programmer: Range0–100`) are preserved.
* These are included under the corresponding question block as part of the `.content` section or treated separately as EXTRA in JSON.

## 8. Miscellaneous Content

* All non-question, non-section, non-table content is grouped under:
```html
<div class="misc">...</div>
```
These conventions are applied in `HTMLCleaner.clean()` and enforced primarily in `wrap_questions()`, `wrap_sections()`, and related helpers.
They ensure consistent HTML structure for downstream question-answer extraction and JSON schema generation.