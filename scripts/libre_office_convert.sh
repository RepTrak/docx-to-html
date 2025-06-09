#!/bin/bash

INPUT_DIR="/home/jliu/docx-to-html/data/docx_input"
OUTPUT_DIR="/home/jliu/docx-to-html/data/html_output"
IMAGE="jagregory/libreoffice"

mkdir -p "$OUTPUT_DIR"

for docx_file in "$INPUT_DIR"/*.docx; do
  if [[ -f "$docx_file" ]]; then
    filename=$(basename "$docx_file")
    echo "→ Converting: $filename"

    docker run --rm \
      -v "$INPUT_DIR":/data \
      -v "$OUTPUT_DIR":/out \
      "$IMAGE" \
      --headless --convert-to html:"HTML (StarWriter)" --outdir /out "/data/$filename"
  fi
done

echo "All conversions complete. Output saved to $OUTPUT_DIR"
