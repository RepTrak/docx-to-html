"""
File upload module for the conversion pipeline.
"""

import streamlit as st
from .state_manager import ConversionStateManager


class FileUploadModule:
    """Handles file upload functionality."""
    
    def render(self):
        """Render the file upload section."""
        st.header("📁 File Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a file to convert",
            type=['docx', 'md'],
            help="Upload a DOCX questionnaire or Markdown file for conversion"
        )
        
        if uploaded_file is not None:
            st.success(f"File uploaded: {uploaded_file.name}")
            
            # Store file info
            ConversionStateManager.update_state({
                'uploaded_file': uploaded_file,
                'file_uploaded': True,
                'filename': uploaded_file.name,
                'file_type': uploaded_file.name.split('.')[-1].lower()
            })
            
            # File info
            with st.expander("📋 File Information", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Filename", uploaded_file.name)
                with col2:
                    st.metric("File Type", uploaded_file.type)
                with col3:
                    st.metric("File Size", f"{len(uploaded_file.getvalue())} bytes")
