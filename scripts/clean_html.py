import os
from bs4 import BeautifulSoup, Tag
import re

ALLOWED_STYLES = {"color"}
STRIP_ATTRS = {"width", "align", "size", "cellpadding", "cellspacing", "valign", "height"}


class HTMLCleaner:
    def __init__(self, input_path, output_path):
        self.input_path = input_path
        self.output_path = output_path
        self.soup = None

    def load_html(self):
        with open(self.input_path, "r", encoding="utf-8") as f:
            self.soup = BeautifulSoup(f, "html.parser")

    def save_html(self):
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(self.soup.prettify())

    def clean_styles_and_attrs(self):
        for tag in self.soup.find_all(True):
            if tag.has_attr("style"):
                styles = []
                for item in tag["style"].split(";"):
                    if ":" not in item:
                        continue
                    key, value = item.split(":", 1)
                    if key.strip().lower() in ALLOWED_STYLES:
                        styles.append(f"{key.strip()}: {value.strip()}")
                if styles:
                    tag["style"] = "; ".join(styles)
                else:
                    del tag["style"]
            for attr in STRIP_ATTRS:
                tag.attrs.pop(attr, None)

    def unwrap_fonts(self):
        for font in self.soup.find_all("font"):
            font.unwrap()

    def remove_empty_paragraphs(self):
        for p in self.soup.find_all("p"):
            if not p.get_text(strip=True):
                p.decompose()

    def wrap_sections(self):
        section_pattern = re.compile(r"Section\s+(\d{3,4})\s*[-–—]?\s*(.*)", re.IGNORECASE)
        body = self.soup.body
        if not body:
            return

        elements = list(body.children)
        i = 0
        while i < len(elements):
            el = elements[i]
            if not isinstance(el, Tag):
                i += 1
                continue

            match = section_pattern.match(el.get_text(strip=True))
            if el.name in {"h1", "h2", "p"} and match:
                section_code = match.group(1)
                section_label = match.group(2).strip()
                section_id = f"section-{section_code.lower()}"
                wrapper = self.soup.new_tag("div", attrs={"id": section_id, "class": "section"})

                print(f"→ Wrapping section {section_code}: {section_label}")
                el.insert_before(wrapper)
                wrapper.append(el.extract())

                i += 1
                elements = list(body.children)
            else:
                i += 1

    def mark_tables(self):
        table_labels = {"VARIABLES TABLE", "COLUMNS TABLE"}
        last_label = None
        for p in self.soup.find_all("p"):
            bold_text = p.get_text(strip=True).upper()
            if bold_text in table_labels:
                last_label = bold_text
                p.decompose()
            elif p.find_next_sibling() and p.find_next_sibling().name == "table":
                label = last_label or "OTHER TABLE"
                label_tag = self.soup.new_tag("p")
                label_tag.string = f"[TABLE LABEL: {label}]"
                p.insert_before(label_tag)
                last_label = None

    def strip_table_prefixes(self):
        for table in self.soup.find_all("table"):
            for row in table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) > 0:
                    cell_text = cells[0].get_text(strip=True)
                    match = re.match(r"Q\d{3}_(\d+)", cell_text)
                    if match:
                        cells[0].string = match.group(1)

    def remove_language_and_class_attrs(self):
        for tag in self.soup.find_all(True):
            if tag.get("lang") == "en-US":
                del tag["lang"]
            if tag.get("class") == ["western"]:
                del tag["class"]

    def wrap_questions(self):
        question_pattern = re.compile(r"(?P<code>\w+)\s*\[(?P<type>\w+)]\s*:")
        body = self.soup.body
        if not body:
            return
    
        elements = list(body.children)
        i = 0
        while i < len(elements):
            el = elements[i]
            if not isinstance(el, Tag):
                i += 1
                continue

            match = question_pattern.search(el.get_text())
            if match:
                code = match.group("code")
                qtype = match.group("type")
                print(f"→ Wrapping question block with code={code} and type={qtype}")
                wrapper = self.soup.new_tag("div", attrs={"class": "question", "data-code": code, "data-type": qtype})
                el.insert_before(wrapper)
                wrapper.append(el.extract())

                j = i
                while j < len(elements) - 1:
                    next_el = elements[j + 1]
                    if isinstance(next_el, Tag) and next_el.get_text(strip=True) == "===":
                        wrapper.append(next_el.extract())
                        break
                    wrapper.append(next_el.extract())
                    j += 1
                
                elements = list(body.children)
                i = j + 1
            else:
                if not any(parent.name == 'div' and 'question' in parent.get('class', []) for parent in el.parents):
                    misc_wrapper = self.soup.new_tag("div", attrs={"class": "misc"})
                    el.insert_before(misc_wrapper)
                    misc_wrapper.append(el.extract())
                    elements = list(body.children)
                i += 1
    
    def compress_table_cells(self):
        for table in self.soup.find_all("table"):
            for td in table.find_all("td"):
                if len(td.contents) == 1 and isinstance(td.contents[0], Tag) and td.contents[0].name == "p":
                    p = td.contents[0]
                    if len(p.contents) == 1 and isinstance(p.contents[0], Tag) and p.contents[0].name == "b":
                        td.clear()
                        td.append(p.contents[0])
                    elif len(p.contents) == 1 and isinstance(p.contents[0], str):
                        td.string = p.contents[0]
                    else:
                        td.clear()
                        for child in p.contents:
                            td.append(child)
                elif all(isinstance(child, Tag) and child.name == "p" for child in td.contents):
                    flat_text = " ".join(p.get_text(strip=True) for p in td.find_all("p"))
                    td.clear()
                    td.string = flat_text

    def clean(self):
        self.load_html()
        self.clean_styles_and_attrs()
        self.unwrap_fonts()
        self.remove_empty_paragraphs()
        self.wrap_sections()
        self.mark_tables()
        self.strip_table_prefixes()
        self.wrap_questions()
        self.compress_table_cells()
        self.remove_language_and_class_attrs()
        self.save_html()

def batch_clean_html(folder):
    for name in os.listdir(folder):
        if name.endswith(".html") and not name.endswith("_cleaned.html"):
            in_path = os.path.join(folder, name)
            out_path = os.path.join(folder, name.replace(".html", "_cleaned.html"))
            print(f"\n--- Starting: {name} ---")
            try:
                cleaner = HTMLCleaner(in_path, out_path)
                cleaner.clean()
                print(f"✔ Finished: {name}")
            except Exception as e:
                print(f"✖ Error in {name}: {str(e)}")
        else:
            print(f"(Skipping file: {name})")


if __name__ == "__main__":
    batch_clean_html("/home/jliu/docx-to-html/data/html_output")