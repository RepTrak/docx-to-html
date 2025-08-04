"""
Results export module for the conversion pipeline.
"""

import streamlit as st
import json
from datetime import datetime

from .state_manager import ConversionStateManager


class ResultsExportModule:
    """Handles results display and export functionality."""
    
    def render(self):
        """Render the results export step."""
        
        if not ConversionStateManager.is_step_complete('schema'):
            st.warning("⚠️ Please complete schema generation first")
            return
        
        state = ConversionStateManager.get_state()
        survey = state['schema_result']
        stats = state['processing_stats']
        
        # Export options
        self._render_export_buttons(survey, stats)
        
        # Summary report
        self._render_summary_report(survey, stats)
        
        # Reset button
        if st.button("🔄 Process Another File", key="reset"):
            ConversionStateManager.reset_state()
            st.rerun()
    
    def _render_export_buttons(self, survey, stats):
        """Render export download buttons."""
        col1, col2 = st.columns(2)
        
        with col1:
            # Download JSON schema
            schema_json = json.dumps(survey.model_dump(), indent=2, ensure_ascii=False)
            st.download_button(
                label="📄 Download JSON Schema",
                data=schema_json,
                file_name=f"schema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            # Download processing stats
            stats_json = json.dumps({
                'total_chunks': stats.total_chunks,
                'processed_chunks': stats.processed_chunks,
                'sections_created': stats.sections_created,
                'elements_created': stats.elements_created,
                'variables_created': stats.variables_created,
                'columns_created': stats.columns_created,
                'llm_calls': stats.llm_calls,
                'total_tokens': stats.total_tokens,
                'processing_time': stats.processing_time,
                'errors': stats.errors,
                'warnings': stats.warnings
            }, indent=2)
            
            st.download_button(
                label="📊 Download Statistics",
                data=stats_json,
                file_name=f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    def _render_summary_report(self, survey, stats):
        """Render the processing summary report."""
        with st.expander("📋 Processing Summary", expanded=True):
            state = ConversionStateManager.get_state()
            
            st.markdown(f"""
            ### Conversion Summary
            
            **File Processed:** `{state['filename']}`
            
            **Pipeline Results:**
            - ✅ Document conversion completed
            - ✅ Content split into {len(state['split_result'].chunks)} chunks
            - ✅ Schema generation completed
            
            **Final Output:**
            - 🏷️ **{len(survey.sections)} sections** created
            - ❓ **{stats.elements_created} elements** extracted
            - 📊 **{stats.variables_created} variables** identified
            - 📈 **{stats.columns_created} columns** processed
            
            **Processing Stats:**
            - 🤖 **{stats.llm_calls} LLM calls** made
            - 🔤 **{sum(stats.total_tokens.values()):,} tokens** used
            - ⏱️ **{stats.processing_time:.2f} seconds** total time
            """)
