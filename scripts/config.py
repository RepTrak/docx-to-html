import os
from typing import List

from pydantic import BaseSettings

class Settings(BaseSettings):
    docx_allstate_path: str = "/home/jliu/docx-to-html/data/"
    docx_input_names: list = ["Allstate-Customers-QNR_2024_Q3 CLEAN.docx", "_CRT QNR - MAIN - ENGLISH__FEBRUARY_2025_v6_03-Feb-2025.docx"]
    html_output_folder: str = "/home/jliu/docx-to-html/data/html_output"

settings = Settings()