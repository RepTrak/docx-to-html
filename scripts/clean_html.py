from bs4 import BeautifulSoup, Tag
import os
import re

class HTMLCleaner:
    ALLOWED_STYLES = {"color"}

    def __init__(self, filepath_in, filepath_out):
        self.filepath_in = filepath_in
        self.filepath_out = filepath_out
        with open(filepath_in, "r", encoding="utf-8") as f:
            self.soup = BeautifulSoup(f, "html.parser")

    def clean_styles(self):
        for tag in self.soup.find_all(True):
            if tag.has_attr("style"):
                cleaned_styles = []
                for item in tag["style"].split(";"):
                    if ":" not in item:
                        continue
                    key, value = item.split(":", 1)
                    key = key.strip().lower()
                    if key in self.ALLOWED_STYLES:
                        cleaned_styles.append(f"{key}: {value.strip()}")
                if cleaned_styles:
                    tag["style"] = "; ".join(cleaned_styles)
                else:
                    del tag["style"]

    def remove_unwanted_attributes(self):
        for tag in self.soup.find_all(True):
            for attr in ["width", "align", "size", "cellpadding", "cellspacing", "valign", "height"]:
                tag.attrs.pop(attr, None)

    def unwrap_fonts_preserve_color(self):
        for font in self.soup.find_all("font"):
            color = font.get("color")
            contents = font.contents
            if color:
                span = self.soup.new_tag("span", style=f"color: {color}")
                for content in contents:
                    span.append(content)
                font.replace_with(span)
            else:
                font.unwrap()

    def remove_empty_paragraphs(self):
        for p in self.soup.find_all("p"):
            if not p.get_text(strip=True):
                p.decompose()

    def wrap_question_blocks(self):
        body = self.soup.body
        if not body:
            return

        elements = list(body.children)
        i = 0
        question_pattern = re.compile(r"([A-Z0-9_]+)(?:\s*\[([A-Z0-9_]+)\])?:", re.IGNORECASE)

        while i < len(elements):
            el = elements[i]
            if not isinstance(el, Tag) or not el.get_text(strip=True):
                i += 1
                continue

            text = el.get_text(strip=True)
            match = question_pattern.match(text)
            if match:
                code = match.group(1)
                qtype = match.group(2) if match.group(2) else "CHOICE"

                wrapper = self.soup.new_tag("div", attrs={
                    "class": "question",
                    "data-code": code,
                    "data-type": qtype
                })

                el.insert_before(wrapper)

                moved_elements = 0
                while i < len(elements):
                    current_el = elements[i]
                    if not isinstance(current_el, Tag):
                        i += 1
                        continue

                    wrapper.append(current_el.extract())
                    moved_elements += 1

                    if "RESPONDENT MUST" in current_el.get_text():
                        break
                    if current_el.name == "table":
                        if i + 1 >= len(elements) or elements[i + 1].name not in {"table", "p"}:
                            break
                    i += 1

                if moved_elements == 0:
                    wrapper.decompose()
            else:
                i += 1

    def write(self):
        with open(self.filepath_out, "w", encoding="utf-8") as f:
            f.write(self.soup.prettify())
        print(f"Cleaned HTML written to {self.filepath_out}")

    def run_all(self):
        self.clean_styles()
        self.remove_unwanted_attributes()
        self.unwrap_fonts_preserve_color()
        self.remove_empty_paragraphs()
        self.wrap_question_blocks()
        self.write()

def batch_clean_html(folder_path):
    for name in os.listdir(folder_path):
        if name.endswith(".html") and not name.endswith("_cleaned.html"):
            input_path = os.path.join(folder_path, name)
            output_path = input_path.replace(".html", "_cleaned.html")
            cleaner = HTMLCleaner(input_path, output_path)
            cleaner.run_all()

batch_clean_html("/home/jliu/docx-to-html/data/html_output")
