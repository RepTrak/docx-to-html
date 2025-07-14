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
    """Analyze differences between original and reconstructed content"""
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

def debug_html_diff(original, reconstructed, context=200):
    print("\nGenerating complete diff analysis...")
    matcher = difflib.SequenceMatcher(None, original, reconstructed)
    
    missing_sections = []
    current_missing = ""
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "delete":
            missing_text = original[i1:i2]
            current_missing += missing_text
            
            # If this is a substantial non-whitespace section
            if not missing_text.strip() and current_missing.strip():
                missing_sections.append(current_missing)
                current_missing = ""
    
    if current_missing.strip():
        missing_sections.append(current_missing)
    
    print(f"\nFound {len(missing_sections)} substantial missing sections:")
    for i, section in enumerate(missing_sections[:5]):  # Show first 5 for brevity
        print(f"\nMissing Section {i+1} ({len(section)} chars):")
        print(repr(section[:500]))  # Show first 500 chars

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
    
    for file in chunk_files:
        chunk_html = extract_body_html(file)
        reconstructed_body += chunk_html

    reconstructed_len = len(reconstructed_body)
    print(f"Reconstructed body length: {reconstructed_len} characters")
    
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