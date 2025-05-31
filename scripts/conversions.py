import os
import io
from abc import ABC, abstractmethod
from config import settings
import subprocess
import mammoth

from docx_parser_converter.docx_to_html.docx_to_html_converter import DocxToHtmlConverter
from docx_parser_converter.docx_to_txt.docx_to_txt_converter import DocxToTxtConverter
from docx_parser_converter.docx_parsers.utils import read_binary_from_file_path

import zipfile
from bs4 import BeautifulSoup
from lxml import etree
from config import settings

WORD_NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

class Converter(ABC):
    @abstractmethod
    def convert(self, input_path: str, output_path: str) -> None:
        pass

    @property
    def suffix(self) -> str:
        """Default suffix derived from class name (e.x. '_bs4', '_pandoc', etc.)"""
        name = self.__class__.__name__.replace("HTMLConverter", "").replace("PlainConverter", "")
        return f"_{name.lower()}"


class DocxParserHTMLConverter(Converter):
    def convert(self, input_path: str, output_path: str):
        docx_file_content = read_binary_from_file_path(input_path)
        try:
            converter = DocxToHtmlConverter(docx_file_content, use_default_values=True)
            html_output = converter.convert_to_html()
        except AttributeError as e:
            if "'NoneType' object has no attribute 'instances'" in str(e):
                print(f"Warning: numbering_schema is None in {input_path}, skipping conversion.")
                # sometimes word docs have faulty numbering.xml schemas that throw off this particular library
                return 
            else:
                raise e
        converter.save_html_to_file(html_output, output_path)

class DocxParserPlainConverter(Converter):
    def convert(self, input_path: str, output_path: str):
        docx_file_content = read_binary_from_file_path(input_path)
        try:
            converter = DocxToTxtConverter(docx_file_content, use_default_values=True)
            txt_output = converter.convert_to_txt()
        except AttributeError as e:
            if "'NoneType' object has no attribute 'instances'" in str(e):
                print(f"Warning: numbering_schema is None in {input_path}, skipping plain text conversion.")
                return 
            else:
                raise e
        converter.save_txt_to_file(txt_output, output_path)

class BeautifulSoupHTMLConverter(Converter):
    def convert(self, input_path: str, output_path: str):
        root = self._extract_document_xml(input_path)
        soup = self._build_soup(root)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(soup.prettify())
        print(f"Saved HTML to {output_path}")

    def _extract_document_xml(self, docx_path: str) -> etree.Element:
        with open(docx_path, "rb") as f:
            docx_data = f.read()
        with zipfile.ZipFile(io.BytesIO(docx_data), "r") as z:
            with z.open("word/document.xml") as doc_xml:
                return etree.parse(doc_xml).getroot()

    def _get_text(self, paragraph) -> str:
        texts = [node.text for node in paragraph.xpath(".//w:t", namespaces=WORD_NS) if node.text]
        return "".join(texts).strip()

    def _build_soup(self, document_root: etree.Element) -> BeautifulSoup:
        soup = BeautifulSoup("<html><head><meta charset='utf-8'></head><body></body></html>", "lxml")
        body = soup.body
        for p in document_root.xpath(".//w:body/w:p", namespaces=WORD_NS):
            text = self._get_text(p)
            if text:
                p_tag = soup.new_tag("p")
                p_tag.string = text
                body.append(p_tag)
        return soup

class MammothHTMLConverter(Converter):
    def convert(self, input_path: str, output_path: str):
        with open(input_path, "rb") as docx_file:
            result = mammoth.convert_to_html(docx_file)
            html = result.value
            messages = result.messages
            if messages:
                print(f"Warnings from mammoth for {input_path}:", messages)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[Mammoth] Saved HTML to {output_path}")

class PandocHTMLConverter(Converter):
    def convert(self, input_path: str, output_path: str):
        try:
            subprocess.run(
                ["pandoc", "-f", "docx", "-t", "html", input_path, "-o", output_path],
                check=True
            )
            print(f"[Pandoc] Saved HTML to {output_path}")
        except subprocess.CalledProcessError as e:
            print(f"[Pandoc] Error converting {input_path}: {e}")

def run_converters(converters: list[Converter]):
    for converter in converters:
        print(f"\n=== Running {converter.__class__.__name__} ===")
        for name in settings.docx_input_names:
            input_path = os.path.join(settings.docx_allstate_path, name)
            base, _ = os.path.splitext(name)
            ext = "html" if "html" in converter.__class__.__name__.lower() else "txt"
            output_file = f"{base}{converter.suffix}.{ext}"
            output_path = os.path.join(settings.html_output_folder, output_file)
            print(f"input = {input_path}, output = {output_path}")
            converter.convert(input_path, output_path)

if __name__ == "__main__":
    converters = [
        # DocxParserHTMLConverter(),
        # DocxParserPlainConverter(),
        BeautifulSoupHTMLConverter(),
        MammothHTMLConverter(),
        PandocHTMLConverter()
    ]
    run_converters(converters)