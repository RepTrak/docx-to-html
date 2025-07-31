"""
Service for converting HTML/Markdown files to JSON using LLM with structured output.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional, Union, Any
from datetime import datetime

from ..llm import LLMClient
from ..models.questionnaire import FullSectionElementSchema, FullSectionResponseSchema

SYSTEM_PROMPT = """
**You are an expert algorithm that translate HTML or Markdown content into structured JSON format for a questionnaire.**

# Questionnaire Structure:
```
survey
- section 1
    - element 1
        - variable 1
        - variable n
        - grid column 1
        - grid column n
    - element 2
    - element n 
- section 2
- section n
```
Where an element can be a question, a break page, a termination or a text.
Question elements can have `Variables` and/or `Columns`.
By default all questions are `CHOICE` type, unless specified otherwise.
All sections/elements/variable/column have always a unique `code` and a `label`.
## Element Types:
- **CHOICE**: A question with multiple choice answers (radio buttons, checkboxes, etc.)
- **OPEN_END**: A question that allows free text input (text field, textarea, etc.)
- **BREAK_PAGE**: A page break element that separates sections
- **SCREENER**: A special type of question that screens texts to respondents, can based on their answers using placeholders

# Input Format
The provided content will follow a specific structure, and your task is to extract relevant sections and elements with them children.
**MUST KEEP CODES and LABELS EXACTLY AS THEY ARE**.
## Sections format
| section input | expected output |
| `# Section 1000 \- Study Intro Text` | `{"code": "section_1000", "label": "Study Intro Text", "notes": null}` |
| `# Section 100 – Familiarity (Screener)` | `{"code": "section_100", "label": "Familiarity (Screener)", "notes": null}` |
| `# CEO SECTION (Company1, Company2, Company3\)` | `{"code": "section_ceo", "label": "CEO SECTION", "notes": null}` |

