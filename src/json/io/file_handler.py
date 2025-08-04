"""
File I/O operations for markdown processing.
"""

import json
from pathlib import Path
from typing import Optional

from ...models.parsing_state import ProcessingResult
from ...models.monitoring import PartialReport


class FileHandler:
    """Service for handling file I/O operations."""
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the file handler.
        
        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(message)
    
    def read_markdown_file(self, file_path: Path) -> str:
        """
        Read markdown file content.
        
        Args:
            file_path: Path to the markdown file
            
        Returns:
            File content as string
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Markdown file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def save_results(
        self, 
        result: ProcessingResult, 
        file_path: Path, 
        output_dir: Path,
        monitor_report: Optional[PartialReport] = None
    ) -> None:
        """
        Save processing results to files.
        
        Args:
            result: Processing result to save
            file_path: Original file path for naming
            output_dir: Output directory
            monitor_report: Optional monitoring report
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save survey JSON
        survey_file = output_dir / f"{file_path.stem}_survey.json"
        with open(survey_file, 'w', encoding='utf-8') as f:
            json.dump(result.survey.dict(), f, indent=2, ensure_ascii=False)
        
        # Save processing report
        report_file = output_dir / f"{file_path.stem}_processing_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(result.dict(), f, indent=2, ensure_ascii=False, default=str)
        
        # Save final partial report
        if monitor_report:
            partial_report_file = output_dir / f"{file_path.stem}_partial_report_final.json"
            with open(partial_report_file, 'w', encoding='utf-8') as f:
                json.dump(monitor_report.dict(), f, indent=2, ensure_ascii=False, default=str)
        
        # Save checkpoint summary if available
        checkpoint_info = result.parsing_stats.get("checkpoint_info")
        if checkpoint_info:
            checkpoint_file = output_dir / f"{file_path.stem}_checkpoint_summary.json"
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_info, f, indent=2, ensure_ascii=False, default=str)
            
            self._log(f"Checkpoint summary saved to: {checkpoint_file}")
        
        self._log(f"Results saved to: {output_dir}")
