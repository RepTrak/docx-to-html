"""
Document conversion module for the conversion pipeline.
"""

import streamlit as st
import tempfile
import traceback
from pathlib import Path

from .state_manager import ConversionStateManager
from ....conversion.docx_converter import DocxToMarkdownConverter, ConversionResult


class DocumentConversionModule:
    """Handles document conversion functionality."""
    
    def render(self):
        """Render the document conversion step."""
        st.subheader("📄 Document Conversion")
        
        if not ConversionStateManager.is_step_complete('upload'):
            st.warning("⚠️ Please upload a file first")
            return
        
        state = ConversionStateManager.get_state()
        file_type = state['file_type']
        
        if file_type == 'md':
            self._handle_markdown_file()
        elif file_type == 'docx':
            self._handle_docx_file()
        
        # Display conversion results
        if ConversionStateManager.is_step_complete('conversion'):
            self._display_conversion_results()
    
    def _handle_markdown_file(self):
        """Handle markdown file reading."""
        if st.button("📖 Read Markdown File", key="read_md"):
            try:
                state = ConversionStateManager.get_state()
                content = state['uploaded_file'].getvalue().decode('utf-8')
                
                ConversionStateManager.update_state({
                    'markdown_content': content,
                    'conversion_complete': True,
                    'conversion_result': ConversionResult(
                        success=True,
                        markdown_content=content,
                        original_file_path=state['filename'],
                        conversion_stats={
                            'markdown_length': len(content),
                            'markdown_lines': len(content.split('\n')),
                            'markdown_words': len(content.split()),
                            'conversion_tool': 'Direct Read'
                        }
                    )
                })
                
                st.success("✅ Markdown file read successfully!")
                
            except Exception as e:
                st.error(f"❌ Error reading markdown file: {str(e)}")
    
    def _handle_docx_file(self):
        """Handle DOCX file conversion."""
        if st.button("🔄 Convert DOCX to Markdown", key="convert_docx"):
            with st.spinner("Converting DOCX to Markdown..."):
                try:
                    state = ConversionStateManager.get_state()
                    
                    # Save uploaded file temporarily
                    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp_file:
                        tmp_file.write(state['uploaded_file'].getvalue())
                        tmp_path = Path(tmp_file.name)
                    
                    # Convert using DocxToMarkdownConverter
                    converter = DocxToMarkdownConverter(verbose=True)
                    result = converter.convert_file(tmp_path)
                    
                    # Clean up temp file
                    tmp_path.unlink()
                    
                    if result.success:
                        ConversionStateManager.update_state({
                            'markdown_content': result.markdown_content,
                            'conversion_complete': True,
                            'conversion_result': result
                        })
                        
                        st.success("✅ DOCX converted to Markdown successfully!")
                    else:
                        st.error(f"❌ Conversion failed: {result.error_message}")
                        
                except Exception as e:
                    st.error(f"❌ Error during conversion: {str(e)}")
                    st.code(traceback.format_exc())
    
    def _display_conversion_results(self):
        """Display conversion results and statistics."""
        state = ConversionStateManager.get_state()
        result = state['conversion_result']
        
        with st.expander("📊 Conversion Statistics", expanded=False):
            if result.conversion_stats:
                col1, col2, col3, col4 = st.columns(4)
                stats = result.conversion_stats
                
                with col1:
                    st.metric("Content Length", f"{stats.get('markdown_length', 0):,} chars")
                with col2:
                    st.metric("Lines", f"{stats.get('markdown_lines', 0):,}")
                with col3:
                    st.metric("Words", f"{stats.get('markdown_words', 0):,}")
                with col4:
                    st.metric("Tool Used", stats.get('conversion_tool', 'Unknown'))
        
        # Download button
        content = state['markdown_content']
        filename = state['filename']
        
        # Generate download filename
        base_name = Path(filename).stem
        download_filename = f"{base_name}_converted.md"
        
        st.download_button(
            label="📥 Download Markdown",
            data=content,
            file_name=download_filename,
            mime="text/markdown",
            help="Download the converted markdown content"
        )
        
        with st.expander("📝 Markdown Preview", expanded=False):
            if content:
                st.text_area("Markdown Content", content[:2000] + "..." if len(content) > 2000 else content, height=300, disabled=True)
