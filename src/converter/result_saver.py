"""
Saves conversion results to various file formats.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Union

from ..models.questionnaire import FullSurveyResponseSchema
from .schema_models import ProcessingStats

logger = logging.getLogger(__name__)


class ResultSaver:
    """Saves conversion results to files."""
    
    def __init__(self, verbose: bool = True):
        """
        Initialize the result saver.
        
        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
    
    def _log(self, message: str, level: str = "info") -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            getattr(logger, level, logger.info)(f"[ResultSaver] {message}")
    
    def save_results(
        self, 
        survey: FullSurveyResponseSchema, 
        stats: ProcessingStats,
        output_dir: Union[str, Path], 
        filename_prefix: str = "survey"
    ) -> Dict[str, Path]:
        """
        Save conversion results to files.
        
        Args:
            survey: The converted survey schema
            stats: Processing statistics
            output_dir: Directory to save files
            filename_prefix: Prefix for output files
            
        Returns:
            Dictionary of saved file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        try:
            # Save survey schema as JSON
            schema_file = output_dir / f"{filename_prefix}_schema.json"
            with open(schema_file, 'w', encoding='utf-8') as f:
                json.dump(survey.model_dump(), f, indent=2, ensure_ascii=False)
            saved_files['schema'] = schema_file
            
            # Save processing stats
            stats_file = output_dir / f"{filename_prefix}_stats.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump({
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
                }, f, indent=2)
            saved_files['stats'] = stats_file
            
            # Save human-readable summary
            summary_file = output_dir / f"{filename_prefix}_summary.txt"
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(self._create_summary_report(survey, stats))
            saved_files['summary'] = summary_file
            
            self._log(f"Results saved to {output_dir}")
            return saved_files
            
        except Exception as e:
            error_msg = f"Error saving results: {str(e)}"
            self._log(error_msg, "error")
            raise
    
    def _create_summary_report(self, survey: FullSurveyResponseSchema, stats: ProcessingStats) -> str:
        """Create a human-readable summary report."""
        lines = [
            "MARKDOWN TO SCHEMA CONVERSION SUMMARY",
            "=" * 50,
            "",
            f"Processing Statistics:",
            f"- Total chunks processed: {stats.processed_chunks}/{stats.total_chunks}",
            f"- LLM calls made: {stats.llm_calls}",
            f"- Total tokens used: {sum(stats.total_tokens.values()):,}",
            f"- Processing time: {stats.processing_time:.2f} seconds",
            "",
            f"Content Statistics:",
            f"- Sections created: {stats.sections_created}",
            f"- Elements created: {stats.elements_created}",
            f"- Variables created: {stats.variables_created}",
            f"- Columns created: {stats.columns_created}",
            "",
            f"Survey Structure:",
        ]
        
        # Add section details
        for i, section in enumerate(survey.sections, 1):
            lines.append(f"  {i}. Section '{section.code}': {section.label[:50]}...")
            if section.elements:
                lines.append(f"     - {len(section.elements)} elements")
                for j, element in enumerate(section.elements[:3], 1):  # Show first 3 elements
                    lines.append(f"       {j}. {element.code} ({element.type})")
                if len(section.elements) > 3:
                    lines.append(f"       ... and {len(section.elements) - 3} more elements")
            lines.append("")
        
        # Add errors and warnings
        if stats.errors:
            lines.extend([
                "Errors encountered:",
                *[f"- {error}" for error in stats.errors],
                ""
            ])
        
        if stats.warnings:
            lines.extend([
                "Warnings:",
                *[f"- {warning}" for warning in stats.warnings],
                ""
            ])
        
        return "\n".join(lines)
