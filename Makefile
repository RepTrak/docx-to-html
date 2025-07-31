.PHONY: build run clean help convert test split-html split-html-batch html-to-md html-to-md-batch html-to-md-mapping process-md process-md-batch validate-md

# Default variables
IMAGE_NAME := docx-to-html
CONTAINER_NAME := docx-converter
INPUT_DIR := $(PWD)/data/input
OUTPUT_DIR := $(PWD)/data/output

# Build the Docker image
build:
	@echo "Creating directories if they do not exist..."
	@mkdir -p $(INPUT_DIR) $(OUTPUT_DIR)
	@echo "Building Docker image: $(IMAGE_NAME)"
	docker build -t $(IMAGE_NAME) .

run: build
	docker run --rm -it \
		-v $(INPUT_DIR):/input \
		-v $(OUTPUT_DIR):/output \
		$(IMAGE_NAME) 

# Convert DOCX files to HTML
convert: build
	@echo "Converting DOCX files to HTML..."
	@if [ ! -d "$(INPUT_DIR)" ] || [ -z "$$(ls -A $(INPUT_DIR)/*.docx 2>/dev/null)" ]; then \
		echo "Error: No .docx files found in $(INPUT_DIR)"; \
		echo "Please place your .docx files in $(INPUT_DIR) before running conversion"; \
		exit 1; \
	fi
	docker run --rm \
		-v $(INPUT_DIR):/input \
		-v $(OUTPUT_DIR):/output \
		$(IMAGE_NAME) ./scripts/convert.sh

# Split HTML files into sections and questions
split-html:
	@echo "Splitting HTML files..."
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make split-html FILE=path/to/file.html [OUTPUT=path/to/output]"; \
		exit 1; \
	fi
	@if [ -n "$(OUTPUT)" ]; then \
		python3 scripts/split_html.py split-html "$(FILE)" --output-dir "$(OUTPUT)" ; \
	else \
		python3 scripts/split_html.py split-html "$(FILE)" ; \
	fi

# Split all HTML files in a directory
split-html-batch:
	@echo "Splitting HTML files in batch..."
	@if [ -z "$(DIR)" ]; then \
		echo "Usage: make split-html-batch DIR=path/to/directory [OUTPUT=path/to/output]"; \
		exit 1; \
	fi
	@if [ -n "$(OUTPUT)" ]; then \
		python3 scripts/split_html.py split-html-batch "$(DIR)" --output-dir "$(OUTPUT)" ; \
	else \
		python3 scripts/split_html.py split-html-batch "$(DIR)" ; \
	fi

# Convert HTML file to Markdown
html-to-md:
	@echo "Converting HTML to Markdown..."
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make html-to-md FILE=path/to/file.html [OUTPUT=path/to/output]"; \
		exit 1; \
	fi
	@if [ -n "$(OUTPUT)" ]; then \
		python3 scripts/convert_html_to_markdown.py convert-file "$(FILE)" --output-dir "$(OUTPUT)"; \
	else \
		python3 scripts/convert_html_to_markdown.py convert-file "$(FILE)" ; \
	fi

# Convert all HTML files in a directory to Markdown
html-to-md-batch:
	@echo "Converting HTML files to Markdown in batch..."
	@if [ -z "$(DIR)" ]; then \
		echo "Usage: make html-to-md-batch DIR=path/to/directory [OUTPUT=path/to/output]"; \
		exit 1; \
	fi
	@if [ -n "$(OUTPUT)" ]; then \
		python3 scripts/convert_html_to_markdown.py convert-batch "$(DIR)" --output-dir "$(OUTPUT)" ; \
	else \
		python3 scripts/convert_html_to_markdown.py convert-batch "$(DIR)" ; \
	fi

# Convert HTML files to Markdown using mapping file
html-to-md-mapping:
	@echo "Converting HTML to Markdown using mapping file..."
	@if [ -z "$(MAPPING)" ]; then \
		echo "Usage: make html-to-md-mapping MAPPING=path/to/sections_questions_mapping.json [OUTPUT=path/to/output]"; \
		exit 1; \
	fi
	@if [ -n "$(OUTPUT)" ]; then \
		python3 scripts/convert_html_to_markdown.py convert-from-mapping "$(MAPPING)" --output-dir "$(OUTPUT)" ; \
	else \
		python3 scripts/convert_html_to_markdown.py convert-from-mapping "$(MAPPING)" ; \
	fi

# Process markdown file in chunks to build survey schema
process-md:
	@echo "Processing markdown file in chunks..."
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make process-md FILE=path/to/file.md [OUTPUT=path/to/output] [CHUNK_SIZE=2000] [OVERLAP=200] [PROVIDERS='anthropic openai']"; \
		exit 1; \
	fi
	@CMD="python3 scripts/process_markdown_chunks.py process-file '$(FILE)'"; \
	if [ -n "$(OUTPUT)" ]; then \
		CMD="$$CMD --output-dir '$(OUTPUT)'"; \
	fi; \
	eval $$CMD

