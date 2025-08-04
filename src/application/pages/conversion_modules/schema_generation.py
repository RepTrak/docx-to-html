"""
Schema generation module for the conversion pipeline.
"""

import streamlit as st
import traceback

from .state_manager import ConversionStateManager
from ....converter.markdown_schema_converter import MarkdownToSchemaConverter, ProcessingStats


class SchemaGenerationModule:
    """Handles schema generation functionality."""
    
    def render(self):
        """Render the schema generation step."""
        st.subheader("🧠 Schema Generation")
        
        if not ConversionStateManager.is_step_complete('splitting'):
            st.warning("⚠️ Please complete content splitting first")
            return
        
        # LLM configuration
        provider, model, temperature = self._render_llm_config()
        
        # Progress tracking
        if 'schema_progress' not in st.session_state:
            st.session_state.schema_progress = None
        
        if st.button("🧠 Generate Schema", key="generate_schema"):
            self._perform_schema_generation(provider, model, temperature)
        
        # Display schema generation results
        if ConversionStateManager.is_step_complete('schema'):
            self._display_schema_results()
    
    def _render_llm_config(self):
        """Render LLM configuration options."""
        with st.expander("⚙️ LLM Configuration", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                provider = st.selectbox(
                    "LLM Provider",
                    options=["openai", "anthropic"],
                    index=0
                )
            
            with col2:
                models = {
                    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
                    "anthropic": ["claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022"]
                }
                model = st.selectbox(
                    "Model",
                    options=models[provider],
                    index=0
                )
            
            with col3:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1
                )
        
        return provider, model, temperature
    
    def _progress_callback(self, stats: ProcessingStats):
        """Update progress in real-time."""
        if st.session_state.schema_progress:
            progress = stats.processed_chunks / stats.total_chunks if stats.total_chunks > 0 else 0
            st.session_state.schema_progress.progress(progress, text=f"Processing chunk {stats.processed_chunks}/{stats.total_chunks}")
    
    def _perform_schema_generation(self, provider: str, model: str, temperature: float):
        """Perform the schema generation operation."""
        with st.spinner("Generating schema using LLM..."):
            try:
                # Create progress bar
                st.session_state.schema_progress = st.progress(0, text="Initializing...")
                
                # Initialize converter
                converter = MarkdownToSchemaConverter(
                    model=model,
                    provider=provider,
                    temperature=temperature,
                    verbose=True,
                    progress_callback=self._progress_callback
                )
                
                # Convert chunks to schema
                state = ConversionStateManager.get_state()
                split_result = state['split_result']
                survey_schema = converter.convert_from_split_result(split_result)
                
                # Get final stats
                final_stats = converter.get_processing_stats()
                
                ConversionStateManager.update_state({
                    'schema_result': survey_schema,
                    'processing_stats': final_stats,
                    'schema_complete': True
                })
                
                # Clear progress bar
                st.session_state.schema_progress = None
                
                st.success(f"✅ Schema generated successfully! Found {len(survey_schema.sections)} sections")
                
            except Exception as e:
                st.error(f"❌ Error during schema generation: {str(e)}")
                st.code(traceback.format_exc())
                # Clear progress bar on error
                st.session_state.schema_progress = None
    
    def _display_schema_results(self):
        """Display schema generation results and statistics."""
        state = ConversionStateManager.get_state()
        stats = state['processing_stats']
        survey = state['schema_result']
        
        with st.expander("📊 Processing Statistics", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("LLM Calls", stats.llm_calls)
            with col2:
                st.metric("Total Tokens", f"{sum(stats.total_tokens.values()):,}")
            with col3:
                st.metric("Processing Time", f"{stats.processing_time:.2f}s")
            with col4:
                st.metric("Sections Created", stats.sections_created)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Elements Created", stats.elements_created)
            with col2:
                st.metric("Variables Created", stats.variables_created)
            with col3:
                st.metric("Columns Created", stats.columns_created)
        
        # Errors and warnings
        if stats.errors:
            with st.expander("⚠️ Errors", expanded=False):
                for error in stats.errors:
                    st.error(error)
        
        if stats.warnings:
            with st.expander("⚠️ Warnings", expanded=False):
                for warning in stats.warnings:
                    st.warning(warning)
        
        # Schema preview
        with st.expander("🔍 Schema Preview", expanded=True):
            st.write(f"**Survey with {len(survey.sections)} sections:**")
            
            for i, section in enumerate(survey.sections):
                with st.container():
                    st.write(f"**Section {i+1}: {section.code}**")
                    st.write(f"Label: {section.label}")
                    if section.elements:
                        st.write(f"Elements: {len(section.elements)}")
                        
                        # Show first few elements
                        for j, element in enumerate(section.elements[:3]):
                            st.write(f"  - {element.code} ({element.type}): {element.label[:50]}...")
                        
                        if len(section.elements) > 3:
                            st.write(f"  ... and {len(section.elements) - 3} more elements")
                    st.divider()
