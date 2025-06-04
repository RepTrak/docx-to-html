from bs4 import BeautifulSoup, Tag
import re
import os

class HTMLCleaner:
    ALLOWED_STYLES = {"color"}
    QUESTION_HEADER_RE = re.compile(
        r'^\s*(?P<code>[A-Z0-9_]+)(?:\s*\[(?P<type>[A-Z0-9_]+)\])?\s*[:：]?\s*', re.IGNORECASE
    )

    def __init__(self, filepath_in: str, filepath_out: str):
        self.filepath_in = filepath_in
        self.filepath_out = filepath_out
        self.soup = None

    def load_html(self):
        with open(self.filepath_in, "r", encoding="utf-8") as f:
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

    def remove_unwanted_attrs(self):
        for tag in self.soup.find_all(True):
            for attr in ["width", "align", "size", "cellpadding", "cellspacing", "valign", "height", "bgcolor", "lang"]:
                tag.attrs.pop(attr, None)

    def unwrap_fonts(self):
        for font in self.soup.find_all("font"):
            font.unwrap()

    def remove_empty_paragraphs(self):
        for p in self.soup.find_all("p"):
            if not p.get_text(strip=True):
                p.decompose()

    def wrap_questions(self):
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

            text = el.get_text(strip=True)
            match = self.QUESTION_HEADER_RE.match(text)
            if match:
                code = match.group("code")
                qtype = match.group("type") or "CHOICE"
                wrapper = self.soup.new_tag("div", attrs={"class": "question", "data-code": code, "data-type": qtype})
                el.insert_before(wrapper)

                while i < len(elements):
                    current_el = elements[i]
                    if not isinstance(current_el, Tag):
                        i += 1
                        continue

                    if current_el.name in {"h1", "h2"}:
                        break
                    text = current_el.get_text(strip=True)
                    if self.QUESTION_HEADER_RE.match(text):
                        break

                    wrapper.append(current_el.extract())
                    i += 1
            else:
                i += 1

    def save_html(self):
        with open(self.filepath_out, "w", encoding="utf-8") as f:
            f.write(self.soup.prettify())
        print(f"Cleaned HTML written to {self.filepath_out}")

    def clean(self):
        self.load_html()
        self.clean_styles()
        self.remove_unwanted_attrs()
        self.unwrap_fonts()
        self.remove_empty_paragraphs()
        self.wrap_questions()
        self.save_html()


def batch_clean_html(folder_path: str):
    for name in os.listdir(folder_path):
        if name.endswith(".html") and not name.endswith("_cleaned.html"):
            input_path = os.path.join(folder_path, name)
            output_path = input_path.replace(".html", "_cleaned.html")
            cleaner = HTMLCleaner(input_path, output_path)
            cleaner.clean()