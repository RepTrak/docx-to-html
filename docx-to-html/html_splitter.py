from bs4 import BeautifulSoup, Tag
import os
import re

def split_html_by_questions_fixed(input_path, output_dir):
    with open(input_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    os.makedirs(output_dir, exist_ok=True)
    body = soup.body
    if not body:
        print("No <body> tag found in HTML.")
        return

    elements = list(body.children)
    chunks = []

    def is_end_line(tag):
        return (
            isinstance(tag, Tag)
            and tag.name == "p"
            and tag.get("lang") == "en-US"
            and tag.get("class") == ["western"]
            and tag.get("style") == "line-height: 100%; margin-bottom: 0in"
        )

    preface_elements = []
    current_chunk = []
    current_code = None
    label_complete = False
    seen_question = False

    all_processed_ids = set()
    epilogue_elements = []

    for el in elements:
        if not isinstance(el, Tag):
            continue

        text = el.get_text(strip=True)
        type_match = re.search(r"\[(\w+)\]", text)

        if type_match and el.name == "p":
            if not seen_question:
                seen_question = True
                if preface_elements:
                    chunks.append(("preface", list(preface_elements)))
                    all_processed_ids.update(id(e) for e in preface_elements)
                    preface_elements.clear()
            if current_chunk and current_code:
                chunks.append((current_code, list(current_chunk)))
                all_processed_ids.update(id(e) for e in current_chunk)
            current_chunk = [el]
            current_code = text.split('[')[0].strip()
            label_complete = False
        elif not type_match and el.name == "p" and not seen_question:
            preface_elements.append(el)
        elif not type_match and el.name == "p" and not current_chunk:
            seen_question = True
            if preface_elements:
                chunks.append(("preface", list(preface_elements)))
                all_processed_ids.update(id(e) for e in preface_elements)
                preface_elements.clear()
            current_code = text.strip()
            current_chunk = [el]
            label_complete = False
        elif current_chunk:
            current_chunk.append(el)
            if not label_complete and text == "===":
                label_complete = True
            elif is_end_line(el):
                chunks.append((current_code, list(current_chunk)))
                all_processed_ids.update(id(e) for e in current_chunk)
                current_chunk = []
                current_code = None
                label_complete = False
        elif not seen_question:
            preface_elements.append(el)

    if current_chunk and current_code:
        chunks.append((current_code, list(current_chunk)))
        all_processed_ids.update(id(e) for e in current_chunk)
    elif preface_elements and not seen_question:
        chunks.append(("preface", list(preface_elements)))
        all_processed_ids.update(id(p) for p in preface_elements)

    epilogue_elements = [el for el in elements if id(el) not in all_processed_ids]
    if epilogue_elements:
        chunks.append(("epilogue", epilogue_elements))

    saved_files = []
    for i, (code, elements) in enumerate(chunks):
        chunk_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        for el in elements:
            chunk_soup.body.append(el)
        safe_code = code.replace('/', '_').replace('\\', '_').strip() or 'chunk'
        filename = f"{i:03d}_{safe_code}.html"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(chunk_soup))
        saved_files.append(filepath)

    return saved_files

# Run fixed version
input_path = "/home/jliu/docx-to-html/data/html_output/svb_qnr_-_main_-_english__february_2024_for_ingestion.html"
output_dir = "/home/jliu/docx-to-html/data/html_chunks_precleaned"
split_html_by_questions_fixed(input_path, output_dir)
