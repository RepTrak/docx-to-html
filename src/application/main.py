"""
Main Streamlit application entry point and page imports.
"""

# Import pages from the new structure
from .pages.documentation import DocumentationPage
from .pages.conversion import ConversionPage
from .pages.diff import DiffPage

# Re-export for backward compatibility
__all__ = ['DocumentationPage', 'ConversionPage', 'DiffPage']
