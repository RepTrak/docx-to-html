"""
Service for processing markdown files in chunks to build FullSurveyResponseSchema incrementally.
"""

import logging
import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Iterator, Callable
from datetime import datetime, timedelta
import time

from ..llm import LLMClient
from ..models.questionnaire import (
    FullSurveyResponseSchema, FullSectionResponseSchema, 
    FullSectionElementSchema, VariableResponseSchema, GridColumnSchema
)
from ..models.parsing_state import (
    ChunkAnalysis, ChunkType, ParsingState, PartialSection, 
    PartialElement, ProcessingResult, ContentBoundary
)
from ..models.monitoring import ProcessingMonitor, PartialReport, ProcessingPhase

LLM_PROVIDER="openai"  # Default provider
LLM_MODEL="gpt-4o-mini-2024-07-18"  # Default model


SYSTEM_PROMPT = """
# Global context
** You are an expert algorithm that processes markdown files to extract structured questionnaire content.**
## Questionnaire Structure:
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
- **COUNTRY_DROPDOWN**: A dropdown list of countries (usually first question in a survey even if not explicitly mentioned)
- **AGE_ORI**: A question that asks for the respondent's age, with specific ranges and recoding questions. Normally with match with a question with the code `AGE_ORI`
- **S105_RATING_FAMILIARITY**: A question that rates familiarity of companies in the project
- **GEOGRAPHIC_AREA_REGION**: A question that asks for the respondent's geographic area or region and recodes. Normally with match with a question with the code `REGION_C`
- **PULSE_FILTER**: A question that filters respondents based on pulse criteria. Normally with match with a question with the code `Q305`
- **YES_NO**: A question that asks for a yes or no answer
- **EDUCATION_STANDARD**: A question that asks for the respondent's education level, with specific options and recoding questions. Normally with match with a question with the code `EDUCATION_C`
- **INCOME_STANDARD**: A question that asks for the respondent's income level, with specific options and recoding questions. Normally with match with a question with the code `INCOME_C`


## Input Format
The provided content will follow a specific structure, and your task is to extract relevant sections and elements with them children.
**MUST KEEP CODES and LABELS EXACTLY AS THEY ARE**.
### Sections format
| section input | expected output |
| `# Section 1000 \- Study Intro Text` | `{"code": "section_1000", "label": "Study Intro Text", "notes": null}` |
| `# Section 100 – Familiarity (Screener)` | `{"code": "section_100", "label": "Familiarity (Screener)", "notes": null}` |
| `# CEO SECTION (Company1, Company2, Company3\)` | `{"code": "section_ceo", "label": "CEO SECTION", "notes": null}` |

### Elements format
| element input | expected output |
| `**cQCA\\_Language\\_CA** :\r\n\r\nWould you prefer to complete the survey in English or French?\r\n\r\nPr\u00E9f\u00E9rez\\-vous r\u00E9pondre \u00E0 ce questionnaire en\r\nAnglais ou en Fran\u00E7ais?\r\n\r\n* **SINGLE\r\n ANSWER**\r\n* **Prog:\r\n show default instruction text side\\-by\\-side in both English\r\n (code\\=1000\\) and French (Code\\=3000\\).**\r\n\r\n| **Value** **Code** | **Value** **Label** |\r\n| 1 | English\/Anglais |\r\n| 2 | French\/Fran\u00E7ais |` | `{"code": "cQCA_Language_CA", "label": "nWould you prefer to complete the survey in English or French?\r\n\r\nPr\u00E9f\u00E9rez\\-vous r\u00E9pondre \u00E0 ce questionnaire en\r\nAnglais ou en Fran\u00E7ais?\r\n\r\n", "type": "CHOICE", "position": 1, "variables": [{"code": "1", "label": "English/Anglais", "position": 1}, {"code": "2", "label": "French/Fran\u00E7ais", "position": 2}], "help_text": null, notes: "* **SINGLE ANSWER**\n* **Prog: show default instruction text side-by-side in both English (code=1000) and French (Code=3000).**"}` |
| `**Gender**:What is your gender?\r\n\r\n* **SINGLE\r\n ANSWER**\r\n\r\n| **Value****Code** | **Value****Label** |\r\n| 1 | Male |\r\n| 2 | Female |` | {"code":"Gender", "type": "CHOICE", "label": "What is your gender?", "variables": [{"code":"1", "label"Male"}, {"code":"2", "label"Female"}]}`|
| `**AGE\\_ORI**:What is your age as of today?\r\n\r\n* **Programmer:** **Numeric\r\n open ended**\r\n\r\n    + **SHOW\r\n     AS A SINGLE SELECT RANGE FOR RUSSIA (AGE\\_RU). RECODE AS LISTED\r\n     BELOW**\r\n\r\n**Range for Russia:**\r\n\r\n* **Use\r\n Select One Instruction Text if RU:**\u0412\u044B\u0431\u0435\u0440\u0438\u0442\u0435\r\n \u043E\u0434\u0438\u043D \u0432\u0430\u0440\u0438\u0430\u043D\u0442 \u043E\u0442\u0432\u0435\u0442\u0430.\r\n\r\n| **Value Code** | **Value Label** | **Notes** |\r\n| 0 | Under 18 | Terminate |\r\n| 1 | 18\\-24 | RECODE TO GENERATION \\= 2 and AGE \\= 1 |\r\n| 2 | 25\\-34 | RECODE TO GENERATION \\= 3 and AGE \\= 2 |\r\n| 3 | 35\\-40 | RECODE TO GENERATION \\= 3 and AGE \\= 3 |\r\n| 4 | 41\\-44 | RECODE TO GENERATION \\= 4 and AGE \\= 3 |\r\n| 5 | 45\\-55 | RECODE TO GENERATION \\= 4 and AGE \\= 4 |\r\n| 6 | 56\\-64 | RECODE TO GENERATION \\= 5 and AGE \\= 4 |\r\n| 7 | 65\\+ | RECODE TO GENERATION \\= 6 and AGE \\= 5 |\r\n\r\n* **Programmer:\r\n Valid** **Range\r\n \u201C0\\-115\u201D**\r\n\r\n**Terminate:** **if\r\nAGE\\_ORI is below 18**\r\n\r\n**Age \\[HIDDEN \u2013 recode Age from question\r\nAGE\\_ORI]:**\r\n\r\n| **Value Code** | **Value Label** | **Notes** |\r\n| 0 | Under 18 | Terminate |\r\n| 1 | 18\\-24 |  |\r\n| 2 | 25\\-34 |  |\r\n| 3 | 35\\-44 |  |\r\n| 4 | 45\\-64 |  |\r\n| 5 | 65\\+ |  |\r\n\r\n**GENERATION \\[HIDDEN \u2013 recode Generation\r\nfrom question AGE\\_ORI]:**\r\n\r\n| **Value Code** | **Value Label** | **Notes** |\r\n| 1 | Under 18 | Terminate |\r\n| 2 | 18\\-25 | **GenZ** |\r\n| 3 | 26\\-40 | **Millennials** |\r\n| 4 | 41\\-55 | **GenX** |\r\n| 5 | 56\\-64 | **Baby Boomers** |\r\n| 6 | 65\\+ | **Older Baby Boomers \/ Silent Generation** |\r\n\r\n**\\[PN: IF AUSTRALIA (CODE\\=26\\) OR NEW ZEALAND\r\n(CODE\\=198\\): SHOW POSTCODE AND REGION\\_C ON SAME SCREEN]**\r\n\r\n**PN: ASK POSTCODE IF AUSTRALIA (CODE\\=26\\) OR\r\nNEW ZEALAND (CODE\\=198\\)**` | {"code":"AGE_ORI", "type": "AGE_ORI", "label": "What is your age as of today?"}`|
| `**Q215**: The next questions concern\r\na number of different attitudes or behaviors you might have toward a\r\ncompany.\r\n\r\nPlease consider how well they describe your attitude toward**\\<b\\>{\\#Company1}\\<\/b\\>**.\r\n\r\nPlease select a number from 1 to 7 where \u201C1\u201D means \u201CI strongly\r\ndisagree\u201D and \u201C7\u201D means \u201CI strongly agree\u201D.\r\n\r\n* **SINGLE\r\n ANSWER EACH ITEM.**\r\n* **RANDOMIZE.**\r\n* **PLEASE\r\n DISPLAY SCALE RESPONSE (I strongly agree 1, 2, \u2026, Not sure) ALSO\r\n AT THE BOTTOM OF THE GRID**\r\n* **PN:\r\n if respondent qualifies to rate Company 2, use variable naming\r\n \u201CQ216\u201D**\r\n* **PN:\r\n if respondent qualifies to rate Company 3, use variable naming\r\n \u201CQ217\u201D**\r\n\r\n| **Variable Name** | **Variable Label** | **NOTES** |\r\n| Q215\\_3 | I would say something positive about **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_4 | I would give the benefit of the doubt to **\\<b\\>{\\#Company1}\\<\/b\\>** if the company was facing a crisis |  |\r\n| Q215\\_5 | If **\\<b\\>{\\#Company1}\\<\/b\\>** was faced with a product  or service problem, I would trust them to do the right thing |  |\r\n| Q215\\_6 | **SHOW  DEFAULT TEXT:**If I had the opportunity, I would buy the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>** **UNLESS  AUSTRALIA (CODE\\=26\\) AND ONE OF THE FOLLOWING COMPANIES:*** **AustralianSuper  (COMPANY CODE \\= 260622\\)** * **HESTA  (COMPANY CODE \\= 260674\\)** * **Hostplus  (COMPANY CODE \\= 260675\\)** * **Rest  Super (COMPANY CODE \\= 260684\\)** * **QSuper  (COMPANY CODE \\= 260788\\)** * **Aware  Super (COMPANY CODE \\= 260789\\)** * **Australian  Retirement Trust (COMPANY CODE \\= 260826\\)** * **UniSuper  (COMPANY CODE \\= 260854\\)** **SHOW TEXT:**If I had the opportunity, I would be a  member of **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_7 | **SHOW  DEFAULT TEXT:**If I had the opportunity, I would invest in **\\<b\\>{\\#Company1}\\<\/b\\>** **UNLESS  AUSTRALIA (CODE\\=26\\) AND ONE OF THE FOLLOWING COMPANIES:*** **AustralianSuper  (COMPANY CODE \\= 260622\\)** * **HESTA  (COMPANY CODE \\= 260674\\)** * **Hostplus  (COMPANY CODE \\= 260675\\)** * **Rest  Super (COMPANY CODE \\= 260684\\)** * **QSuper  (COMPANY CODE \\= 260788\\)** * **Aware  Super (COMPANY CODE \\= 260789\\)** * **Australian  Retirement Trust (COMPANY CODE \\= 260826\\)** * **UniSuper  (COMPANY CODE \\= 260854\\)** **SHOW TEXT:**I would recommend to someone to invest their  super with **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_8 | If I had the opportunity, I would work for **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_10 | I would recommend the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n\r\n* **Programmer:\r\n Show scale numbers, except on \u201CNot sure\u201D**\r\n\r\n| **Value Code** | **Value Label** |\r\n| 1 | I strongly disagree 1 |\r\n| 2 | 2 |\r\n| 3 | 3 |\r\n| 4 | 4 |\r\n| 5 | 5 |\r\n| 6 | 6 |\r\n| 7 | I strongly agree 7 |\r\n| 99 | Not sure |` | {"code":"Q215", "type": "AGE_ORI", "label": "The next questions concern\r\na number of different attitudes or behaviors you might have toward a\r\ncompany.\r\n\r\nPlease consider how well they describe your attitude toward**\\<b\\>{\\#Company1}\\<\/b\\>**.\r\n\r\nPlease select a number from 1 to 7 where \u201C1\u201D means \u201CI strongly\r\ndisagree\u201D and \u201C7\u201D means \u201CI strongly agree\u201D.", "options": {"randomize_variables":true, "columns": [{"code":"1", "label":"I strongly disagree 1", ....}]}, "variables":[{"code":"3","label":"I would say something positive about **\\<b\\>{\\#Company1}\\<\/b\\>", ..., "code":"6","label":"If I had the opportunity, I would buy the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>", notes: "**SHOW  DEFAULT TEXT:**If I had the opportunity, I would buy the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>** **UNLESS  AUSTRALIA (CODE\\=26\\) AND ONE OF THE FOLLOWING COMPANIES:*** **AustralianSuper  (COMPANY CODE \\= 260622\\)** * **HESTA  (COMPANY CODE \\= 260674\\)** * **Hostplus  (COMPANY CODE \\= 260675\\)** * **Rest  Super (COMPANY CODE \\= 260684\\)** * **QSuper  (COMPANY CODE \\= 260788\\)** * **Aware  Super (COMPANY CODE \\= 260789\\)** * **Australian  Retirement Trust (COMPANY CODE \\= 260826\\)** * **UniSuper  (COMPANY CODE \\= 260854\\)** **SHOW TEXT:**If I had the opportunity, I would be a  member of **\\<b\\>{\\#Company1}\\<\/b\\>**"}], "columns": [{"code":"1", "label":"I strongly disagree 1", ....}]}`|

** In general any information that does not fit in the schema fields, must me placed in `notes` at section, element or variable level.***
"""

