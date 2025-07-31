#!/bin/bash

INPUT_DIR="/input"
OUTPUT_DIR="/output"

echo "Starting DOCX to HTML conversion..."
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"

# Check if input directory exists and has files
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory $INPUT_DIR does not exist"
    exit 1
fi

# Count DOCX files
docx_count=$(find "$INPUT_DIR" -name "*.docx" -type f | wc -l)
if [ "$docx_count" -eq 0 ]; then
    echo "No .docx files found in $INPUT_DIR"
    exit 0
fi

echo "Found $docx_count .docx file(s) to convert"

# Convert each DOCX file
for docx_file in "$INPUT_DIR"/*.docx; do
    if [[ -f "$docx_file" ]]; then
        filename=$(basename "$docx_file")
        echo "→ Converting: $filename"
        mkdir -p "$OUTPUT_DIR/$filename"
        
        libreoffice --headless --convert-to html:"HTML (StarWriter)" --outdir "$OUTPUT_DIR/$filename" "$docx_file" > /dev/null 2>&1
        # Check if the conversion was successful
        if [ $? -eq 0 ]; then
            echo "✓ Successfully converted: $filename"
        else
            echo "✗ Failed to convert: $filename"
        fi
        #show the output directory structure
        echo "Output saved to: $OUTPUT_DIR/$filename"
        
        if [ $? -eq 0 ]; then
            echo "✓ Successfully converted: $filename"
        else
            echo "✗ Failed to convert: $filename"
        fi
    fi
done

echo "All conversions complete. Output saved to $OUTPUT_DIR"
