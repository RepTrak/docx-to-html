const fs = require('fs');
const path = require('path');
const TurndownService = require('turndown');

// Input and output directories
const inputDir = '/home/jliu/docx-to-html/data/html_chunks_cleaned';
const outputDir = '/home/jliu/docx-to-html/data/markdown_chunks';

// Ensure output directory exists
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Initialize Turndown service
const turndownService = new TurndownService();

// Read all files in input directory
fs.readdirSync(inputDir).forEach((file) => {
  // Only process _cleaned.html files
  if (file.endsWith('_cleaned.html')) {
    const inputPath = path.join(inputDir, file);
    const html = fs.readFileSync(inputPath, 'utf8');

    // Convert HTML to Markdown
    const markdown = turndownService.turndown(html);

    // Remove "_cleaned" and change extension to .md
    const outputFile = file.replace('_cleaned.html', '.md');
    const outputPath = path.join(outputDir, outputFile);

    fs.writeFileSync(outputPath, markdown, 'utf8');
    console.log(`Converted ${file} → ${outputFile}`);
  }
});
