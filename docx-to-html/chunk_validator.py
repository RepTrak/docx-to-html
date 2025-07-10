from bs4 import BeautifulSoup
import os
import difflib

def extract_body_html(path):
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    body = soup.body
    return body.encode_contents().decode("utf-8").strip() if body else ""

def debug_html_diff(original, reconstructed, context=200):
    print("Generating detailed diff...\n")

    matcher = difflib.SequenceMatcher(None, original, reconstructed)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            print(f"Change type: {tag}")
            print(f"Original [{i1}:{i2}] ({i2 - i1} chars):\n{original[i1:i2][:context]!r}\n")
            print(f"Reconstructed [{j1}:{j2}] ({j2 - j1} chars):\n{reconstructed[j1:j2][:context]!r}\n")
            break  # Remove this `break` if you want to show *all* differences

def compute_chunk_offsets(chunks_dir):
    print("\nChunk file offsets:")
    total = 0
    files = sorted(os.listdir(chunks_dir))
    for f in files:
        path = os.path.join(chunks_dir, f)
        size = os.path.getsize(path)
        print(f"  - {f:40} starts at {total:7} chars")
        total += size

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
        debug_html_diff(original_body, reconstructed_body)
        compute_chunk_offsets('/home/jliu/docx-to-html/data/html_chunks_precleaned')
        # for fname, length in chunk_lengths:
        #     print(f"  - {os.path.basename(fname)}: {length} chars")

        # diff = difflib.unified_diff(
        #     original_body.splitlines(),
        #     reconstructed_body.splitlines(),
        #     fromfile='original',
        #     tofile='reconstructed',
        #     lineterm=''
        # )
        # print("\nDiff (first 100 lines):")
        # for line in list(diff)[:100]:
        #     print(line)

if __name__ == "__main__":
    validate_chunks(
        original_path="/home/jliu/docx-to-html/data/html_output/svb_qnr_-_main_-_english__february_2024_for_ingestion.html",
        chunk_dir="/home/jliu/docx-to-html/data/html_chunks_precleaned"
    )
