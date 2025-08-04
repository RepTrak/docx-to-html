from bs4 import BeautifulSoup, Tag
import os
import re
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any


class HTMLProcessor:
    """Service for processing HTML files to extract sections and questions."""
    
    def __init__(self, input_file: str, output_dir: str):
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.sections_dir = self.output_dir / "sections"
        self.questions_dir = self.output_dir / "questions"
    
    def extract_sections(self) -> List[Tuple[str, List[Tag]]]:
        """Extract sections from HTML file based on h1 tags."""
        with open(self.input_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

        body = soup.body
        if not body:
            print("No <body> tag found in HTML.")
            return []

        elements = list(body.children)
        section_chunks = []
        current_section = []
        section_title = None

        for el in elements:
            if isinstance(el, Tag) and el.name == "h1":
                font = el.find("font")
                text = font.get_text(strip=True) if font else el.get_text(strip=True)

                if section_title and current_section:
                    section_chunks.append((section_title, list(current_section)))
                    current_section.clear()

                section_title = text

            if section_title:
                current_section.append(el)

        if section_title and current_section:
            section_chunks.append((section_title, current_section))

        return section_chunks
    
    def is_question_start(self, tag: Tag) -> bool:
        """Identify if a <p> tag is the start of a question."""
        if tag.name != "p":
            return False
        font = tag.find("font", attrs={"color": "#0070c0"})
        bold = tag.find("b")
        text = tag.get_text(strip=True)
        return bool(font and bold and ":" in text and len(text) > 4)
    
    def extract_questions_from_section(self, section_content: List[Tag]) -> List[Tuple[str, List[Tag]]]:
        """Extract question chunks from a section's content."""
        question_chunks = []
        current_chunk = []
        in_question = False
        question_idx = 0

        for el in section_content:
            if self.is_question_start(el):
                if current_chunk:
                    question_chunks.append((f"question_{question_idx}", list(current_chunk)))
                    question_idx += 1
                    current_chunk = []
                in_question = True
            if in_question:
                current_chunk.append(el)

        if current_chunk:
            question_chunks.append((f"question_{question_idx}", list(current_chunk)))

        return question_chunks
    
    def save_sections(self, sections: List[Tuple[str, List[Tag]]]) -> None:
        """Save sections to individual HTML files."""
        self.sections_dir.mkdir(parents=True, exist_ok=True)
        
        for i, (label, chunk) in enumerate(sections):
            chunk_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
            for el in chunk:
                if hasattr(el, 'name'):  # Only append Tag objects
                    chunk_soup.body.append(el)
            
            safe_label = re.sub(r'[^\w\-_.]', '_', label.strip()) or "section"
            filepath = self.sections_dir / f"{i:03d}_{safe_label}.html"
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(chunk_soup.prettify())
        
        print(f"✔ Extracted {len(sections)} sections to {self.sections_dir}")
    
    def save_questions(self, sections: List[Tuple[str, List[Tag]]]) -> None:
        """Save questions to individual HTML files."""
        self.questions_dir.mkdir(parents=True, exist_ok=True)
        
        total_questions = 0
        
        for section_idx, (section_label, section_content) in enumerate(sections):
            questions = self.extract_questions_from_section(section_content)
            
            safe_section_label = re.sub(r'[^\w\-_.]', '_', section_label.strip()) or "section"
            
            for q_idx, (q_label, q_chunk) in enumerate(questions):
                chunk_soup = BeautifulSoup("<html><body></body></html>", "html.parser")
                for el in q_chunk:
                    if hasattr(el, 'name'):  # Only append Tag objects
                        chunk_soup.body.append(el)
                
                filename = f"{section_idx:03d}_{safe_section_label}__{q_idx:03d}_{q_label}.html"
                filepath = self.questions_dir / filename
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(chunk_soup.prettify())
            
            total_questions += len(questions)
        
        print(f"✔ Extracted {total_questions} total questions to {self.questions_dir}")
    
    def generate_mapping(self, sections: List[Tuple[str, List[Tag]]]) -> Dict[str, Any]:
        """Generate a mapping structure of sections and their questions."""
        mapping = {
            "metadata": {
                "source_file": str(self.input_file),
                "total_sections": len(sections),
                "total_questions": 0
            },
            "sections": []
        }
        
        total_questions = 0
        
        for section_idx, (section_label, section_content) in enumerate(sections):
            questions = self.extract_questions_from_section(section_content)
            
            safe_section_label = re.sub(r'[^\w\-_.]', '_', section_label.strip()) or "section"
            section_filename = f"{section_idx:03d}_{safe_section_label}.html"
            
            section_data = {
                "index": section_idx,
                "title": section_label,
                "filename": section_filename,
                "question_count": len(questions),
                "questions": []
            }
            
            for q_idx, (q_label, q_chunk) in enumerate(questions):
                question_filename = f"{section_idx:03d}_{safe_section_label}__{q_idx:03d}_{q_label}.html"
                question_data = {
                    "index": q_idx,
                    "label": q_label,
                    "filename": question_filename
                }
                section_data["questions"].append(question_data)
            
            mapping["sections"].append(section_data)
            total_questions += len(questions)
        
        mapping["metadata"]["total_questions"] = total_questions
        return mapping
    
    def save_mapping(self, mapping: Dict[str, Any]) -> None:
        """Save the section-question mapping to a JSON file."""
        mapping_file = self.output_dir / "sections_questions_mapping.json"
        
        with open(mapping_file, "w", encoding="utf-8") as f:
            json.dump(mapping, f, indent=2, ensure_ascii=False)
        
        print(f"✔ Mapping saved to {mapping_file}")

    def process(self, extract_sections: bool = True, extract_questions: bool = True) -> None:
        """Process the HTML file to extract sections and/or questions."""
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")
        
        print(f"Processing HTML file: {self.input_file}")
        
        # Extract sections
        sections = self.extract_sections()
        
        if not sections:
            print("No sections found in the HTML file.")
            return
        
        # Save sections if requested
        if extract_sections:
            self.save_sections(sections)
        
        # Save questions if requested
        if extract_questions:
            self.save_questions(sections)
        
        # Generate and save mapping
        mapping = self.generate_mapping(sections)
        self.save_mapping(mapping)
        
        print(f"Processing complete. Output saved to: {self.output_dir}")
