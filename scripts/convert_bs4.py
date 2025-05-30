import os
import zipfile
import io
from bs4 import BeautifulSoup
from lxml import etree
from config import settings

def extract_document_xml(docx_path: str) -> etree.Element:
    with open(docx_path, "rb") as f:
        docx_data = f.read()
    with zipfile.ZipFile(io.BytesIO(docx_data), "r") as z:
        with z.open("word/document.xml") as doc_xml:
            return etree.parse(doc_xml).getroot()

def paragraph_text(paragraph) -> str:
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    texts = [node.text for node in paragraph.xpath(".//w:t", namespaces=ns) if node.text]
    return "".join(texts).strip()

def convert_docx_to_html(input_path: str, output_path: str):
    document_root = extract_document_xml(input_path)
    soup = BeautifulSoup("<html><head><meta charset='utf-8'></head><body></body></html>", "lxml")
    body = soup.body

    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    paragraphs = document_root.xpath(".//w:body/w:p", namespaces=ns)

    for p in paragraphs:
        text = paragraph_text(p)
        if text:
            p_tag = soup.new_tag("p")
            p_tag.string = text
            body.append(p_tag)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify()))

    print(f"Saved HTML to {output_path}")

for name in settings.docx_input_names:
    input_path = os.path.join(settings.docx_allstate_path, name)
    output_path = os.path.join(settings.html_output_folder, name.replace(".docx", ".html"))
    print(f"input = {input_path}, output = {output_path}")
    convert_docx_to_html(input_path, output_path)