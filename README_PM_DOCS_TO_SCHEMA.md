# Word Files to ReProject HUB Schema Converter

This is a "toolbox" for internal human operations.

## DOCX Format

### Sections

Must be `title` word style and format `Section XXXX - label`

### Questionnaire Elements

Any element in a section - questions, screener texts, etc must follow some concrete conventions

- Codes must be `<bold>Q_CODE [TYPE]</bold>:`. *By default all elements are `CHOICE` type if the type is not set*
- Question text/label must be next to the code
- `===` string tell the system the end question/element **text**
- `***` string tell the system the end of the question/element

```WORDFILE
<bold>Q_CODE [TYPE]</bold>: Question text

with multiline is possible
delimiting with

===
***

<bold>Q_CODE [TYPE]</bold>: Question text

with multiline is possible
delimiting with

===

- list with
- options
- or

PROGRAMER NOTES

VARIABLES TABLE
| CODE | LABEL | NOTES |
| 1    | foo   | ...   |

COLUMNS TABLE
| CODE | LABEL | NOTES |
| 1    | foo   | ...   |

***
```

### Markdown conversion

From the previous example the expected markdown output is:
```markdown
***

**Q_CODE [TYPE]**: Question text

with multiline is possible
delimiting with

===

- list with
- options
- or

PROGRAMER NOTES

VARIABLES TABLE
| CODE | LABEL | NOTES |
| 1    | foo   | ...   |


COLUMNS TABLE
| CODE | LABEL | NOTES |
| 1    | foo   | ...   |

***
```
