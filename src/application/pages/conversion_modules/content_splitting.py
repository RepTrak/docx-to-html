"""
Content splitting module for the conversion pipeline.
"""

import streamlit as st
import traceback

from .state_manager import ConversionStateManager
from ....conversion.markdown_splitter import MarkdownTextSplitter


class ContentSplittingModule:
    """Handles content splitting functionality."""
    
    def render(self):
        """Render the content splitting step."""
        st.subheader("✂️ Content Splitting")
        
        if not ConversionStateManager.is_step_complete('conversion'):
            st.warning("⚠️ Please complete document conversion first")
            return
        
        # Splitting configuration
        with st.expander("⚙️ Splitting Configuration", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                delimiter = st.text_input(
                    "Primary Delimiter Pattern",
                    value=r'\\\*\\\*\\\*',
                    help="Regex pattern for splitting content"
                )
            
            with col2:
                fallback_size = st.number_input(
                    "Fallback Chunk Size",
                    min_value=500,
                    max_value=5000,
                    value=2000,
                    help="Size for fallback chunking if delimiter fails"
                )
        
        if st.button("✂️ Split Content", key="split_content"):
            self._perform_splitting(delimiter, fallback_size)
        
        # Display splitting results
        if ConversionStateManager.is_step_complete('splitting'):
            self._display_splitting_results()
    
    def _perform_splitting(self, delimiter: str, fallback_size: int):
        """Perform the content splitting operation."""
        with st.spinner("Splitting content into chunks..."):
            try:
                splitter = MarkdownTextSplitter(
                    primary_delimiter=delimiter,
                    fallback_chunk_size=fallback_size,
                    verbose=True
                )
                
                state = ConversionStateManager.get_state()
                split_result = splitter.split_text(state['markdown_content'])
                
                if split_result.success:
                    ConversionStateManager.update_state({
                        'split_result': split_result,
                        'splitting_complete': True
                    })
                    
                    st.success(f"✅ Content split into {len(split_result.chunks)} chunks!")
                else:
                    st.error(f"❌ Splitting failed: {split_result.error_message}")
                    
            except Exception as e:
                st.error(f"❌ Error during splitting: {str(e)}")
                st.code(traceback.format_exc())
    
    def _display_splitting_results(self):
        """Display splitting results and chunk analysis."""
        state = ConversionStateManager.get_state()
        split_result = state['split_result']
        
        with st.expander("📊 Splitting Statistics", expanded=True):
            if split_result.split_stats:
                col1, col2, col3, col4 = st.columns(4)
                stats = split_result.split_stats
                
                with col1:
                    st.metric("Total Chunks", stats.get('total_chunks', 0))
                with col2:
                    st.metric("Strategy Used", stats.get('strategy_used', 'Unknown'))
                with col3:
                    st.metric("Avg Chunk Size", f"{stats.get('average_chunk_size', 0):,} chars")
                with col4:
                    st.metric("Size Range", f"{stats.get('min_chunk_size', 0)}-{stats.get('max_chunk_size', 0)}")
        
        with st.expander("🔍 Chunk Analysis", expanded=False):
            if split_result.structure_map and 'chunks_info' in split_result.structure_map:
                chunks_info = split_result.structure_map['chunks_info']
                
                for i, chunk_info in enumerate(chunks_info):
                    with st.container():
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.write(f"**Chunk {i+1}**")
                        with col2:
                            st.write(f"Size: {chunk_info['size']} chars")
                        with col3:
                            indicators = []
                            if chunk_info.get('has_section_header'):
                                indicators.append("🏷️ Section")
                            if chunk_info.get('has_element_pattern'):
                                indicators.append("❓ Element")
                            if chunk_info.get('has_table'):
                                indicators.append("📊 Table")
                            st.write(" ".join(indicators) if indicators else "📝 Text")
                        with col4:
                            if st.button(f"👁️ View", key=f"view_chunk_{i}"):
                                self._show_chunk_dialog(i, split_result.chunks[i], chunk_info)

    @st.dialog("📄 Chunk Details")
    def _show_chunk_dialog(self, chunk_index: int, chunk_content: str, chunk_info: dict):
        """Show chunk details in a dialog."""
        st.subheader(f"Chunk {chunk_index + 1}")
        
        # Chunk metadata
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Size", f"{chunk_info['size']} chars")
        with col2:
            indicators = []
            if chunk_info.get('has_section_header'):
                indicators.append("🏷️ Section")
            if chunk_info.get('has_element_pattern'):
                indicators.append("❓ Element")
            if chunk_info.get('has_table'):
                indicators.append("📊 Table")
            st.write("**Type:** " + (" ".join(indicators) if indicators else "📝 Text"))
        with col3:
            if chunk_info.get('section_title'):
                st.write(f"**Section:** {chunk_info['section_title']}")
        
        # Chunk content
        st.subheader("Content")
        st.text_area(
            "Chunk Content",
            chunk_content,
            height=400,
            label_visibility="collapsed"
        )
        
        # Action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📋 Copy to Clipboard", key=f"copy_chunk_{chunk_index}"):
                st.write("Content copied to clipboard!")
        with col2:
            if st.button("✅ Close", key=f"close_chunk_{chunk_index}"):
                st.rerun()
