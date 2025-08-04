"""
State management for the conversion pipeline.
"""

import streamlit as st
from typing import Dict, Any, Optional


class ConversionStateManager:
    """Manages session state for the conversion pipeline."""
    
    @staticmethod
    def initialize_state():
        """Initialize the conversion state if not exists."""
        if 'conversion_state' not in st.session_state:
            st.session_state.conversion_state = {
                'file_uploaded': False,
                'conversion_complete': False,
                'splitting_complete': False,
                'schema_complete': False,
                'markdown_content': None,
                'conversion_result': None,
                'split_result': None,
                'schema_result': None,
                'processing_stats': None
            }
    
    @staticmethod
    def get_state() -> Dict[str, Any]:
        """Get the current conversion state."""
        return st.session_state.conversion_state
    
    @staticmethod
    def update_state(updates: Dict[str, Any]):
        """Update the conversion state with new values."""
        st.session_state.conversion_state.update(updates)
    
    @staticmethod
    def reset_state():
        """Reset the conversion state for a new file."""
        for key in list(st.session_state.keys()):
            if key.startswith('conversion_state'):
                del st.session_state[key]
    
    @staticmethod
    def is_step_complete(step: str) -> bool:
        """Check if a specific step is complete."""
        state = ConversionStateManager.get_state()
        step_mapping = {
            'upload': 'file_uploaded',
            'conversion': 'conversion_complete',
            'splitting': 'splitting_complete',
            'schema': 'schema_complete'
        }
        return state.get(step_mapping.get(step, step), False)
