"""
Service for logging prompts and responses for debugging purposes.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class PromptLogger:
    """Logger for saving prompts and responses for debugging."""
    
    def __init__(self, log_dir: str = "debug_logs", enabled: bool = False):
        """
        Initialize the prompt logger.
        
        Args:
            log_dir: Directory to save log files
            enabled: Whether logging is enabled
        """
        self.enabled = enabled
        self.log_dir = Path(log_dir)
        
        if self.enabled:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Create session-specific subdirectory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.session_dir = self.log_dir / f"session_{timestamp}"
            self.session_dir.mkdir(exist_ok=True)
            
            self.prompt_count = 0
    
    def log_prompt(
        self,
        prompt_type: str,
        messages: List[Dict[str, str]],
        chunk_index: int,
        chunk_content: str,
        response: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a prompt and its response.
        
        Args:
            prompt_type: Type of prompt (e.g., "chunk_analysis")
            messages: LLM messages sent
            chunk_index: Index of the chunk being analyzed
            chunk_content: The actual chunk content
            response: LLM response (if available)
            metadata: Additional metadata to log
        """
        if not self.enabled:
            return
        
        self.prompt_count += 1
        
        # Create log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "prompt_type": prompt_type,
            "chunk_index": chunk_index,
            "prompt_count": self.prompt_count,
            "messages": messages,
            "chunk_content": chunk_content,
            "response": response,
            "metadata": metadata or {}
        }
        
        # Save to individual file
        filename = f"{prompt_type}_{chunk_index:03d}_{self.prompt_count:03d}.json"
        filepath = self.session_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_entry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to log prompt to {filepath}: {e}")
    
    def log_analysis_summary(self, summary: Dict[str, Any]) -> None:
        """Log a summary of the analysis session."""
        if not self.enabled:
            return
        
        summary_file = self.session_dir / "analysis_summary.json"
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to log analysis summary: {e}")
    
    def get_session_path(self) -> Optional[str]:
        """Get the path to the current session directory."""
        if self.enabled:
            return str(self.session_dir)
        return None
