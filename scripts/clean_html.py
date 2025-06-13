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
                    match = re.match(r"Q\d{1,4}_(\d+)", cell_text)
                    if match:
                        cells[0].string = match.group(1)

    def remove_language_and_class_attrs(self):
        for tag in self.soup.find_all(True):
            if tag.get("lang") == "en-US":
                del tag["lang"]
            if tag.get("class") == ["western"]:
                del tag["class"]

    def wrap_questions(self):
        question_pattern = re.compile(r"(?P<code>Q[\w\d_]+)")
        type_pattern = re.compile(r"\[(?P<type>\w+)]")
        body = self.soup.body
        if not body:
            return

        def is_end_line(tag):
            return (
                isinstance(tag, Tag)
                and tag.name == "p"
                and tag.get("lang") == "en-US"
                and tag.get("class") == ["western"]
                and tag.get("style") == "line-height: 100%; margin-bottom: 0in"
            )

        # First collect all question elements and their positions
        question_elements = []
        for i, el in enumerate(body.children):
            if not isinstance(el, Tag):
                continue
            text = el.get_text(strip=True)
            if (question_pattern.search(text) and 
                type_pattern.search(text) and 
                el.name == "p"):
                question_elements.append((i, el))

        # Create a list to hold processed questions
        processed_questions = []

        # Process each question block in forward order
        for start_idx, el in question_elements:
            # Get fresh elements list
            elements = list(body.children)
            if start_idx >= len(elements) or elements[start_idx] != el:
                continue  # Skip if already processed
                
            text = el.get_text(strip=True)
            question_match = question_pattern.search(text)
            type_match = type_pattern.search(text)
            
            if not (question_match and type_match):
                continue
                
            code = question_match.group("code")
            qtype = type_match.group("type")
            print(f"→ Wrapping question block with code={code}, type={qtype}")

            # Create wrapper
            wrapper = self.soup.new_tag("div", attrs={"class": f"question{code}", "id": qtype})
            label_div = self.soup.new_tag("div", attrs={"class": "label"})
            wrapper.append(label_div)

            # Add header line
            label_div.append(el.extract())

            # Collect label content until ===
            i = start_idx
            while i < len(elements):
                next_el = elements[i]
                if not isinstance(next_el, Tag):
                    i += 1
                    continue
                if next_el.get_text(strip=True) == "===":
                    label_div.append(next_el.extract())
                    break
                label_div.append(next_el.extract())
                i += 1

            # Collect content until end marker or next question start
            content_div = self.soup.new_tag("div", attrs={"class": "content"})
            next_question_pos = None
            # Find position of next question
            for q_pos, q_el in question_elements:
                if q_pos > start_idx:
                    next_question_pos = q_pos
                    break
                
            while i < len(elements):
                next_el = elements[i]
                if not isinstance(next_el, Tag):
                    i += 1
                    continue
                    
                # Check if we've reached the next question
                if next_question_pos and i >= next_question_pos:
                    break
                    
                # Check for end marker
                if is_end_line(next_el):
                    next_el.extract()
                    break
                    
                content_div.append(next_el.extract())
                i += 1

            if content_div.contents:
                wrapper.append(content_div)

            # Add to processed questions
            processed_questions.append(wrapper)

        # Clear body and add processed questions in order
        body.clear()
        for question in processed_questions:
            body.append(question)

        # Add any remaining non-question content to misc
        elements = list(body.children)
        misc_content = []
        for el in elements:
            if not isinstance(el, Tag):
                continue
                
            # Skip if already in a question div
            if any(parent.name == 'div' and 'question' in ''.join(parent.get('class', [])) 
                for parent in el.parents):
                continue
                
            misc_content.append(el.extract())

        if misc_content:
            misc_wrapper = self.soup.new_tag("div", attrs={"class": "misc"})
            body.append(misc_wrapper)
            for el in misc_content:
                misc_wrapper.append(el)


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