## Elements format
| element input | expected output |
| `**cQCA\\_Language\\_CA** :\r\n\r\nWould you prefer to complete the survey in English or French?\r\n\r\nPr\u00E9f\u00E9rez\\-vous r\u00E9pondre \u00E0 ce questionnaire en\r\nAnglais ou en Fran\u00E7ais?\r\n\r\n* **SINGLE\r\n ANSWER**\r\n* **Prog:\r\n show default instruction text side\\-by\\-side in both English\r\n (code\\=1000\\) and French (Code\\=3000\\).**\r\n\r\n| **Value** **Code** | **Value** **Label** |\r\n| 1 | English\/Anglais |\r\n| 2 | French\/Fran\u00E7ais |` | `{"code": "cQCA_Language_CA", "label": "nWould you prefer to complete the survey in English or French?\r\n\r\nPr\u00E9f\u00E9rez\\-vous r\u00E9pondre \u00E0 ce questionnaire en\r\nAnglais ou en Fran\u00E7ais?\r\n\r\n", "type": "CHOICE", "position": 1, "variables": [{"code": "1", "label": "English/Anglais", "position": 1}, {"code": "2", "label": "French/Fran\u00E7ais", "position": 2}], "help_text": null, notes: "* **SINGLE ANSWER**\n* **Prog: show default instruction text side-by-side in both English (code=1000) and French (Code=3000).**"}` |
"""

class HtmlToJsonService:
    """Service for converting HTML/Markdown files to structured JSON using LLM."""
    
    def __init__(
        self, 
        llm_client: Optional[LLMClient] = None,
        verbose: bool = False,
        retry_attempts: int = 3
    ):
        """
        Initialize the HTML to JSON service.
        
        Args:
            llm_client: Optional LLM client instance (creates default if None)
            verbose: Enable verbose logging
            retry_attempts: Number of retry attempts for LLM calls
        """
        self.verbose = verbose
        self.llm_client = llm_client or LLMClient(
            providers=["anthropic", "openai"],
            retry_attempts=retry_attempts,
            retry_delay=1.0,
            retry_backoff=2.0
        )
        
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
            
    def _read_file_content(self, file_path: Path) -> str:
        """Read content from HTML or Markdown file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _create_section_prompt(
        self, 
        content: str, 
        section_title: str,
        position: int,
        total_sections: int
    ) -> List[Dict[str, str]]:
        """Create prompt for section extraction."""
        prompt = f"""
Analyze the following content and extract it as a structured section for a questionnaire.

CONTEXT:
- This is section {position} of {total_sections} total sections
- Section title: "{section_title}"
- Position in survey: {position}

CONTENT TO ANALYZE:
{content}

INSTRUCTIONS:
1. Extract the section information including code, label, notes, and position
2. Identify all question elements within this section
3. For each element, determine the type (CHOICE, OPEN_END, or BREAK_PAGE)
4. Extract variables and grid columns where applicable
5. Maintain the hierarchical structure and positioning information
6. Use the section title as the label and generate an appropriate code
7. Set the position to {position}

The response should follow the FullSectionResponseSchema structure with all nested elements properly defined.
"""
        
        return [{"role": "user", "content": prompt}]
    
    def _create_element_prompt(
        self, 
        content: str, 
        element_info: Dict[str, Any],
        position: int,
        section_context: str = ""
    ) -> List[Dict[str, str]]:
        """Create prompt for individual element extraction."""
        context_info = f"\nSection context: {section_context}" if section_context else ""
        element_label = element_info.get('label', f'question_{position}')
        
        prompt = f"""
Analyze the following content and extract it as a structured questionnaire element.

CONTEXT:
- Element identifier: "{element_label}"
- Position in section: {position}{context_info}

CONTENT TO ANALYZE:
{content}

INSTRUCTIONS:
1. Determine the element type (CHOICE, OPEN_END, or BREAK_PAGE)
2. Extract the code, label, notes, and other properties
3. Set the position to {position}
4. Generate a meaningful code from the content (not just "{element_label}")
5. Extract a descriptive label from the question text (not just "{element_label}")
6. If this is a choice question, extract all variables (answer options)
7. If this is a grid question, extract columns
8. Include any help text or additional settings
9. Generate appropriate codes for the element and its sub-components

The response should follow the FullSectionElementSchema structure.
"""
        
        return [{"role": "user", "content": prompt}]
    
    def convert_section_file(
        self, 
        file_path: Path, 
        section_info: Dict[str, Any],
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Convert a section file to JSON using LLM.
        
        Args:
            file_path: Path to the section file (HTML or Markdown)
            section_info: Section metadata from mapping
            output_dir: Optional output directory
            
        Returns:
            Dictionary with conversion results
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Section file not found: {file_path}")
        
        self._log(f"Converting section: {section_info['title']}")
        
        # Read content
        content = self._read_file_content(file_path)
        
        # Create prompt
        messages = self._create_section_prompt(
            content=content,
            section_title=section_info['title'],
            position=section_info['index'],
            total_sections=section_info.get('total_sections', 1)
        )
        
        try:
            # Get structured response from LLM
            response = self.llm_client.completion(
                messages=messages,
                response_format=FullSectionResponseSchema,
                temperature=0.0,
                max_tokens=4096
            )
            
            result = {
                'file': str(file_path),
                'section_info': section_info,
                'status': 'success',
                'provider': response['provider'],
                'usage': response['usage']
            }
            
            if 'parsed' in response and response['parsed']:
                result['parsed_section'] = response['parsed']
                result['raw_content'] = response['content']
                
                # Save to file if output directory specified
                if output_dir:
                    output_dir = Path(output_dir)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    output_file = output_dir / f"section_{section_info['index']:03d}_{file_path.stem}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'metadata': {
                                'source_file': str(file_path),
                                'section_info': section_info,
                                'conversion_timestamp': datetime.now().isoformat(),
                                'provider': response['provider'],
                                'usage': response['usage']
                            },
                            'section': response['parsed'].dict()
                        }, f, indent=2, ensure_ascii=False)
                    
                    result['output_file'] = str(output_file)
                    self._log(f"Saved section JSON: {output_file}")
            else:
                result['status'] = 'parse_error'
                result['error'] = response.get('parse_error', 'Failed to parse structured response')
                result['raw_content'] = response['content']
                
        except Exception as e:
            self._log(f"Error converting section {section_info['title']}: {e}")
            result = {
                'file': str(file_path),
                'section_info': section_info,
                'status': 'error',
                'error': str(e)
            }
            
        return result
    
    def convert_element_file(
        self, 
        file_path: Path, 
        element_info: Dict[str, Any],
        section_context: str = "",
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Convert an element file to JSON using LLM.
        
        Args:
            file_path: Path to the element file (HTML or Markdown)
            element_info: Element metadata from mapping
            section_context: Context about the parent section
            output_dir: Optional output directory
            
        Returns:
            Dictionary with conversion results
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Element file not found: {file_path}")
        
        element_label = element_info.get('label', f"question_{element_info.get('index', 0)}")
        self._log(f"Converting element: {element_label}")
        
        # Read content
        content = self._read_file_content(file_path)
        
        # Create prompt
        messages = self._create_element_prompt(
            content=content,
            element_info=element_info,
            position=element_info.get('index', 0),
            section_context=section_context
        )
        
        try:
            # Get structured response from LLM
            response = self.llm_client.completion(
                messages=messages,
                response_format=FullSectionElementSchema,
                temperature=0.0,
                max_tokens=4096
            )
            
            result = {
                'file': str(file_path),
                'element_info': element_info,
                'status': 'success',
                'provider': response['provider'],
                'usage': response['usage']
            }
            
            if 'parsed' in response and response['parsed']:
                result['parsed_element'] = response['parsed']
                result['raw_content'] = response['content']
                
                # Save to file if output directory specified
                if output_dir:
                    output_dir = Path(output_dir)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    
                    element_index = element_info.get('index', 0)
                    output_file = output_dir / f"element_{element_index:03d}_{file_path.stem}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'metadata': {
                                'source_file': str(file_path),
                                'element_info': element_info,
                                'section_context': section_context,
                                'conversion_timestamp': datetime.now().isoformat(),
                                'provider': response['provider'],
                                'usage': response['usage']
                            },
                            'element': response['parsed'].dict()
                        }, f, indent=2, ensure_ascii=False)
                    
                    result['output_file'] = str(output_file)
                    self._log(f"Saved element JSON: {output_file}")
            else:
                result['status'] = 'parse_error'
                result['error'] = response.get('parse_error', 'Failed to parse structured response')
                result['raw_content'] = response['content']
                
        except Exception as e:
            self._log(f"Error converting element {element_label}: {e}")
            result = {
                'file': str(file_path),
                'element_info': element_info,
                'status': 'error',
                'error': str(e)
            }
            
        return result
    
    def convert_from_mapping(
        self, 
        mapping_file: Path, 
        source_type: str = "html",
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Convert files to JSON based on mapping metadata.
        
        Args:
            mapping_file: Path to the mapping JSON file
            source_type: Type of source files ("html" or "markdown")
            output_dir: Optional output directory for JSON files
            
        Returns:
            Conversion results with statistics
        """
        mapping_file = Path(mapping_file)
        
        if not mapping_file.exists():
            raise FileNotFoundError(f"Mapping file not found: {mapping_file}")
        
        # Read mapping
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        self._log(f"Processing mapping from: {mapping_file}")
        
        # Determine source directory based on type
        base_dir = mapping_file.parent
        if source_type == "markdown":
            sections_dir = base_dir / "sections_md"
            elements_dir = base_dir / "questions_md"
            file_key = "md_filename"
        else:
            sections_dir = base_dir / "sections"
            elements_dir = base_dir / "questions"
            file_key = "html_filename"
        
        # Setup output directory
        if output_dir:
            output_dir = Path(output_dir)
        else:
            output_dir = base_dir / f"json_from_{source_type}"
            
        sections_json_dir = output_dir / "sections"
        elements_json_dir = output_dir / "elements"
        
        # Initialize results
        results = {
            'metadata': {
                'source_mapping': str(mapping_file),
                'source_type': source_type,
                'total_sections': mapping['metadata']['total_sections'],
                'total_questions': mapping['metadata']['total_questions'],
                'conversion_timestamp': datetime.now().isoformat()
            },
            'conversion_stats': {
                'sections_processed': 0,
                'sections_success': 0,
                'elements_processed': 0,
                'elements_success': 0,
                'total_tokens_used': {'input': 0, 'output': 0},
                'errors': []
            },
            'sections': [],
            'elements': []
        }
        
        # Process sections
        for section in mapping['sections']:
            section_filename = section.get(file_key)
            if not section_filename:
                self._log(f"Warning: No {file_key} found for section {section.get('title', section.get('index'))}")
                continue
                
            section_file = sections_dir / section_filename
            
            section_info = {
                **section,
                'total_sections': mapping['metadata']['total_sections']
            }
            
            results['conversion_stats']['sections_processed'] += 1
            
            try:
                section_result = self.convert_section_file(
                    file_path=section_file,
                    section_info=section_info,
                    output_dir=sections_json_dir
                )
                
                results['sections'].append(section_result)
                
                if section_result['status'] == 'success':
                    results['conversion_stats']['sections_success'] += 1
                    usage = section_result.get('usage', {})
                    results['conversion_stats']['total_tokens_used']['input'] += usage.get('input_tokens', 0)
                    results['conversion_stats']['total_tokens_used']['output'] += usage.get('output_tokens', 0)
                else:
                    error_msg = f"Section {section.get('title', section.get('index'))}: {section_result.get('error', 'Unknown error')}"
                    results['conversion_stats']['errors'].append(error_msg)
                    
            except Exception as e:
                error_msg = f"Section {section.get('title', section.get('index'))}: {str(e)}"
                results['conversion_stats']['errors'].append(error_msg)
                self._log(f"Error processing section: {error_msg}")
            
            # Process elements in this section
            for element in section.get('questions', []):
                element_filename = element.get(file_key)
                if not element_filename:
                    self._log(f"Warning: No {file_key} found for element {element.get('label', element.get('index'))}")
                    continue
                    
                element_file = elements_dir / element_filename
                
                results['conversion_stats']['elements_processed'] += 1
                
                try:
                    element_result = self.convert_element_file(
                        file_path=element_file,
                        element_info=element,
                        section_context=section.get('title', f"Section {section.get('index')}"),
                        output_dir=elements_json_dir
                    )
                    
                    results['elements'].append(element_result)
                    
                    if element_result['status'] == 'success':
                        results['conversion_stats']['elements_success'] += 1
                        usage = element_result.get('usage', {})
                        results['conversion_stats']['total_tokens_used']['input'] += usage.get('input_tokens', 0)
                        results['conversion_stats']['total_tokens_used']['output'] += usage.get('output_tokens', 0)
                    else:
                        error_msg = f"Element {element.get('label', element.get('index'))}: {element_result.get('error', 'Unknown error')}"
                        results['conversion_stats']['errors'].append(error_msg)
                        
                except Exception as e:
                    error_msg = f"Element {element.get('label', element.get('index'))}: {str(e)}"
                    results['conversion_stats']['errors'].append(error_msg)
                    self._log(f"Error processing element: {error_msg}")
        
        # Save conversion report
        report_file = output_dir / "conversion_report.json"
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        # Print summary
        stats = results['conversion_stats']
        self._log(f"\n=== Conversion Summary ===")
        self._log(f"Sections: {stats['sections_success']}/{stats['sections_processed']} successful")
        self._log(f"Elements: {stats['elements_success']}/{stats['elements_processed']} successful")
        self._log(f"Total tokens used: {stats['total_tokens_used']['input']} input, {stats['total_tokens_used']['output']} output")
        self._log(f"Errors: {len(stats['errors'])}")
        self._log(f"Report saved: {report_file}")
        
        return results
