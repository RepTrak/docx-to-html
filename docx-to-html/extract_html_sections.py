from bs4 import BeautifulSoup, Tag
import os
import re

def extract_sections(input_path, sections_dir):
    with open(input_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    os.makedirs(sections_dir, exist_ok=True)
    body = soup.body
    if not body:
        print("No <body> tag found in HTML.")
        return

    elements = list(body.children)

    section_chunks = []
    current_section = []
    section_title = None

    for el in elements:
        if isinstance(el, Tag) and el.name == "h1":
            font = el.find("font")
            text = font.get_text(strip=True) if font else el.get_text(strip=True)

            if section_title and current_section:
                section_chunks.append((section_title, list(current_section)))
                current_section.clear()

            section_title = text

        if section_title:
            current_section.append(el)

    if section_title and current_section:
        section_chunks.append((section_title, current_section))

    for i, (label, chunk) in enumerate(section_chunks):
        chunk_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        for el in chunk:
            chunk_soup.body.append(el)
        safe_label = re.sub(r'[^\w\-_.]', '_', label.strip()) or "section"
        filepath = os.path.join(sections_dir, f"{i:03d}_{safe_label}.html")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(chunk_soup.decode())

    print(f"✔ Extracted {len(section_chunks)} sections to {sections_dir}")

input_path = "/home/jliu/docx-to-html/data/svb_qnr_-_main_-_english__february_2024_for_ingestion.html"
questions_dir = "/home/jliu/docx-to-html/data/html_sections"
extract_sections(input_path, questions_dir)