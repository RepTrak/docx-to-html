# docx-to-html
Converting .docx to .html

Exploring tools like BeautifulSoup or docx-parser-converter, may also attempt to convert from .docx to .pdf to .html, or .docx to .xml to .html.

Running Python 3.10.0

The class using docx_parser_converter is currently blocked and unable to correctly convert from .docx to .html

The class using Beautiful Soup is currently working and able to produce .html files. However, it is too lossy to be feasible (output .html file does not retain any text formatting or hierarchy). Will attempt to rewrite the script to make a smarter converter.

The Pandoc and Mammoth methods look more promising right now, they are able to maintain a decent amount of text hierarchy and table structures.

The PyPI pandoc package is just a wrapper, and the Pandoc CLI must be separately installed in order for the class to work.

To install Pandoc 3.1.13:

```bash
cd /usr/local/bin
curl -LO https://github.com/jgm/pandoc/releases/download/3.1.13/pandoc-3.1.13-linux-amd64.tar.gz
tar -xzf pandoc-3.1.13-linux-amd64.tar.gz
cp -r pandoc-3.1.13/bin/* /usr/local/bin/
rm -rf pandoc-3.1.13*
```
verify with pandoc --version