CHUNK_ANALYSIS_PROMPT = """
You are an expert algorithm that analyzes markdown chunks to identify questionnaire structure.

**Your task**: Analyze the provided markdown chunk and determine:
1. What type of content this chunk contains
2. Whether it starts, continues, or completes sections/elements
3. Extract any structured content found
4. Provide context for the next chunk

**Content Types**:
- SECTION_START: Beginning of a new section (usually starts with # header)
- SECTION_CONTINUATION: Continuation of current section content
- ELEMENT_START: Beginning of a new question/element (usually **bold** text)
- ELEMENT_CONTINUATION: Continuation of current element content
- ELEMENT_COMPLETE: A complete element that can be finalized
- SECTION_COMPLETE: End of current section
- DOCUMENT_END: End of document
- UNKNOWN: Unclear content type

**Analysis Context**:
- Current parsing state: {parsing_state}
- Current position: Chunk {chunk_index} of {total_chunks}
- Previous chunk type: {previous_chunk_type}

**Chunk Content**:
{chunk_content}

**Instructions**:
1. Identify the chunk type based on content patterns
2. Determine content boundaries (what starts/continues/completes)
3. Extract any complete structured elements
4. Assess completion status
5. Provide continuation context for next chunk
6. Set confidence level (0.0-1.0)

Respond with structured ChunkAnalysis.
"""

