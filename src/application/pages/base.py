"""
Base page class for the application.
"""

import streamlit as st


class BasePage:
    """Base class for application pages."""
    
    def __init__(self):
        self.title = "Base Page"
    
    def render(self):
        """Render the page content."""
        st.title(self.title)
