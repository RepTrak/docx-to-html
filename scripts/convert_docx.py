from docx_parser_converter.docx_to_html.docx_to_html_converter import DocxToHtmlConverter
from docx_parser_converter.docx_to_txt.docx_to_txt_converter import DocxToTxtConverter
from docx_parser_converter.docx_parsers.utils import read_binary_from_file_path
from config import settings
import os

def docx_to_html(input, output):
    docx_file_content = read_binary_from_file_path(input)
    converter = DocxToHtmlConverter(docx_file_content, use_default_values=True)
    html_output = converter.convert_to_html()
    converter.save_html_to_file(html_output, output)

def docx_to_plain(input, output):
    docx_file_content = read_binary_from_file_path(input)
    converter = DocxToTxtConverter(docx_file_content, use_default_values=True)
    txt_output = converter.convert_to_txt()
    converter.save_txt_to_file(txt_output, output)

for name in settings.docx_input_names:
    input_path = os.path.join(settings.docx_allstate_path, name)
    output_path = os.path.join(settings.html_output_folder, name.replace(".docx", ".html"))
    print(f"input = {input_path}, output = {output_path}")
    docx_to_plain(input_path, output_path)

    # currently blocked: when parsing the docx file, docx_parser_converter fails to correctly parse the .docx file's numbering.xml component.
    # can try local patch to library or clean up .docx file