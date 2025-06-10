import os
from typing import List
from abc import ABC

class Settings(ABC):
    docx_input_folder: str = "/home/jliu/docx-to-html/data/docx_input"
    docx_input_names: list = ["svb_qnr_-_main_-_english__february_2024_for_ingestion.docx"]
    html_output_folder: str = "/home/jliu/docx-to-html/data/html_output"

settings = Settings()