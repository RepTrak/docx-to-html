import os
from bs4 import BeautifulSoup, Tag
import re

def split_questions_into_chunks(input_path, output_dir):
    with open(input_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    body = soup.body
    if not body:
        print("No <body> found in HTML.")
        return

    elements = list(body.children)

    def is_end_line(tag):
        return (
            isinstance(tag, Tag)
            and tag.name == "p"
            and tag.get("lang") == "en-US"
            and tag.get("class") == ["western"]
            and tag.get("style") == "line-height: 100%; margin-bottom: 0in"
        )

    def parse_questions(elements):
        questions = []
        current_question = None

        for el in elements:
            if not isinstance(el, Tag):
                continue

            text = el.get_text(strip=True)
            type_match = re.search(r"\[(\w+)]", text)

            if type_match and el.name == "p":
                if current_question:
                    questions.append(current_question)
                question_code = text.split('[')[0].strip()
                question_type = type_match.group(1)
                current_question = {
                    "code": question_code,
                    "type": question_type,
                    "label_elements": [el],
                    "content_elements": []
                }
            elif not type_match and el.name == "p" and not current_question:
                question_code = text.strip()
                current_question = {
                    "code": question_code,
                    "type": "CHOICE",
                    "label_elements": [el],
                    "content_elements": []
                }
            elif current_question:
                if text == "===":
                    current_question["label_elements"].append(el)
                elif is_end_line(el):
                    questions.append(current_question)
                    current_question = None
                else:
                    if current_question.get("label_elements") and not current_question.get("content_elements"):
                        current_question["label_elements"].append(el)
                    else:
                        current_question["content_elements"].append(el)

        if current_question:
            questions.append(current_question)
        return questions

    questions = parse_questions(elements)

    os.makedirs(output_dir, exist_ok=True)

    for i, q in enumerate(questions):
        new_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        new_body = new_soup.body

        for el in q["label_elements"] + q["content_elements"]:
            new_body.append(el)

        filename = f"question_chunk_{i+1:03d}_{q['code']}.html"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_soup.prettify())

    print(f"✔ Split into {len(questions)} chunks saved to {output_dir}")

split_questions_into_chunks(
    "/home/jliu/docx-to-html/data/html_output/svb_qnr_-_main_-_english__february_2024_for_ingestion_cleaned.html",
    "/home/jliu/docx-to-html/data/html_chunks"
)
