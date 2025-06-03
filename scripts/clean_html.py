import os
from bs4 import BeautifulSoup
import re

def clean_html(filepath_in: str, filepath_out: str):
    with open(filepath_in, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    for header_row in soup.select("tr.header"):
        header_row.name = "tr"
        header_row.attrs.pop("class", None)
        for th in header_row.find_all("th"):
            th.name = "td"

    for tr in soup.select("tr"):
        tr.attrs.pop("class", None)

    question_pattern = re.compile(r"^(Q\d{3}(\/\d+)?):", re.IGNORECASE)
    all_elements = soup.select("section > *")
    i = 0
    while i < len(all_elements):
        el = all_elements[i]
        match = el.get_text(strip=True)
        qmatch = question_pattern.match(match if match else "")
        if qmatch:
            qcode = qmatch.group(1)
            wrapper = soup.new_tag("div", attrs={"class": "question", "data-code": qcode})
            start_el = all_elements[i]
            parent = start_el.parent
            insert_index = list(parent.children).index(start_el)

            # First insert the empty wrapper at the correct position
            parent.insert(insert_index, wrapper)
            
            # Now move elements into the wrapper
            while i < len(all_elements):
                next_el = all_elements[i]
                # Need to get the element again since the DOM has changed
                current_el = parent.contents[insert_index + 1] if (insert_index + 1) < len(parent.contents) else None
                if current_el:
                    wrapper.append(current_el.extract())
                
                # Check if we should stop
                if next_el.name == "p" and "RESPONDENT MUST" in next_el.get_text():
                    break
                if next_el.name == "table":
                    peek = all_elements[i + 1] if i + 1 < len(all_elements) else None
                    if not peek or peek.name not in {"table", "p"}:
                        break
                i += 1
        else:
            i += 1

    with open(filepath_out, "w", encoding="utf-8") as f:
        f.write(str(soup.prettify()))

    print(f"Cleaned HTML written to {filepath_out}")

if __name__ == "__main__":
    folder = "../data/html_output"
    for name in os.listdir(folder):
        if name.endswith("_pandoc.html"):
            input_path = os.path.join(folder, name)
            output_path = input_path.replace("_pandoc.html", "_cleaned.html")
            clean_html(input_path, output_path)