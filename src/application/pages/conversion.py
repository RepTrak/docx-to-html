"""
Main conversion page with file upload and processing pipeline.
"""

import streamlit as st
from .base import BasePage
from .conversion_modules import (
    ConversionStateManager,
    FileUploadModule,
    DocumentConversionModule,
    ContentSplittingModule,
    SchemaGenerationModule,
    ResultsExportModule
)


class ConversionPage(BasePage):
    """Main conversion page with file upload and processing pipeline."""
    
    def __init__(self):
        self.title = "🔄 File Conversion Pipeline"
        
        # Initialize modules
        self.file_upload = FileUploadModule()
        self.document_conversion = DocumentConversionModule()
        self.content_splitting = ContentSplittingModule()
        self.schema_generation = SchemaGenerationModule()
        self.results_export = ResultsExportModule()
    
    def render(self):
        """Render the conversion page."""
        st.title(self.title)
        
        # Initialize session state
        ConversionStateManager.initialize_state()
        
        # File upload section
        self.file_upload.render()
        
        # Processing pipeline
        if ConversionStateManager.is_step_complete('upload'):
            self._render_conversion_pipeline()
    
    def _render_conversion_pipeline(self):
        """Render the main conversion pipeline."""
        st.header("⚙️ Conversion Pipeline")
        
        # Create 2-column layout
        col_steps, col_results = st.columns([2, 3])
        
        with col_steps:
            st.subheader("🔧 Processing Steps")
            
            # Pipeline steps
            steps = [
                ("📄", "Document Conversion", "document_conversion", self.document_conversion.render),
                ("✂️", "Content Splitting", "content_splitting", self.content_splitting.render), 
                ("🧠", "Schema Generation", "schema_generation", self.schema_generation.render)
            ]
            
            # Initialize active step in session state
            if 'active_step' not in st.session_state:
                st.session_state.active_step = 'document_conversion'
            
            # Render each step with expandable sections
            for icon, name, step_key, render_func in steps:
                with st.expander(f"{icon} {name}", expanded=(st.session_state.active_step == step_key)):
                    if st.button(f"Activate {name}", key=f"btn_{step_key}"):
                        st.session_state.active_step = step_key
                        st.rerun()
                    
                    if st.session_state.active_step == step_key:
                        render_func()
        
        with col_results:
            st.subheader("📊 Results & Export")
            # Results are always visible
            self.results_export.render()