CONTENT_EXTRACTION_PROMPT = """
# LOCAL CONTEXT
Extract structured questionnaire content from the provided text.

**Context**: {context}
**Content Type**: {content_type}
**Accumulated Content**: {accumulated_content}

**Current Chunk**:
{chunk_content}

**Instructions**:
1. If this is a SECTION: extract code, label, notes, position
2. If this is an ELEMENT: extract code, label, type, variables, columns, etc.
3. Merge with accumulated content if this is a continuation
4. Generate appropriate codes and maintain structure
5. Keep original formatting and text exactly as provided

**Expected Structure**: {expected_schema}

Extract as much structured content as possible from the available text.
"""

class MarkdownChunkProcessor:
    """Service for processing markdown files in chunks to build survey schemas."""
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        chunk_size: int = 2000,
        chunk_overlap: int = 200,
        verbose: bool = False,
        retry_attempts: int = 3,
        progress_callback: Optional[Callable[[PartialReport], None]] = None,
        auto_save_interval: int = 10,
        auto_save_dir: Optional[str] = None
    ):
        """
        Initialize the chunk processor.
        
        Args:
            llm_client: Optional LLM client instance
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
            verbose: Enable verbose logging
            retry_attempts: Number of retry attempts for LLM calls
            progress_callback: Optional callback for progress updates
            auto_save_interval: Save partial results every N chunks
            auto_save_dir: Directory for auto-saving partial results
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.verbose = verbose
        self.llm_client = llm_client or LLMClient(
            providers=["anthropic", "openai"],
            retry_attempts=retry_attempts,
            retry_delay=1.0,
            retry_backoff=2.0
        )
        
        # Initialize monitoring
        self.monitor = ProcessingMonitor(
            progress_callback=progress_callback,
            save_interval_chunks=auto_save_interval,
            auto_save_dir=auto_save_dir
        )
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def _chunk_markdown(self, content: str) -> List[str]:
        """Split markdown content into overlapping chunks."""
        if len(content) <= self.chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            end = start + self.chunk_size
            
            # If not the last chunk, try to break at a good boundary
            if end < len(content):
                # Look for section breaks (## headers) within overlap distance
                section_break = content.rfind('\n# ', start, end)
                if section_break > start:
                    end = section_break
                else:
                    # Look for element breaks (**bold**) within overlap distance
                    element_break = content.rfind('\n**', start, end)
                    if element_break > start:
                        end = element_break
                    else:
                        # Look for paragraph breaks
                        para_break = content.rfind('\n\n', start, end)
                        if para_break > start:
                            end = para_break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Calculate next start position with overlap
            if end >= len(content):
                break
            start = max(start + 1, end - self.chunk_overlap)
        
        return chunks
    
    def _analyze_chunk(
        self, 
        chunk: str, 
        chunk_index: int, 
        total_chunks: int,
        parsing_state: ParsingState
    ) -> ChunkAnalysis:
        """Analyze a chunk to determine its type and content."""
        
        start_time = time.time()
        
        # Create analysis prompt
        prompt = CHUNK_ANALYSIS_PROMPT.format(
            parsing_state=parsing_state.parsing_phase,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            previous_chunk_type=parsing_state.last_chunk_type,
            chunk_content=chunk
        )
        
        messages = [{"role": "assistant", "content": SYSTEM_PROMPT},{"role": "user", "content": prompt}]
        
        try:
            response = self.llm_client.completion(
                messages=messages,
                response_format=ChunkAnalysis,
                provider=LLM_PROVIDER,
                model=LLM_MODEL,
                temperature=0.1,
                max_tokens=8192
            )
            
            processing_time = int((time.time() - start_time) * 1000)
            
            if 'parsed' in response and response['parsed']:
                analysis = response['parsed']
                analysis.chunk_index = chunk_index
                logging.info(f"Chunk {chunk_index} analysis: {analysis}")
                
                # Update monitoring
                self.monitor.complete_chunk_analysis(
                    chunk_index, 
                    analysis.chunk_type.value, 
                    analysis.confidence,
                    processing_time
                )
                
                # Track token usage if available
                if 'usage' in response:
                    usage = response['usage']
                    self.monitor.update_token_usage(
                        usage.get('prompt_tokens', 0),
                        usage.get('completion_tokens', 0)
                    )
                
                return analysis
            else:
                # Fallback analysis
                self.monitor.complete_chunk_analysis(
                    chunk_index, 
                    ChunkType.UNKNOWN.value, 
                    0.0,
                    processing_time
                )
                return ChunkAnalysis(
                    chunk_index=chunk_index,
                    chunk_type=ChunkType.UNKNOWN,
                    confidence=0.0
                )
                
        except Exception as e:
            self._log(f"Error analyzing chunk {chunk_index}: {e}")
            self.monitor.add_error(f"Analysis error in chunk {chunk_index}: {str(e)}")
            return ChunkAnalysis(
                chunk_index=chunk_index,
                chunk_type=ChunkType.UNKNOWN,
                confidence=0.0
            )
    
    def _extract_content(
        self, 
        chunk: str, 
        analysis: ChunkAnalysis, 
        parsing_state: ParsingState
    ) -> Optional[Dict]:
        """Extract structured content from a chunk based on analysis."""
        
        context = f"Chunk {analysis.chunk_index}, Type: {analysis.chunk_type}"
        accumulated_content = ""
        expected_schema = ""
        
        if analysis.chunk_type in [ChunkType.SECTION_START, ChunkType.SECTION_CONTINUATION]:
            if parsing_state.current_section:
                accumulated_content = parsing_state.current_section.accumulated_content
            expected_schema = "FullSectionResponseSchema"
        elif analysis.chunk_type in [ChunkType.ELEMENT_START, ChunkType.ELEMENT_CONTINUATION, ChunkType.ELEMENT_COMPLETE]:
            if parsing_state.current_element:
                accumulated_content = parsing_state.current_element.accumulated_content
            expected_schema = "FullSectionElementSchema"
        
        prompt = CONTENT_EXTRACTION_PROMPT.format(
            context=context,
            content_type=analysis.chunk_type,
            accumulated_content=accumulated_content,
            chunk_content=chunk,
            expected_schema=expected_schema
        )
        
        messages = [{"role": "assistant", "content": SYSTEM_PROMPT},{"role": "user", "content": prompt}]
        
        try:
            # Use appropriate response format based on content type
            if analysis.chunk_type in [ChunkType.SECTION_START, ChunkType.SECTION_CONTINUATION]:
                response_format = FullSectionResponseSchema
            else:
                response_format = FullSectionElementSchema
            
            response = self.llm_client.completion(
                messages=messages,
                response_format=response_format,
                provider=LLM_PROVIDER,
                model=LLM_MODEL,
                temperature=0.1,
                max_tokens=8192
            )
            
            if 'parsed' in response and response['parsed']:
                # Update monitoring
                self.monitor.complete_chunk_extraction(analysis.chunk_index)
                
                # Track token usage if available
                if 'usage' in response:
                    usage = response['usage']
                    self.monitor.update_token_usage(
                        usage.get('prompt_tokens', 0),
                        usage.get('completion_tokens', 0)
                    )
                
                return response['parsed'].dict()
            
        except Exception as e:
            self._log(f"Error extracting content from chunk {analysis.chunk_index}: {e}")
            self.monitor.add_error(f"Extraction error in chunk {analysis.chunk_index}: {str(e)}")
        
        return None
    
    def _update_parsing_state(
        self, 
        chunk: str, 
        analysis: ChunkAnalysis, 
        extracted_content: Optional[Dict],
        parsing_state: ParsingState
    ) -> None:
        """Update parsing state based on chunk analysis and extracted content."""
        
        parsing_state.current_chunk_index = analysis.chunk_index
        parsing_state.last_chunk_type = analysis.chunk_type
        
        # Handle section-level changes
        if analysis.chunk_type == ChunkType.SECTION_START:
            # Complete current section if exists
            if parsing_state.current_section and parsing_state.current_section.is_complete:
                self._finalize_current_section(parsing_state)
            
            # Start new section
            parsing_state.current_section = PartialSection(
                accumulated_content=chunk
            )
            parsing_state.parsing_phase = "section"
            parsing_state.global_position_counters["section"] += 1
            
            if extracted_content:
                self._merge_section_content(parsing_state.current_section, extracted_content)
        
        elif analysis.chunk_type == ChunkType.SECTION_CONTINUATION:
            if parsing_state.current_section:
                parsing_state.current_section.accumulated_content += "\n" + chunk
                if extracted_content:
                    self._merge_section_content(parsing_state.current_section, extracted_content)
        
        elif analysis.chunk_type == ChunkType.ELEMENT_START:
            # Complete current element if exists
            if parsing_state.current_element and parsing_state.current_element.is_complete:
                self._finalize_current_element(parsing_state)
            
            # Start new element
            parsing_state.current_element = PartialElement(
                accumulated_content=chunk
            )
            parsing_state.parsing_phase = "element"
            parsing_state.global_position_counters["element"] += 1
            
            if extracted_content:
                self._merge_element_content(parsing_state.current_element, extracted_content)
        
        elif analysis.chunk_type == ChunkType.ELEMENT_CONTINUATION:
            if parsing_state.current_element:
                parsing_state.current_element.accumulated_content += "\n" + chunk
                if extracted_content:
                    self._merge_element_content(parsing_state.current_element, extracted_content)
        
        elif analysis.chunk_type == ChunkType.ELEMENT_COMPLETE:
            if parsing_state.current_element:
                parsing_state.current_element.accumulated_content += "\n" + chunk
                if extracted_content:
                    self._merge_element_content(parsing_state.current_element, extracted_content)
                parsing_state.current_element.is_complete = True
        
        elif analysis.chunk_type == ChunkType.SECTION_COMPLETE:
            if parsing_state.current_section:
                parsing_state.current_section.is_complete = True
        
        # Update context buffer
        parsing_state.context_buffer = chunk[-self.chunk_overlap:] if len(chunk) > self.chunk_overlap else chunk
        
        # Update monitoring with current previews
        section_preview = None
        element_preview = None
        
        if parsing_state.current_section:
            section_preview = {
                "code": parsing_state.current_section.code,
                "label": parsing_state.current_section.label,
                "elements_count": len(parsing_state.current_section.elements or [])
            }
        
        if parsing_state.current_element:
            element_preview = {
                "code": parsing_state.current_element.code,
                "label": parsing_state.current_element.label,
                "type": parsing_state.current_element.type,
                "variables_count": len(parsing_state.current_element.variables or []),
                "columns_count": len(parsing_state.current_element.columns or [])
            }
        
        self.monitor.update_current_previews(section_preview, element_preview)
        
        # Update content counts
        total_elements = sum(len(section.elements or []) for section in parsing_state.completed_sections)
        if parsing_state.current_section and parsing_state.current_section.elements:
            total_elements += len(parsing_state.current_section.elements)
        
        total_variables = 0
        total_columns = 0
        for section in parsing_state.completed_sections:
            for element in section.elements or []:
                total_variables += len(element.variables or [])
                total_columns += len(element.columns or [])
        
        self.monitor.update_content_counts(
            len(parsing_state.completed_sections),
            total_elements,
            total_variables,
            total_columns
        )
    
    def _merge_section_content(self, partial_section: PartialSection, content: Dict) -> None:
        """Merge extracted content into partial section."""
        for key, value in content.items():
            if value is not None:
                if key == "elements":
                    # Handle elements separately
                    continue
                setattr(partial_section, key, value)
    
    def _merge_element_content(self, partial_element: PartialElement, content: Dict) -> None:
        """Merge extracted content into partial element."""
        for key, value in content.items():
            if value is not None:
                if key in ["variables", "columns"]:
                    # Merge lists
                    current_list = getattr(partial_element, key, [])
                    if isinstance(value, list):
                        # Merge by code/id to avoid duplicates
                        existing_codes = {item.get('code') for item in current_list if isinstance(item, dict)}
                        for item in value:
                            if isinstance(item, dict) and item.get('code') not in existing_codes:
                                current_list.append(item)
                        setattr(partial_element, key, current_list)
                else:
                    setattr(partial_element, key, value)
    
    def _finalize_current_element(self, parsing_state: ParsingState) -> None:
        """Finalize current element and add to current section."""
        if not parsing_state.current_element:
            return
        
        # Convert partial element to full schema
        element_data = {
            "code": parsing_state.current_element.code or f"element_{parsing_state.global_position_counters['element']}",
            "label": parsing_state.current_element.label or "Untitled Element",
            "type": parsing_state.current_element.type or "CHOICE",
            "position": parsing_state.current_element.position or parsing_state.global_position_counters["element"],
            "notes": parsing_state.current_element.notes,
            "revision": parsing_state.current_element.revision,
            "tags": parsing_state.current_element.tags,
            "is_loop_target": parsing_state.current_element.is_loop_target,
            "help_text": parsing_state.current_element.help_text,
            "variables": parsing_state.current_element.variables,
            "columns": parsing_state.current_element.columns
        }
        
        try:
            element = FullSectionElementSchema(**element_data)
            
            # Add to current section
            if parsing_state.current_section:
                if not hasattr(parsing_state.current_section, 'elements') or parsing_state.current_section.elements is None:
                    parsing_state.current_section.elements = []
                parsing_state.current_section.elements.append(PartialElement(**element.dict()))
            
        except Exception as e:
            self._log(f"Error finalizing element: {e}")
        
        # Clear current element
        parsing_state.current_element = None
    
    def _finalize_current_section(self, parsing_state: ParsingState) -> None:
        """Finalize current section and add to completed sections."""
        if not parsing_state.current_section:
            return
        
        # Finalize any pending element
        if parsing_state.current_element:
            self._finalize_current_element(parsing_state)
        
        # Convert partial elements to full schemas
        elements = []
        if parsing_state.current_section.elements:
            for partial_elem in parsing_state.current_section.elements:
                if isinstance(partial_elem, PartialElement):
                    elem_data = {
                        "code": partial_elem.code or f"element_{len(elements) + 1}",
                        "label": partial_elem.label or "Untitled Element",
                        "type": partial_elem.type or "CHOICE",
                        "position": partial_elem.position or len(elements) + 1,
                        "notes": partial_elem.notes,
                        "revision": partial_elem.revision,
                        "tags": partial_elem.tags,
                        "is_loop_target": partial_elem.is_loop_target,
                        "help_text": partial_elem.help_text,
                        "variables": partial_elem.variables,
                        "columns": partial_elem.columns
                    }
                    try:
                        elements.append(FullSectionElementSchema(**elem_data))
                    except Exception as e:
                        self._log(f"Error converting partial element: {e}")
        
        # Create full section
        section_data = {
            "code": parsing_state.current_section.code or f"section_{parsing_state.global_position_counters['section']}",
            "label": parsing_state.current_section.label or "Untitled Section",
            "position": parsing_state.current_section.position or parsing_state.global_position_counters["section"],
            "notes": parsing_state.current_section.notes,
            "loop": parsing_state.current_section.loop,
            "elements": elements
        }
        
        try:
            section = FullSectionResponseSchema(**section_data)
            parsing_state.completed_sections.append(section)
            
            # Update monitoring
            self.monitor.add_completed_section(section.dict())
            
        except Exception as e:
            self._log(f"Error finalizing section: {e}")
            self.monitor.add_error(f"Error finalizing section: {str(e)}")
        
        # Clear current section
        parsing_state.current_section = None
    
    def process_markdown_file(
        self, 
        file_path: Path,
        output_dir: Optional[Path] = None
    ) -> ProcessingResult:
        """
        Process a markdown file in chunks to build FullSurveyResponseSchema.
        
        Args:
            file_path: Path to the markdown file
            output_dir: Optional output directory for results
            
        Returns:
            ProcessingResult with the complete survey schema and stats
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")
        
        self._log(f"Processing markdown file: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split into chunks
        self.monitor.update_phase(ProcessingPhase.CHUNKING)
        chunks = self._chunk_markdown(content)
        self._log(f"Split into {len(chunks)} chunks")
        
        # Initialize monitoring
        self.monitor.initialize(str(file_path), len(chunks))
        
        # Initialize parsing state
        parsing_state = ParsingState(
            total_chunks=len(chunks),
            global_position_counters={"section": 0, "element": 0}
        )
        
        # Process each chunk
        self.monitor.update_phase(ProcessingPhase.ANALYZING)
        total_tokens = {"input": 0, "output": 0}
        errors = []
        warnings = []
        
        logging.info(f"Starting processing of {len(chunks)} chunks")
        
        for i, chunk in enumerate(chunks):
            try:
                self._log(f"Processing chunk {i+1}/{len(chunks)}")
                
                # Start chunk in monitor
                self.monitor.start_chunk(i, len(chunk))
                
                # Analyze chunk
                analysis = self._analyze_chunk(chunk, i, len(chunks), parsing_state)
                
                # Extract content if needed
                extracted_content = None
                if analysis.chunk_type != ChunkType.UNKNOWN:
                    extracted_content = self._extract_content(chunk, analysis, parsing_state)
                
                # Update parsing state
                self._update_parsing_state(chunk, analysis, extracted_content, parsing_state)
                
                # Complete chunk in monitor
                self.monitor.complete_chunk(i)
                
            except Exception as e:
                error_msg = f"Error processing chunk {i}: {str(e)}"
                errors.append(error_msg)
                self.monitor.complete_chunk(i, error_msg)
                self._log(error_msg)
                raise e  # Re-raise to stop processing on error
        
        # Finalize any remaining content
        self.monitor.update_phase(ProcessingPhase.FINALIZING)
        if parsing_state.current_element:
            self._finalize_current_element(parsing_state)
        if parsing_state.current_section:
            self._finalize_current_section(parsing_state)
        
        # Build final survey schema
        survey = FullSurveyResponseSchema(
            sections=parsing_state.completed_sections
        )
        
        # Update monitoring with completion
        self.monitor.update_phase(ProcessingPhase.COMPLETED)
        
        # Get final token usage from monitor
        monitor_report = self.monitor.get_current_report()
        if monitor_report:
            total_tokens = monitor_report.token_usage
        
        # Create result
        result = ProcessingResult(
            survey=survey,
            parsing_stats={
                "total_chunks": len(chunks),
                "sections_found": len(parsing_state.completed_sections),
                "elements_found": sum(len(section.elements or []) for section in parsing_state.completed_sections),
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap
            },
            chunks_processed=len(chunks),
            sections_found=len(parsing_state.completed_sections),
            elements_found=sum(len(section.elements or []) for section in parsing_state.completed_sections),
            total_tokens_used=total_tokens,
            errors=errors,
            warnings=warnings
        )
        
        # Save results if output directory specified
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save survey JSON
            survey_file = output_dir / f"{file_path.stem}_survey.json"
            with open(survey_file, 'w', encoding='utf-8') as f:
                json.dump(survey.dict(), f, indent=2, ensure_ascii=False)
            
            # Save processing report
            report_file = output_dir / f"{file_path.stem}_processing_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(result.dict(), f, indent=2, ensure_ascii=False, default=str)
            
            # Save final partial report
            if monitor_report:
                partial_report_file = output_dir / f"{file_path.stem}_partial_report_final.json"
                with open(partial_report_file, 'w', encoding='utf-8') as f:
                    json.dump(monitor_report.dict(), f, indent=2, ensure_ascii=False, default=str)
            
            self._log(f"Results saved to: {output_dir}")
        
        return result
    
    def get_partial_report(self) -> Optional[PartialReport]:
        """Get the current partial report for monitoring."""
        return self.monitor.get_current_report()
