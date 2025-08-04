"""
Main entry point for the DOCX to Schema Conversion Streamlit application.
"""

import streamlit as st
import sys
from pathlib import Path

# Add src to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Configure Streamlit page
st.set_page_config(
    page_title="DOCX to Schema Converter",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    """Main application entry point."""
    
    # Import the main application after setting up the path
    from src.application.main import DocumentationPage, ConversionPage, DiffPage
    
    # Sidebar navigation
    st.sidebar.title("📄 DOCX to Schema Converter")
    st.sidebar.markdown("---")
    
    # Page selection
    page_options = {
        "📖 Documentation": DocumentationPage,
        "🔄 File Conversion": ConversionPage,
        "📊 File Diff Comparison": DiffPage
    }
    
    selected_page = st.sidebar.selectbox(
        "Select Page",
        options=list(page_options.keys()),
        index=0
    )
    
    # Render selected page
    page_class = page_options[selected_page]
    page = page_class()
    page.render()

if __name__ == "__main__":
    main()
