# need python 3.10+ to support the current version of docx-parser-converter, currently installing on local machine
# earlier versions of python don't support the pipe operation for type unions:
# def generate_html_body(doc_margins: DocMargins, elements: List[Paragraph | Table], numbering_schema: NumberingSchema) -> etree.Element:

from docx_parser_converter.docx_to_html.docx_to_html_converter import DocxToHtmlConverter
from docx_parser_converter.docx_to_txt.docx_to_txt_converter import DocxToTxtConverter
from docx_parser_converter.docx_parsers.utils import read_binary_from_file_path
from config import settings

def convert_file(input, output):
    docx_file_content = read_binary_from_file_path(input)
    converter = DocxToHtmlConverter(input, use_default_values=True)
    html_output = converter.convert_to_html()
    converter.save_html_to_file(html_output, output)

for name in settings.docx_input_names:
    input_path = os.path.join(settings.docx_allstate_path, name)
    output_path = os.path.join(settings.html_output_folder, name.replace(".docx", ".html"))
    print(f"input = {input_path}, output = {output_path}")
    convert_file(input_path, output_path)