# Process all markdown files in a directory
process-md-batch:
	@echo "Processing markdown files in batch..."
	@if [ -z "$(DIR)" ]; then \
		echo "Usage: make process-md-batch DIR=path/to/directory [OUTPUT=path/to/output] [CHUNK_SIZE=2000] [OVERLAP=200] [PROVIDERS='anthropic openai']"; \
		exit 1; \
	fi
	@CMD="python3 scripts/process_markdown_chunks.py process-batch '$(DIR)'"; \
	if [ -n "$(OUTPUT)" ]; then \
		CMD="$$CMD --output-dir '$(OUTPUT)'"; \
	fi; \
	eval $$CMD

# Validate markdown file structure without full processing
validate-md:
	@echo "Validating markdown file structure..."
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make validate-md FILE=path/to/file.md [CHUNK_SIZE=2000] [OVERLAP=200] [SHOW_CHUNKS=1]"; \
		exit 1; \
	fi
	@CMD="python3 scripts/process_markdown_chunks.py validate '$(FILE)' --analyze-patterns --show-chunks"; \
	eval $$CMD

# Clean output directories
clean:
	@echo "Cleaning output directories..."
	@rm -rf $(OUTPUT_DIR)/*
	@echo "✓ Output directories cleaned"

help:
	@echo "DOCX to HTML Conversion Pipeline"
	@echo ""
	@echo "Available commands:"
	@echo "  build                    - Build Docker image"
	@echo "  run                      - Run interactive container"
	@echo "  convert                  - Convert DOCX files to HTML"
	@echo ""
	@echo "HTML Processing Commands:"
	@echo "  split-html              - Split HTML file into sections and questions"
	@echo "                           Usage: make split-html FILE=path/to/file.html [OUTPUT=path/to/output]"
	@echo "  split-html-batch        - Split all HTML files in directory"
	@echo "                           Usage: make split-html-batch DIR=path/to/directory [OUTPUT=path/to/output]"
	@echo ""
	@echo "HTML to Markdown Commands:"
	@echo "  html-to-md              - Convert HTML file to Markdown"
	@echo "                           Usage: make html-to-md FILE=path/to/file.html [OUTPUT=path/to/output]"
	@echo "  html-to-md-batch        - Convert all HTML files to Markdown"
	@echo "                           Usage: make html-to-md-batch DIR=path/to/directory [OUTPUT=path/to/output]"
	@echo "  html-to-md-mapping      - Convert HTML to Markdown using mapping file"
	@echo "                           Usage: make html-to-md-mapping MAPPING=path/to/mapping.json [OUTPUT=path/to/output]"
	@echo ""
	@echo "Markdown Processing Commands:"
	@echo "  process-md              - Process markdown file in chunks to build survey schema"
	@echo "                           Usage: make process-md FILE=path/to/file.md [OUTPUT=path/to/output]"
	@echo "                           Options: [CHUNK_SIZE=2000] [OVERLAP=200] [PROVIDERS='anthropic openai'] [VERBOSE=1]"
	@echo "  process-md-batch        - Process all markdown files in directory"
	@echo "                           Usage: make process-md-batch DIR=path/to/directory [OUTPUT=path/to/output]"
	@echo "                           Options: [CHUNK_SIZE=2000] [OVERLAP=200] [PROVIDERS='anthropic openai'] [VERBOSE=1]"
	@echo "  validate-md             - Validate markdown file structure without processing"
	@echo "                           Usage: make validate-md FILE=path/to/file.md [CHUNK_SIZE=2000] [OVERLAP=200] [SHOW_CHUNKS=1] [VERBOSE=1]"
	@echo ""
	@echo "Utility Commands:"
	@echo "  clean                   - Clean output directories"
	@echo "  help                    - Show this help message"
	@echo ""
	@echo "Environment Variables:"
	@echo "  INPUT_DIR              - Input directory (default: $(INPUT_DIR))"
	@echo "  OUTPUT_DIR             - Output directory (default: $(OUTPUT_DIR))"
	@echo ""
	@echo "Examples:"
	@echo "  make convert                                                    # Convert DOCX to HTML"
	@echo "  make split-html FILE=survey.html                              # Split HTML into sections"
	@echo "  make html-to-md FILE=survey.html OUTPUT=./markdown            # Convert HTML to Markdown"
	@echo "  make process-md FILE=survey.md OUTPUT=./json VERBOSE=1        # Process Markdown with LLM"
	@echo "  make validate-md FILE=survey.md SHOW_CHUNKS=1                 # Validate file structure"
