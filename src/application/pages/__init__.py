"""
Application pages for the DOCX to Schema converter.
"""

from .base import BasePage
from .documentation import DocumentationPage
from .conversion import ConversionPage
from .diff import DiffPage

__all__ = ['BasePage', 'DocumentationPage', 'ConversionPage', 'DiffPage']
