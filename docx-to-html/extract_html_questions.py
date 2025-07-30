from bs4 import BeautifulSoup, Tag
import os
import re

def is_question_start(tag):
    """Identify if a <p> tag is the start of a question."""
    if tag.name != "p":
        return False
    font = tag.find("font", attrs={"color": "#0070c0"})
    bold = tag.find("b")
    text = tag.get_text(strip=True)
    return bool(font and bold and ":" in text and len(text) > 4)

def extract_questions_from_section(section_path):
    """Given a section HTML file, extract question chunks from it."""
    with open(section_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    body = soup.body
    if not body:
        return []

    elements = list(body.children)
    question_chunks = []
    current_chunk = []
    in_question = False
    question_idx = 0

    for el in elements:
        if is_question_start(el):
            if current_chunk:
                question_chunks.append((f"question_{question_idx}", list(current_chunk)))
                question_idx += 1
                current_chunk = []
            in_question = True
        if in_question:
            current_chunk.append(el)

    if current_chunk:
        question_chunks.append((f"question_{question_idx}", list(current_chunk)))

    return question_chunks

def extract_questions_from_all_sections(sections_dir, questions_dir):
    os.makedirs(questions_dir, exist_ok=True)

    html_files = sorted(f for f in os.listdir(sections_dir) if f.endswith(".html"))
    total_questions = 0
    for section_file in html_files:
        section_path = os.path.join(sections_dir, section_file)
        section_base = os.path.splitext(section_file)[0]

        questions = extract_questions_from_section(section_path)

        for i, (label, chunk) in enumerate(questions):
            chunk_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
            for el in chunk:
                chunk_soup.body.append(el)
            filename = f"{section_base}__{i:03d}_{label}.html"
            filepath = os.path.join(questions_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(chunk_soup.decode())

        total_questions += len(questions)

    print(f"✔ Extracted {total_questions} total questions into {questions_dir}")

sections_dir = "/home/jliu/docx-to-html/data/html_sections"
questions_dir = "/home/jliu/docx-to-html/data/html_questions"
extract_questions_from_all_sections(sections_dir, questions_dir)
