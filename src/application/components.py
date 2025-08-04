"""
Reusable Streamlit components for the DOCX to Schema application.
"""

import streamlit as st
from typing import Dict, Any, List, Optional
from datetime import datetime


class ProgressMonitor:
    """Real-time progress monitoring component."""
    
    def __init__(self, title: str = "Processing"):
        self.title = title
        self.progress_bar = None
        self.status_text = None
        self.start_time = None
    
    def start(self, total_steps: int):
        """Initialize progress monitoring."""
        self.start_time = datetime.now()
        self.progress_bar = st.progress(0, text=f"{self.title}: Initializing...")
        self.status_text = st.empty()
    
    def update(self, current_step: int, total_steps: int, message: str = ""):
        """Update progress."""
        if self.progress_bar:
            progress = current_step / total_steps if total_steps > 0 else 0
            self.progress_bar.progress(progress, text=f"{self.title}: {message}")
            
            if self.status_text and self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds()
                self.status_text.text(f"Step {current_step}/{total_steps} • {elapsed:.1f}s elapsed")
    
    def complete(self, message: str = "Complete"):
        """Mark as complete."""
        if self.progress_bar:
            self.progress_bar.progress(1.0, text=f"{self.title}: {message}")
        if self.status_text and self.start_time:
            total_time = (datetime.now() - self.start_time).total_seconds()
            self.status_text.success(f"✅ {message} in {total_time:.1f}s")


class StatsDisplay:
    """Component for displaying statistics and metrics."""
    
    @staticmethod
    def display_conversion_stats(stats: Dict[str, Any], title: str = "Conversion Statistics"):
        """Display conversion statistics in a formatted layout."""
        with st.expander(f"📊 {title}", expanded=False):
            if not stats:
                st.info("No statistics available")
                return
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Content Length", f"{stats.get('markdown_length', 0):,} chars")
            with col2:
                st.metric("Lines", f"{stats.get('markdown_lines', 0):,}")
            with col3:
                st.metric("Words", f"{stats.get('markdown_words', 0):,}")
            with col4:
                st.metric("Tool Used", stats.get('conversion_tool', 'Unknown'))
    
    @staticmethod
    def display_splitting_stats(stats: Dict[str, Any], title: str = "Splitting Statistics"):
        """Display splitting statistics."""
        with st.expander(f"✂️ {title}", expanded=False):
            if not stats:
                st.info("No statistics available")
                return
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Chunks", stats.get('total_chunks', 0))
            with col2:
                st.metric("Strategy Used", stats.get('strategy_used', 'Unknown'))
            with col3:
                st.metric("Avg Chunk Size", f"{stats.get('average_chunk_size', 0):,} chars")
            with col4:
                size_min = stats.get('min_chunk_size', 0)
                size_max = stats.get('max_chunk_size', 0)
                st.metric("Size Range", f"{size_min}-{size_max}")
    
    @staticmethod
    def display_processing_stats(stats, title: str = "Processing Statistics"):
        """Display LLM processing statistics."""
        with st.expander(f"🧠 {title}", expanded=False):
            if not stats:
                st.info("No statistics available")
                return
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("LLM Calls", stats.llm_calls)
            with col2:
                st.metric("Total Tokens", f"{sum(stats.total_tokens.values()):,}")
            with col3:
                st.metric("Processing Time", f"{stats.processing_time:.2f}s")
            with col4:
                st.metric("Sections Found", stats.sections_created)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Elements", stats.elements_created)
            with col2:
                st.metric("Variables", stats.variables_created)
            with col3:
                st.metric("Columns", stats.columns_created)


class ErrorDisplay:
    """Component for displaying errors and warnings."""
    
    @staticmethod
    def display_errors_and_warnings(errors: List[str], warnings: List[str]):
        """Display errors and warnings in expandable sections."""
        if errors:
            with st.expander(f"❌ Errors ({len(errors)})", expanded=len(errors) <= 3):
                for i, error in enumerate(errors, 1):
                    st.error(f"{i}. {error}")
        
        if warnings:
            with st.expander(f"⚠️ Warnings ({len(warnings)})", expanded=False):
                for i, warning in enumerate(warnings, 1):
                    st.warning(f"{i}. {warning}")


class FileUploadComponent:
    """Enhanced file upload component with validation."""
    
    @staticmethod
    def render_upload(
        label: str = "Choose a file to convert",
        accepted_types: List[str] = ['docx', 'md'],
        help_text: str = "Upload a DOCX questionnaire or Markdown file for conversion"
    ) -> Optional[Dict[str, Any]]:
        """Render file upload with validation and info display."""
        
        uploaded_file = st.file_uploader(
            label,
            type=accepted_types,
            help=help_text
        )
        
        if uploaded_file is not None:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            
            # File validation
            file_size = len(uploaded_file.getvalue())
            max_size = 50 * 1024 * 1024  # 50MB limit
            
            if file_size > max_size:
                st.error(f"❌ File too large: {file_size:,} bytes (max: {max_size:,} bytes)")
                return None
            
            # File info display
            with st.expander("📋 File Information", expanded=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Filename", uploaded_file.name)
                with col2:
                    st.metric("File Type", uploaded_file.type)
                with col3:
                    st.metric("File Size", f"{file_size:,} bytes")
            
            return {
                'file': uploaded_file,
                'filename': uploaded_file.name,
                'file_type': uploaded_file.name.split('.')[-1].lower(),
                'file_size': file_size,
                'mime_type': uploaded_file.type
            }
        
        return None


class ConfigurationPanel:
    """Configuration panel for various processing options."""
    
    @staticmethod
    def render_splitting_config() -> Dict[str, Any]:
        """Render splitting configuration panel."""
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
            
            return {
                'delimiter': delimiter,
                'fallback_size': fallback_size
            }
    
    @staticmethod
    def render_llm_config() -> Dict[str, Any]:
        """Render LLM configuration panel."""
        with st.expander("⚙️ LLM Configuration", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                provider = st.selectbox(
                    "LLM Provider",
                    options=["openai", "anthropic"],
                    index=0,
                    help="Choose the LLM provider for processing"
                )
            
            with col2:
                models = {
                    "openai": ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
                    "anthropic": ["claude-3-5-haiku-20241022", "claude-3-5-sonnet-20241022"]
                }
                model = st.selectbox(
                    "Model",
                    options=models[provider],
                    index=0,
                    help="Choose the specific model to use"
                )
            
            with col3:
                temperature = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1,
                    help="Sampling temperature (0.0 = deterministic, 1.0 = creative)"
                )
            
            # Advanced options
            with st.expander("🔧 Advanced Options", expanded=False):
                max_tokens = st.number_input(
                    "Max Tokens",
                    min_value=1000,
                    max_value=8000,
                    value=4000,
                    help="Maximum tokens per LLM response"
                )
                
                verbose = st.checkbox(
                    "Verbose Logging",
                    value=True,
                    help="Enable detailed logging during processing"
                )
            
            return {
                'provider': provider,
                'model': model,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'verbose': verbose
            }
