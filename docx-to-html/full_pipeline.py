import os
import subprocess
from pathlib import Path

class LibreOfficeDockerConverter:
    def __init__(self):
        self.input_dir = Path("/home/jliu/docx-to-html/data/docx_input")
        self.output_dir = Path("/home/jliu/docx-to-html/data/html_output")
        self.docker_image = "linuxserver/libreoffice"
        self.ensure_output_directory()

    def ensure_output_directory(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def convert_all(self):
        docx_files = list(self.input_dir.glob("*.docx"))
        if not docx_files:
            print("No .docx files found.")
            return

        for file_path in docx_files:
            print(f"→ Converting: {file_path.name}")
            self.convert_file(file_path)

        print(f"All conversions complete. Output saved to {self.output_dir}")

    def convert_file(self, file_path: Path):
        command = [
            "docker", "run", "--rm",
            "-v", f"{self.input_dir}:/input",
            "-v", f"{self.output_dir}:/output",
            self.docker_image,
            "libreoffice", "--headless",
            "--convert-to", 'html:"HTML (StarWriter)"',
            "--outdir", "/output",
            f"/input/{file_path.name}"
        ]

        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error converting {file_path.name}: {e}")

if __name__ == "__main__":
    converter = LibreOfficeDockerConverter()
    converter.convert_all()

    print("→ Running clean_html.py postprocessor...")
    try:
        subprocess.run(["python3.12", "clean_html.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during HTML cleanup: {e}")
