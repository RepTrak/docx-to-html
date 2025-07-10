import os

# Makes sure that every filename exists in directory (sanity check)
input_folder = "/home/jliu/docx-to-html/data/html_chunks_cleaned"
filenames = sorted(os.listdir(input_folder))
sanitized_filenames = []

for filename in filenames:
    if filename.endswith(".html"):
        full_path = os.path.join(input_folder, filename)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            sanitized_filenames.append((filename, "OK"))
        except Exception as e:
            sanitized_filenames.append((filename, str(e)))

import pandas as pd


df = pd.DataFrame(sanitized_filenames, columns=["filename", "status"])
print(df.to_string())