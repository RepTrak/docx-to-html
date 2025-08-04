"""
Documentation page displaying README content.
"""

import streamlit as st
from pathlib import Path
from .base import BasePage


class DocumentationPage(BasePage):
    """Documentation page displaying README content."""
    
    def __init__(self):
        self.title = "📖 Documentation"
    
    def render(self):
        """Render the documentation page."""
        st.title(self.title)
        
        # Read and display README content
        readme_path = Path(__file__).parent.parent.parent.parent / "README_PM_DOCS_TO_SCHEMA.md"
        
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read()
                
                st.markdown(readme_content)
                
            except Exception as e:
                st.error(f"Error reading README file: {str(e)}")
                st.info("README file not found. Please check if README_PM_DOCS_TO_SCHEMA.md exists in the project root.")
        else:
            st.warning("README_PM_DOCS_TO_SCHEMA.md not found")
            st.info("This page should display the project documentation from README_PM_DOCS_TO_SCHEMA.md")
            
            # Placeholder content
            st.markdown("""
            ## DOCX to Schema Converter
            
            This application converts DOCX questionnaire files to structured JSON schemas.
            
            ### Process Overview:
            1. **Upload**: Upload a DOCX or Markdown file
            2. **Convert**: DOCX files are converted to Markdown using MarkItDown
            3. **Split**: Content is split into chunks using delimiter-based strategy
            4. **Process**: Each chunk is processed by LLM to extract structured data
            5. **Generate**: Final JSON schema is created following the survey model
            
            ### Features:
            - Multiple file format support (DOCX, Markdown)
            - Intelligent content splitting with fallback strategies
            - LLM-powered content extraction with multiple provider support
            - Real-time monitoring and debugging
            - Comprehensive statistics and error reporting
            - JSON schema generation following questionnaire standards
            
            Use the **File Conversion** page to start processing your documents.
            """)
