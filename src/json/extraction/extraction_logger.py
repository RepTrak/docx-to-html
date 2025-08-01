"""
Specialized logger for content extraction debugging.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..analysis.prompt_logger import PromptLogger


class ExtractionLogger(PromptLogger):
    """Specialized logger for extraction operations with additional context."""
    
    def __init__(self, log_dir: str = "extraction_debug_logs", enabled: bool = False):
        """
        Initialize the extraction logger.
        
        Args:
            log_dir: Directory to save extraction log files
            enabled: Whether logging is enabled
        """
        super().__init__(log_dir, enabled)
        
        if self.enabled:
            # Create extraction-specific subdirectories
            self.extraction_dir = self.session_dir / "extractions"
            self.fragments_dir = self.session_dir / "fragments"
            self.continuity_dir = self.session_dir / "continuity"
            
            self.extraction_dir.mkdir(exist_ok=True)
            self.fragments_dir.mkdir(exist_ok=True)
            self.continuity_dir.mkdir(exist_ok=True)
    
    def log_extraction_prompt(
        self,
        chunk_index: int,
        chunk_content: str,
        analysis_result: Dict[str, Any],
        parsing_state: Dict[str, Any],
        enhanced_prompt: str,
        messages: List[Dict[str, str]],
        response: Optional[Dict[str, Any]] = None,
        fragment_metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an extraction prompt with enhanced context.
        
        Args:
            chunk_index: Index of the chunk being processed
            chunk_content: Raw chunk content
            analysis_result: Result from chunk analysis
            parsing_state: Current parsing state information
            enhanced_prompt: The enhanced prompt used for extraction
            messages: Full LLM messages
            response: LLM response if available
            fragment_metadata: Fragment boundary information
        """
        if not self.enabled:
            return
        
        self.prompt_count += 1
        
        # Create comprehensive extraction log
        extraction_log = {
            "timestamp": datetime.now().isoformat(),
            "chunk_index": chunk_index,
            "prompt_count": self.prompt_count,
            "analysis_result": analysis_result,
            "parsing_state": parsing_state,
            "fragment_metadata": fragment_metadata or {},
            "enhanced_prompt": enhanced_prompt,
            "messages": messages,
            "chunk_content": chunk_content,
            "response": response,
            "extraction_context": {
                "has_accumulated_content": bool(
                    parsing_state.get("current_section", {}).get("accumulated_content") or
                    parsing_state.get("current_element", {}).get("accumulated_content")
                ),
                "is_continuation": analysis_result.get("chunk_type") in [
                    "SECTION_CONTINUATION", "ELEMENT_CONTINUATION"
                ],
                "has_table_data": "|" in chunk_content,
                "chunk_type": analysis_result.get("chunk_type", "UNKNOWN")
            }
        }
        
        # Save to extraction directory
        filename = f"extraction_{chunk_index:03d}_{self.prompt_count:03d}.json"
        filepath = self.extraction_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(extraction_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to log extraction to {filepath}: {e}")
    
    def log_fragment_processing(
        self,
        chunk_index: int,
        fragment_context: Dict[str, Any],
        boundary_detection: Dict[str, Any],
        continuity_analysis: Dict[str, Any]
    ) -> None:
        """Log fragment processing details."""
        if not self.enabled:
            return
        
        fragment_log = {
            "timestamp": datetime.now().isoformat(),
            "chunk_index": chunk_index,
            "fragment_context": fragment_context,
            "boundary_detection": boundary_detection,
            "continuity_analysis": continuity_analysis
        }
        
        filename = f"fragment_{chunk_index:03d}.json"
        filepath = self.fragments_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(fragment_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to log fragment data: {e}")
    
    def log_continuity_decision(
        self,
        chunk_index: int,
        decision_type: str,
        reasoning: str,
        context_factors: Dict[str, Any],
        outcome: Dict[str, Any]
    ) -> None:
        """Log continuity processing decisions."""
        if not self.enabled:
            return
        
        continuity_log = {
            "timestamp": datetime.now().isoformat(),
            "chunk_index": chunk_index,
            "decision_type": decision_type,
            "reasoning": reasoning,
            "context_factors": context_factors,
            "outcome": outcome
        }
        
        filename = f"continuity_{chunk_index:03d}_{decision_type.lower()}.json"
        filepath = self.continuity_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(continuity_log, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to log continuity decision: {e}")
    
    def log_extraction_summary(
        self,
        total_chunks: int,
        successful_extractions: int,
        failed_extractions: int,
        fragment_count: int,
        continuity_decisions: int,
        token_usage: Dict[str, int]
    ) -> None:
        """Log extraction session summary."""
        if not self.enabled:
            return
        
        summary = {
            "session_completed": datetime.now().isoformat(),
            "total_chunks": total_chunks,
            "successful_extractions": successful_extractions,
            "failed_extractions": failed_extractions,
            "fragment_count": fragment_count,
            "continuity_decisions": continuity_decisions,
            "total_extraction_prompts": self.prompt_count,
            "token_usage": token_usage,
            "session_path": str(self.session_dir),
            "extraction_logs_path": str(self.extraction_dir),
            "fragment_logs_path": str(self.fragments_dir),
            "continuity_logs_path": str(self.continuity_dir)
        }
        
        summary_file = self.session_dir / "extraction_summary.json"
        
        try:
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to log extraction summary: {e}")
