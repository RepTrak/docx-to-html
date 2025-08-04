"""
Builds prompts for LLM processing of markdown chunks.
"""

from typing import Dict, Any



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
- **AGE_STANDARD**: A question that asks for the respondent's age, with specific ranges and recoding questions. Normally with match with a question with the code `AGE_ORI`
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
| `**cQCA\\_Language\\_CA** [CHOICE]:\r\n\r\nWould you prefer to complete the survey in English or French?\r\n===\r\nPr\u00E9f\u00E9rez\\-vous r\u00E9pondre \u00E0 ce questionnaire en\r\nAnglais ou en Fran\u00E7ais?\r\n\r\n* **SINGLE\r\n ANSWER**\r\n* **Prog:\r\n show default instruction text side\\-by\\-side in both English\r\n (code\\=1000\\) and French (Code\\=3000\\).**\r\n\r\n| **Value** **Code** | **Value** **Label** |\r\n| 1 | English\/Anglais |\r\n| 2 | French\/Fran\u00E7ais |` | `{"code": "cQCA_Language_CA", "label": "nWould you prefer to complete the survey in English or French?\r\n\r\nPr\u00E9f\u00E9rez\\-vous r\u00E9pondre \u00E0 ce questionnaire en\r\nAnglais ou en Fran\u00E7ais?\r\n\r\n", "type": "CHOICE", "position": 1, "variables": [{"code": "1", "label": "English/Anglais", "position": 1}, {"code": "2", "label": "French/Fran\u00E7ais", "position": 2}], "help_text": null, notes: "* **SINGLE ANSWER**\n* **Prog: show default instruction text side-by-side in both English (code=1000) and French (Code=3000).**"}` |
| `**Gender**[CHOICE]:What is your gender?\r\n===\r\n* **SINGLE\r\n ANSWER**\r\n\r\n| **Value****Code** | **Value****Label** |\r\n| 1 | Male |\r\n| 2 | Female |` | {"code":"Gender", "type": "CHOICE", "label": "What is your gender?", "variables": [{"code":"1", "label"Male"}, {"code":"2", "label"Female"}]}`|
| `**AGE\\_ORI**[AGE_STANDARD]:What is your age as of today?\r\n===\r\n* **Programmer:** **Numeric\r\n open ended**\r\n\r\n    + **SHOW\r\n     AS A SINGLE SELECT RANGE FOR RUSSIA (AGE\\_RU). RECODE AS LISTED\r\n     BELOW**\r\n\r\n**Range for Russia:**\r\n\r\n* **Use\r\n Select One Instruction Text if RU:**\u0412\u044B\u0431\u0435\u0440\u0438\u0442\u0435\r\n \u043E\u0434\u0438\u043D \u0432\u0430\u0440\u0438\u0430\u043D\u0442 \u043E\u0442\u0432\u0435\u0442\u0430.\r\n\r\n| **Value Code** | **Value Label** | **Notes** |\r\n| 0 | Under 18 | Terminate |\r\n| 1 | 18\\-24 | RECODE TO GENERATION \\= 2 and AGE \\= 1 |\r\n| 2 | 25\\-34 | RECODE TO GENERATION \\= 3 and AGE \\= 2 |\r\n| 3 | 35\\-40 | RECODE TO GENERATION \\= 3 and AGE \\= 3 |\r\n| 4 | 41\\-44 | RECODE TO GENERATION \\= 4 and AGE \\= 3 |\r\n| 5 | 45\\-55 | RECODE TO GENERATION \\= 4 and AGE \\= 4 |\r\n| 6 | 56\\-64 | RECODE TO GENERATION \\= 5 and AGE \\= 4 |\r\n| 7 | 65\\+ | RECODE TO GENERATION \\= 6 and AGE \\= 5 |\r\n\r\n* **Programmer:\r\n Valid** **Range\r\n \u201C0\\-115\u201D**\r\n\r\n**Terminate:** **if\r\nAGE\\_ORI is below 18**\r\n\r\n**Age \\[HIDDEN \u2013 recode Age from question\r\nAGE\\_ORI]:**\r\n\r\n| **Value Code** | **Value Label** | **Notes** |\r\n| 0 | Under 18 | Terminate |\r\n| 1 | 18\\-24 |  |\r\n| 2 | 25\\-34 |  |\r\n| 3 | 35\\-44 |  |\r\n| 4 | 45\\-64 |  |\r\n| 5 | 65\\+ |  |\r\n\r\n**GENERATION \\[HIDDEN \u2013 recode Generation\r\nfrom question AGE\\_ORI]:**\r\n\r\n| **Value Code** | **Value Label** | **Notes** |\r\n| 1 | Under 18 | Terminate |\r\n| 2 | 18\\-25 | **GenZ** |\r\n| 3 | 26\\-40 | **Millennials** |\r\n| 4 | 41\\-55 | **GenX** |\r\n| 5 | 56\\-64 | **Baby Boomers** |\r\n| 6 | 65\\+ | **Older Baby Boomers \/ Silent Generation** |\r\n\r\n**\\[PN: IF AUSTRALIA (CODE\\=26\\) OR NEW ZEALAND\r\n(CODE\\=198\\): SHOW POSTCODE AND REGION\\_C ON SAME SCREEN]**\r\n\r\n**PN: ASK POSTCODE IF AUSTRALIA (CODE\\=26\\) OR\r\nNEW ZEALAND (CODE\\=198\\)**` | {"code":"AGE_ORI", "type": "AGE_ORI", "label": "What is your age as of today?"}`|
| `**Q215**[CHOICE]: The next questions concern\r\na number of different attitudes or behaviors you might have toward a\r\ncompany.\r\n\r\nPlease consider how well they describe your attitude toward**\\<b\\>{\\#Company1}\\<\/b\\>**.\r\n\r\nPlease select a number from 1 to 7 where \u201C1\u201D means \u201CI strongly\r\ndisagree\u201D and \u201C7\u201D means \u201CI strongly agree\u201D.\r\n===\r\n* **SINGLE\r\n ANSWER EACH ITEM.**\r\n* **RANDOMIZE.**\r\n* **PLEASE\r\n DISPLAY SCALE RESPONSE (I strongly agree 1, 2, \u2026, Not sure) ALSO\r\n AT THE BOTTOM OF THE GRID**\r\n* **PN:\r\n if respondent qualifies to rate Company 2, use variable naming\r\n \u201CQ216\u201D**\r\n* **PN:\r\n if respondent qualifies to rate Company 3, use variable naming\r\n \u201CQ217\u201D**\r\n\r\n| **Variable Name** | **Variable Label** | **NOTES** |\r\n| Q215\\_3 | I would say something positive about **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_4 | I would give the benefit of the doubt to **\\<b\\>{\\#Company1}\\<\/b\\>** if the company was facing a crisis |  |\r\n| Q215\\_5 | If **\\<b\\>{\\#Company1}\\<\/b\\>** was faced with a product  or service problem, I would trust them to do the right thing |  |\r\n| Q215\\_6 | **SHOW  DEFAULT TEXT:**If I had the opportunity, I would buy the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>** **UNLESS  AUSTRALIA (CODE\\=26\\) AND ONE OF THE FOLLOWING COMPANIES:*** **AustralianSuper  (COMPANY CODE \\= 260622\\)** * **HESTA  (COMPANY CODE \\= 260674\\)** * **Hostplus  (COMPANY CODE \\= 260675\\)** * **Rest  Super (COMPANY CODE \\= 260684\\)** * **QSuper  (COMPANY CODE \\= 260788\\)** * **Aware  Super (COMPANY CODE \\= 260789\\)** * **Australian  Retirement Trust (COMPANY CODE \\= 260826\\)** * **UniSuper  (COMPANY CODE \\= 260854\\)** **SHOW TEXT:**If I had the opportunity, I would be a  member of **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_7 | **SHOW  DEFAULT TEXT:**If I had the opportunity, I would invest in **\\<b\\>{\\#Company1}\\<\/b\\>** **UNLESS  AUSTRALIA (CODE\\=26\\) AND ONE OF THE FOLLOWING COMPANIES:*** **AustralianSuper  (COMPANY CODE \\= 260622\\)** * **HESTA  (COMPANY CODE \\= 260674\\)** * **Hostplus  (COMPANY CODE \\= 260675\\)** * **Rest  Super (COMPANY CODE \\= 260684\\)** * **QSuper  (COMPANY CODE \\= 260788\\)** * **Aware  Super (COMPANY CODE \\= 260789\\)** * **Australian  Retirement Trust (COMPANY CODE \\= 260826\\)** * **UniSuper  (COMPANY CODE \\= 260854\\)** **SHOW TEXT:**I would recommend to someone to invest their  super with **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_8 | If I had the opportunity, I would work for **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_10 | I would recommend the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n\r\n* **Programmer:\r\n Show scale numbers, except on \u201CNot sure\u201D**\r\n\r\n| **Value Code** | **Value Label** |\r\n| 1 | I strongly disagree 1 |\r\n| 2 | 2 |\r\n| 3 | 3 |\r\n| 4 | 4 |\r\n| 5 | 5 |\r\n| 6 | 6 |\r\n| 7 | I strongly agree 7 |\r\n| 99 | Not sure |` | {"code":"Q215", "type": "AGE_ORI", "label": "The next questions concern\r\na number of different attitudes or behaviors you might have toward a\r\ncompany.\r\n\r\nPlease consider how well they describe your attitude toward**\\<b\\>{\\#Company1}\\<\/b\\>**.\r\n\r\nPlease select a number from 1 to 7 where \u201C1\u201D means \u201CI strongly\r\ndisagree\u201D and \u201C7\u201D means \u201CI strongly agree\u201D.", "options": {"randomize_variables":true, "columns": [{"code":"1", "label":"I strongly disagree 1", ....}]}, "variables":[{"code":"3","label":"I would say something positive about **\\<b\\>{\\#Company1}\\<\/b\\>", ..., "code":"6","label":"If I had the opportunity, I would buy the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>", notes: "**SHOW  DEFAULT TEXT:**If I had the opportunity, I would buy the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>** **UNLESS  AUSTRALIA (CODE\\=26\\) AND ONE OF THE FOLLOWING COMPANIES:*** **AustralianSuper  (COMPANY CODE \\= 260622\\)** * **HESTA  (COMPANY CODE \\= 260674\\)** * **Hostplus  (COMPANY CODE \\= 260675\\)** * **Rest  Super (COMPANY CODE \\= 260684\\)** * **QSuper  (COMPANY CODE \\= 260788\\)** * **Aware  Super (COMPANY CODE \\= 260789\\)** * **Australian  Retirement Trust (COMPANY CODE \\= 260826\\)** * **UniSuper  (COMPANY CODE \\= 260854\\)** **SHOW TEXT:**If I had the opportunity, I would be a  member of **\\<b\\>{\\#Company1}\\<\/b\\>**"}], "columns": [{"code":"1", "label":"I strongly disagree 1", ....}]}`|

** In general any information that does not fit in the schema fields, must me placed in `notes` at section, element or variable level.***

### Text format rules
#### Sections
Section have format: `Section {code} - {label}`
#### Elements
Element have format:
```
**{code}**[TYPE]: {label multi line text}
{label multi line text}
{label multi line text}
===
```
Where `===` is the delimiter of the end of the label. After `===` you can found element options, programer notes (notes) and table with variables or columns.
#### Variables
Variables are defined in tables with format:
```
| **Value Code** | **Value Label** | **Notes** |
| 0 | Under 18 | Terminate |
```
Where `Value Code` is the variable code, `Value Label` is the variable label and `Notes` are additional information about the variable.
`Value Code` column could be named as `Code`, `Value Code`, `Variable Code` or similar, and `Value Label` column could be named as `Label`, `Value Label`, `Variable Label` or similar.
If `Value Code` have format `{question_code}_{variable_code}` it means that this variable is a part of a question with the code `{question_code}` and the variable code is `{variable_code}`, keep only `{variable_code}` in the output.
#### Columns
Columns are defined in tables with format:
```
| **Value Code** | **Value Label** |
| 1 | I strongly disagree 1 |
```
Where `Value Code` is the column code and `Value Label` is the column label.

"""


class PromptBuilder:
    """Builds system and user prompts for LLM processing."""
    
    def __init__(self):
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for LLM processing."""
        return """You are an expert at converting questionnaire markdown content into structured JSON schemas.

Your task is to analyze markdown chunks containing questionnaire sections and elements, then extract structured data following the FullSurveyResponseSchema format.

# Schema Definitions

## Section Schema:
```json
{
  "code": "string (required)",
  "label": "string (required)", 
  "notes": "string (optional)",
  "position": "integer (required)",
  "elements": [...]
}
```

## Element Schema:
```json
{
  "code": "string (required)",
  "label": "string (required)",
  "type": "CHOICE|OPEN_END|BREAK_PAGE|SCREENER|COUNTRY_DROPDOWN|AGE_ORI|S105_RATING_FAMILIARITY|GEOGRAPHIC_AREA_REGION|PULSE_FILTER|YES_NO|EDUCATION_STANDARD|INCOME_STANDARD",
  "position": "integer (required)",
  "notes": "string (optional)",
  "help_text": "string (optional)",
  "variables": [...],
  "columns": [...]
}
```

## Variable Schema:
```json
{
  "code": "string (required)",
  "label": "string (required)",
  "position": "integer (required)",
  "notes": "string (optional)"
}
```

## Column Schema:
```json
{
  "code": "integer (required)",
  "label": "string (required)", 
  "position": "integer (required)",
  "notes": "string (optional)"
}
```

# Content Patterns

## Sections:
- Format: "# Section {code} - {label}" or "# {label}"
- Extract code and label, preserve all text

## Elements:
- Format: "**{code}**[{type}]: {label content}"
- Label can be multi-line until "===" delimiter
- Type defaults to "CHOICE" if not specified
- Programming notes come after "==="

## Variables (in tables):
- Format: | code | label | notes |
- Usually in "Value Code" / "Value Label" tables

## Columns (in grids):
- Format: | code | label | 
- Usually in scale questions (1-7, etc.)

# Processing Rules

1. **Preserve exact text**: Keep all codes and labels exactly as written
2. **Handle fragments**: Chunks may contain partial content
3. **Maintain structure**: Respect hierarchical relationships
4. **Extract completely**: Only extract content that appears complete
5. **Handle continuations**: Accumulate content across chunks when needed

# Output Format

Return JSON with this structure:
```json
{
  "chunk_type": "section_start|element_start|element_content|table_content|continuation|complete",
  "extracted_sections": [...],
  "extracted_elements": [...], 
  "partial_content": "string if chunk appears incomplete",
  "requires_continuation": boolean,
  "confidence": 0.0-1.0
}
```

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
- **AGE_STANDARD**: A question that asks for the respondent's age, with specific ranges and recoding questions. Normally with match with a question with the code `AGE_ORI`
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
| `**cQCA\\_Language\\_CA** [CHOICE]:\r\n\r\nWould you prefer to complete the survey in English or French?\r\n===\r\nPr\u00E9f\u00E9rez\\-vous r\u00E9pondre \u00E0 ce questionnaire en\r\nAnglais ou en Fran\u00E7ais?\r\n\r\n* **SINGLE\r\n ANSWER**\r\n* **Prog:\r\n show default instruction text side\\-by\\-side in both English\r\n (code\\=1000\\) and French (Code\\=3000\\).**\r\n\r\n| **Value** **Code** | **Value** **Label** |\r\n| 1 | English\/Anglais |\r\n| 2 | French\/Fran\u00E7ais |` | `{"code": "cQCA_Language_CA", "label": "nWould you prefer to complete the survey in English or French?\r\n\r\nPr\u00E9f\u00E9rez\\-vous r\u00E9pondre \u00E0 ce questionnaire en\r\nAnglais ou en Fran\u00E7ais?\r\n\r\n", "type": "CHOICE", "position": 1, "variables": [{"code": "1", "label": "English/Anglais", "position": 1}, {"code": "2", "label": "French/Fran\u00E7ais", "position": 2}], "help_text": null, notes: "* **SINGLE ANSWER**\n* **Prog: show default instruction text side-by-side in both English (code=1000) and French (Code=3000).**"}` |
| `**Gender**[CHOICE]:What is your gender?\r\n===\r\n* **SINGLE\r\n ANSWER**\r\n\r\n| **Value****Code** | **Value****Label** |\r\n| 1 | Male |\r\n| 2 | Female |` | {"code":"Gender", "type": "CHOICE", "label": "What is your gender?", "variables": [{"code":"1", "label"Male"}, {"code":"2", "label"Female"}]}`|
| `**AGE\\_ORI**[AGE_STANDARD]:What is your age as of today?\r\n===\r\n* **Programmer:** **Numeric\r\n open ended**\r\n\r\n    + **SHOW\r\n     AS A SINGLE SELECT RANGE FOR RUSSIA (AGE\\_RU). RECODE AS LISTED\r\n     BELOW**\r\n\r\n**Range for Russia:**\r\n\r\n* **Use\r\n Select One Instruction Text if RU:**\u0412\u044B\u0431\u0435\u0440\u0438\u0442\u0435\r\n \u043E\u0434\u0438\u043D \u0432\u0430\u0440\u0438\u0430\u043D\u0442 \u043E\u0442\u0432\u0435\u0442\u0430.\r\n\r\n| **Value Code** | **Value Label** | **Notes** |\r\n| 0 | Under 18 | Terminate |\r\n| 1 | 18\\-24 | RECODE TO GENERATION \\= 2 and AGE \\= 1 |\r\n| 2 | 25\\-34 | RECODE TO GENERATION \\= 3 and AGE \\= 2 |\r\n| 3 | 35\\-40 | RECODE TO GENERATION \\= 3 and AGE \\= 3 |\r\n| 4 | 41\\-44 | RECODE TO GENERATION \\= 4 and AGE \\= 3 |\r\n| 5 | 45\\-55 | RECODE TO GENERATION \\= 4 and AGE \\= 4 |\r\n| 6 | 56\\-64 | RECODE TO GENERATION \\= 5 and AGE \\= 4 |\r\n| 7 | 65\\+ | RECODE TO GENERATION \\= 6 and AGE \\= 5 |\r\n\r\n* **Programmer:\r\n Valid** **Range\r\n \u201C0\\-115\u201D**\r\n\r\n**Terminate:** **if\r\nAGE\\_ORI is below 18**\r\n\r\n**Age \\[HIDDEN \u2013 recode Age from question\r\nAGE\\_ORI]:**\r\n\r\n| **Value Code** | **Value Label** | **Notes** |\r\n| 0 | Under 18 | Terminate |\r\n| 1 | 18\\-24 |  |\r\n| 2 | 25\\-34 |  |\r\n| 3 | 35\\-44 |  |\r\n| 4 | 45\\-64 |  |\r\n| 5 | 65\\+ |  |\r\n\r\n**GENERATION \\[HIDDEN \u2013 recode Generation\r\nfrom question AGE\\_ORI]:**\r\n\r\n| **Value Code** | **Value Label** | **Notes** |\r\n| 1 | Under 18 | Terminate |\r\n| 2 | 18\\-25 | **GenZ** |\r\n| 3 | 26\\-40 | **Millennials** |\r\n| 4 | 41\\-55 | **GenX** |\r\n| 5 | 56\\-64 | **Baby Boomers** |\r\n| 6 | 65\\+ | **Older Baby Boomers \/ Silent Generation** |\r\n\r\n**\\[PN: IF AUSTRALIA (CODE\\=26\\) OR NEW ZEALAND\r\n(CODE\\=198\\): SHOW POSTCODE AND REGION\\_C ON SAME SCREEN]**\r\n\r\n**PN: ASK POSTCODE IF AUSTRALIA (CODE\\=26\\) OR\r\nNEW ZEALAND (CODE\\=198\\)**` | {"code":"AGE_ORI", "type": "AGE_ORI", "label": "What is your age as of today?"}`|
| `**Q215**[CHOICE]: The next questions concern\r\na number of different attitudes or behaviors you might have toward a\r\ncompany.\r\n\r\nPlease consider how well they describe your attitude toward**\\<b\\>{\\#Company1}\\<\/b\\>**.\r\n\r\nPlease select a number from 1 to 7 where \u201C1\u201D means \u201CI strongly\r\ndisagree\u201D and \u201C7\u201D means \u201CI strongly agree\u201D.\r\n===\r\n* **SINGLE\r\n ANSWER EACH ITEM.**\r\n* **RANDOMIZE.**\r\n* **PLEASE\r\n DISPLAY SCALE RESPONSE (I strongly agree 1, 2, \u2026, Not sure) ALSO\r\n AT THE BOTTOM OF THE GRID**\r\n* **PN:\r\n if respondent qualifies to rate Company 2, use variable naming\r\n \u201CQ216\u201D**\r\n* **PN:\r\n if respondent qualifies to rate Company 3, use variable naming\r\n \u201CQ217\u201D**\r\n\r\n| **Variable Name** | **Variable Label** | **NOTES** |\r\n| Q215\\_3 | I would say something positive about **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_4 | I would give the benefit of the doubt to **\\<b\\>{\\#Company1}\\<\/b\\>** if the company was facing a crisis |  |\r\n| Q215\\_5 | If **\\<b\\>{\\#Company1}\\<\/b\\>** was faced with a product  or service problem, I would trust them to do the right thing |  |\r\n| Q215\\_6 | **SHOW  DEFAULT TEXT:**If I had the opportunity, I would buy the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>** **UNLESS  AUSTRALIA (CODE\\=26\\) AND ONE OF THE FOLLOWING COMPANIES:*** **AustralianSuper  (COMPANY CODE \\= 260622\\)** * **HESTA  (COMPANY CODE \\= 260674\\)** * **Hostplus  (COMPANY CODE \\= 260675\\)** * **Rest  Super (COMPANY CODE \\= 260684\\)** * **QSuper  (COMPANY CODE \\= 260788\\)** * **Aware  Super (COMPANY CODE \\= 260789\\)** * **Australian  Retirement Trust (COMPANY CODE \\= 260826\\)** * **UniSuper  (COMPANY CODE \\= 260854\\)** **SHOW TEXT:**If I had the opportunity, I would be a  member of **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_7 | **SHOW  DEFAULT TEXT:**If I had the opportunity, I would invest in **\\<b\\>{\\#Company1}\\<\/b\\>** **UNLESS  AUSTRALIA (CODE\\=26\\) AND ONE OF THE FOLLOWING COMPANIES:*** **AustralianSuper  (COMPANY CODE \\= 260622\\)** * **HESTA  (COMPANY CODE \\= 260674\\)** * **Hostplus  (COMPANY CODE \\= 260675\\)** * **Rest  Super (COMPANY CODE \\= 260684\\)** * **QSuper  (COMPANY CODE \\= 260788\\)** * **Aware  Super (COMPANY CODE \\= 260789\\)** * **Australian  Retirement Trust (COMPANY CODE \\= 260826\\)** * **UniSuper  (COMPANY CODE \\= 260854\\)** **SHOW TEXT:**I would recommend to someone to invest their  super with **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_8 | If I had the opportunity, I would work for **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n| Q215\\_10 | I would recommend the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>** |  |\r\n\r\n* **Programmer:\r\n Show scale numbers, except on \u201CNot sure\u201D**\r\n\r\n| **Value Code** | **Value Label** |\r\n| 1 | I strongly disagree 1 |\r\n| 2 | 2 |\r\n| 3 | 3 |\r\n| 4 | 4 |\r\n| 5 | 5 |\r\n| 6 | 6 |\r\n| 7 | I strongly agree 7 |\r\n| 99 | Not sure |` | {"code":"Q215", "type": "AGE_ORI", "label": "The next questions concern\r\na number of different attitudes or behaviors you might have toward a\r\ncompany.\r\n\r\nPlease consider how well they describe your attitude toward**\\<b\\>{\\#Company1}\\<\/b\\>**.\r\n\r\nPlease select a number from 1 to 7 where \u201C1\u201D means \u201CI strongly\r\ndisagree\u201D and \u201C7\u201D means \u201CI strongly agree\u201D.", "options": {"randomize_variables":true, "columns": [{"code":"1", "label":"I strongly disagree 1", ....}]}, "variables":[{"code":"3","label":"I would say something positive about **\\<b\\>{\\#Company1}\\<\/b\\>", ..., "code":"6","label":"If I had the opportunity, I would buy the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>", notes: "**SHOW  DEFAULT TEXT:**If I had the opportunity, I would buy the products\/services of **\\<b\\>{\\#Company1}\\<\/b\\>** **UNLESS  AUSTRALIA (CODE\\=26\\) AND ONE OF THE FOLLOWING COMPANIES:*** **AustralianSuper  (COMPANY CODE \\= 260622\\)** * **HESTA  (COMPANY CODE \\= 260674\\)** * **Hostplus  (COMPANY CODE \\= 260675\\)** * **Rest  Super (COMPANY CODE \\= 260684\\)** * **QSuper  (COMPANY CODE \\= 260788\\)** * **Aware  Super (COMPANY CODE \\= 260789\\)** * **Australian  Retirement Trust (COMPANY CODE \\= 260826\\)** * **UniSuper  (COMPANY CODE \\= 260854\\)** **SHOW TEXT:**If I had the opportunity, I would be a  member of **\\<b\\>{\\#Company1}\\<\/b\\>**"}], "columns": [{"code":"1", "label":"I strongly disagree 1", ....}]}`|

** In general any information that does not fit in the schema fields, must me placed in `notes` at section, element or variable level.***

### Text format rules
#### Sections
Section have format: `Section {code} - {label}`
#### Elements
Element have format:
```
**{code}**[TYPE]: {label multi line text}
{label multi line text}
{label multi line text}
===
```
Where `===` is the delimiter of the end of the label. After `===` you can found element options, programer notes (notes) and table with variables or columns.
#### Variables
Variables are defined in tables with format:
```
| **Value Code** | **Value Label** | **Notes** |
| 0 | Under 18 | Terminate |
```
Where `Value Code` is the variable code, `Value Label` is the variable label and `Notes` are additional information about the variable.
`Value Code` column could be named as `Code`, `Value Code`, `Variable Code` or similar, and `Value Label` column could be named as `Label`, `Value Label`, `Variable Label` or similar.
If `Value Code` have format `{question_code}_{variable_code}` it means that this variable is a part of a question with the code `{question_code}` and the variable code is `{variable_code}`, keep only `{variable_code}` in the output.
#### Columns
Columns are defined in tables with format:
```
| **Value Code** | **Value Label** |
| 1 | I strongly disagree 1 |
```
Where `Value Code` is the column code and `Value Label` is the column label.


**Always respond with valid JSON. Extract only what you can identify with confidence.**"""

    def create_chunk_prompt(self, chunk_content: str, chunk_index: int, total_chunks: int, context: Dict[str, Any]) -> str:
        """Create the prompt for processing a specific chunk."""
        return f"""# Chunk Processing Request

{SYSTEM_PROMPT}

## Context
- Chunk {chunk_index + 1} of {total_chunks}
- Previous chunk type: {context.get('last_chunk_type', 'unknown')}
- Current section: {context.get('current_section_code', 'none')}
- Current element: {context.get('current_element_code', 'none')}
- Accumulated content length: {len(context.get('accumulated_content', ''))}

## Accumulated Content (if any)
```
{context.get('accumulated_content', '')}
```

## Current Chunk Content
```
{chunk_content}
```

## Instructions
1. Analyze the chunk content for questionnaire structure
2. Determine if this is a section start, element start, continuation, or complete content
3. Extract any complete sections, elements, variables, or columns
4. Indicate if content appears incomplete and needs continuation
5. Provide confidence level for extractions

Process this chunk and return structured JSON following the schema definitions."""

    def get_system_prompt(self) -> str:
        """Get the system prompt."""
        return self.system_prompt
