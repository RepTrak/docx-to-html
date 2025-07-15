from bs4 import BeautifulSoup
import os
import difflib
import re

def extract_body_html(path):
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    body = soup.body
    return body.encode_contents().decode("utf-8").strip() if body else ""

def analyze_differences(original, reconstructed):
    matcher = difflib.SequenceMatcher(None, original, reconstructed)
    whitespace_chars = 0
    non_whitespace_chars = 0
    total_diff_chars = 0
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != "equal":
            diff_text = original[i1:i2]
            ws_chars = sum(1 for c in diff_text if c.isspace())
            non_ws_chars = len(diff_text) - ws_chars
            
            whitespace_chars += ws_chars
            non_whitespace_chars += non_ws_chars
            total_diff_chars += len(diff_text)
    
    return {
        "total_diff": total_diff_chars,
        "whitespace_chars": whitespace_chars,
        "non_whitespace_chars": non_whitespace_chars,
        "whitespace_percent": (whitespace_chars / total_diff_chars * 100) if total_diff_chars else 0
    }

def debug_html_diff(original, reconstructed, window_size=300):
    print("\nScanning for truly missing content chunks...")

    missing_sections = []
    i = 0
    while i < len(original):
        snippet = original[i:i + window_size]
        if snippet not in reconstructed:
            start = max(0, i - 100)
            end = min(len(original), i + window_size + 100)
            context_snippet = original[start:end]
            if not any(context_snippet in s for s in missing_sections):
                missing_sections.append(context_snippet)
                print(f"\nMissing snippet {len(missing_sections)} ({len(context_snippet)} chars):")
                print(repr(context_snippet[:500]))
            i += window_size
        else:
            i += window_size // 2

    print(f"\nFound {len(missing_sections)} missing regions not found anywhere in reconstructed HTML.")

def compute_chunk_offsets(chunks_dir):
    print("\nChunk file offsets:")
    total = 0
    files = sorted(os.listdir(chunks_dir))
    for f in files:
        path = os.path.join(chunks_dir, f)
        size = os.path.getsize(path)
        print(f"  - {f:40} starts at {total:7} chars")
        total += size

def save_reconstructed_html(reconstructed_body, output_path):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    html_wrapper = f"<html><body>\n{reconstructed_body}\n</body></html>"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_wrapper)
    print(f"\n📝 Reconstructed HTML saved to: {output_path}")

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
    for file in chunk_files:
        chunk_html = extract_body_html(file)
        reconstructed_body += chunk_html

    reconstructed_len = len(reconstructed_body)
    print(f"Reconstructed body length: {reconstructed_len} characters")

    # Save reconstructed output
    save_reconstructed_html(
        reconstructed_body,
        "/home/jliu/docx-to-html/data/html_output/reconstructed.html"
    )

    # Analyze diff
    diff_stats = analyze_differences(original_body, reconstructed_body)
    
    if reconstructed_body == original_body:
        print("\n✔ Perfect match - all chunks combine to exactly reconstruct the original")
    else:
        print(f"\nMismatch detected ({diff_stats['total_diff']} characters differ)")
        print(f"  - Whitespace differences: {diff_stats['whitespace_chars']} chars ({diff_stats['whitespace_percent']:.1f}%)")
        print(f"  - Non-whitespace differences: {diff_stats['non_whitespace_chars']} chars")
        
        if diff_stats['non_whitespace_chars'] > 0:
            print("\n⚠ WARNING: Non-whitespace differences detected (potential content loss)")
            debug_html_diff(original_body, reconstructed_body)
        else:
            print("\nNote: Differences are only whitespace (likely formatting changes)")
        
        compute_chunk_offsets(chunk_dir)

if __name__ == "__main__":
    validate_chunks(
        original_path="/home/jliu/docx-to-html/data/html_output/svb_qnr_-_main_-_english__february_2024_for_ingestion.html",
        chunk_dir="/home/jliu/docx-to-html/data/html_chunks_precleaned"
    )
