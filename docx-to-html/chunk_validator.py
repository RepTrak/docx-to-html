from bs4 import BeautifulSoup
import os
import difflib

def extract_body_html(path):
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    body = soup.body
    return body.encode_contents().decode("utf-8").strip() if body else ""

def validate_chunks(original_path, chunk_dir):
    print(f"Validating chunks from: {chunk_dir}")
    original_body = extract_body_html(original_path)
    original_len = len(original_body)
    print(f"Original body length: {original_len} characters")

    chunk_files = sorted([
        os.path.join(chunk_dir, name)
        for name in os.listdir(chunk_dir)
        if name.endswith(".html")
    ])

    reconstructed_body = ""
    chunk_lengths = []

    for file in chunk_files:
        chunk_html = extract_body_html(file)
        reconstructed_body += chunk_html
        chunk_lengths.append((file, len(chunk_html)))

    reconstructed_len = len(reconstructed_body)
    print(f"Reconstructed body length: {reconstructed_len} characters")

    if reconstructed_body.strip() == original_body:
        print("Chunks match the original HTML exactly.")
    else:
        print("Mismatch detected between original HTML and concatenated chunks.")
        print(f"Difference in length: {original_len - reconstructed_len} characters")
        print("Chunk breakdown:")
        for fname, length in chunk_lengths:
            print(f"  - {os.path.basename(fname)}: {length} chars")

        diff = difflib.unified_diff(
            original_body.splitlines(),
            reconstructed_body.splitlines(),
            fromfile='original',
            tofile='reconstructed',
            lineterm=''
        )
        print("\nDiff (first 100 lines):")
        for line in list(diff)[:100]:
            print(line)

if __name__ == "__main__":
    validate_chunks(
        original_path="/home/jliu/docx-to-html/data/html_output/svb_qnr_-_main_-_english__february_2024_for_ingestion.html",
        chunk_dir="/home/jliu/docx-to-html/data/html_chunks_precleaned"
    )
