"""
File management utilities for docx-to-html processing.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FileManager:
    """Manages file operations and directory structure for processing."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        
    def setup_output_directories(self, input_path: Path, output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """
        Set up output directory structure for processing.
        
        Returns:
            Dict with 'output', 'monitoring', 'temp' directory paths
        """
        if output_dir is None:
            if input_path.is_file():
                output_dir = input_path.parent / "json_output"
            else:
                output_dir = input_path / "json_output"
        
        output_dir = Path(output_dir)
        monitoring_dir = output_dir / "monitoring"
        temp_dir = output_dir / "temp"
        
        # Create directories
        for dir_path in [output_dir, monitoring_dir, temp_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
            
        return {
            'output': output_dir,
            'monitoring': monitoring_dir,
            'temp': temp_dir
        }
    
    def find_markdown_files(self, directory: Path, recursive: bool = False) -> List[Path]:
        """Find all markdown files in a directory."""
        patterns = ["*.md", "*.markdown"]
        files = []
        
        for pattern in patterns:
            if recursive:
                files.extend(directory.rglob(pattern))
            else:
                files.extend(directory.glob(pattern))
        
        return sorted(files)
    
    def backup_existing_file(self, file_path: Path) -> Optional[Path]:
        """Create a backup of an existing file."""
        if not file_path.exists():
            return None
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.stem}_backup_{timestamp}{file_path.suffix}"
        
        try:
            shutil.copy2(file_path, backup_path)
            logger.info(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            logger.warning(f"Failed to create backup of {file_path}: {e}")
            return None
    
    def save_json_result(self, data: Dict[str, Any], output_path: Path, backup: bool = True) -> bool:
        """Save JSON data to file with optional backup."""
        try:
            if backup and output_path.exists():
                self.backup_existing_file(output_path)
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Saved JSON result to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save JSON result to {output_path}: {e}")
            return False
    
    def save_partial_progress(self, data: Dict[str, Any], monitoring_dir: Path, prefix: str = "partial") -> Path:
        """Save partial progress data with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}.json"
        filepath = monitoring_dir / filename
        
        monitoring_dir.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
        
        return filepath
    
    def cleanup_temp_files(self, temp_dir: Path, max_age_hours: int = 24) -> int:
        """Clean up temporary files older than specified hours."""
        if not temp_dir.exists():
            return 0
            
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleaned_count = 0
        
        for file_path in temp_dir.iterdir():
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    cleaned_count += 1
                except Exception as e:
                    logger.warning(f"Failed to clean up {file_path}: {e}")
        
        return cleaned_count
    
    def get_output_filename(self, input_file: Path, suffix: str = "_survey_schema") -> str:
        """Generate output filename based on input file."""
        return f"{input_file.stem}{suffix}.json"


class ResultsManager:
    """Manages processing results and reports."""
    
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
        
    def save_processing_result(self, result: Any, input_file: Path, output_dir: Path) -> Path:
        """Save the main processing result."""
        filename = self.file_manager.get_output_filename(input_file)
        output_path = output_dir / filename
        
        # Convert result to dict if needed
        if hasattr(result, 'dict'):
            result_data = result.dict()
        elif hasattr(result, '__dict__'):
            result_data = result.__dict__
        else:
            result_data = result
            
        success = self.file_manager.save_json_result(result_data, output_path)
        if not success:
            raise RuntimeError(f"Failed to save processing result to {output_path}")
            
        return output_path
    
    def save_error_report(self, errors: List[str], warnings: List[str], 
                         input_file: Path, monitoring_dir: Path) -> Path:
        """Save error and warning report."""
        report_data = {
            'input_file': str(input_file),
            'timestamp': datetime.now().isoformat(),
            'errors': errors,
            'warnings': warnings,
            'error_count': len(errors),
            'warning_count': len(warnings)
        }
        
        return self.file_manager.save_partial_progress(
            report_data, monitoring_dir, prefix="error_report"
        )
    
    def save_batch_summary(self, summary_data: Dict[str, Any], output_dir: Path) -> Path:
        """Save batch processing summary."""
        summary_path = output_dir / "batch_summary.json"
        
        success = self.file_manager.save_json_result(summary_data, summary_path)
        if not success:
            raise RuntimeError(f"Failed to save batch summary to {summary_path}")
            
        return summary_path
    
    def generate_processing_summary(self, results: List[Any], processing_times: List[float],
                                  total_files: int) -> Dict[str, Any]:
        """Generate a comprehensive processing summary."""
        successful_results = [r for r in results if not (hasattr(r, 'errors') and r.errors)]
        
        summary = {
            'processing_summary': {
                'total_files': total_files,
                'processed_files': len(results),
                'successful_files': len(successful_results),
                'failed_files': len(results) - len(successful_results),
                'success_rate': len(successful_results) / len(results) * 100 if results else 0
            },
            'timing_summary': {
                'total_processing_time': sum(processing_times),
                'average_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0,
                'min_processing_time': min(processing_times) if processing_times else 0,
                'max_processing_time': max(processing_times) if processing_times else 0
            },
            'content_summary': {
                'total_sections': sum(getattr(r, 'sections_found', 0) for r in results),
                'total_elements': sum(getattr(r, 'elements_found', 0) for r in results),
                'total_chunks': sum(getattr(r, 'chunks_processed', 0) for r in results),
                'total_tokens': {
                    'input': sum(getattr(r, 'total_tokens_used', {}).get('input', 0) for r in results),
                    'output': sum(getattr(r, 'total_tokens_used', {}).get('output', 0) for r in results)
                }
            },
            'error_summary': {
                'total_errors': sum(len(getattr(r, 'errors', [])) for r in results),
                'total_warnings': sum(len(getattr(r, 'warnings', [])) for r in results)
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
