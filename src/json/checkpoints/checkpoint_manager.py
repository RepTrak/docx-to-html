"""
Service for managing checkpoints during markdown processing.
Saves individual sections and elements as they are completed for recovery purposes.
"""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from ...models.questionnaire import FullSectionResponseSchema, FullSectionElementSchema
from ...models.parsing_state import PartialSection, PartialElement


class CheckpointManager:
    """Service for managing processing checkpoints."""
    
    def __init__(
        self, 
        checkpoint_dir: Optional[Path] = None,
        enable_checkpoints: bool = True,
        verbose: bool = False
    ):
        """
        Initialize the checkpoint manager.
        
        Args:
            checkpoint_dir: Directory for storing checkpoint files
            enable_checkpoints: Whether to enable checkpoint functionality
            verbose: Enable verbose logging
        """
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else None
        self.enable_checkpoints = enable_checkpoints
        self.verbose = verbose
        self.session_id = f"session_{int(time.time())}"
        
        # Checkpoint metadata
        self.sections_saved = []
        self.elements_saved = []
        self.checkpoint_index = 0
        
        if self.enable_checkpoints and self.checkpoint_dir:
            self._setup_checkpoint_directory()
    
    def _log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[Checkpoint] {message}")
    
    def _setup_checkpoint_directory(self) -> None:
        """Setup checkpoint directory structure."""
        if not self.checkpoint_dir:
            return
            
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # Create session subdirectory
        self.session_dir = self.checkpoint_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for different checkpoint types
        (self.session_dir / "sections").mkdir(exist_ok=True)
        (self.session_dir / "elements").mkdir(exist_ok=True)
        (self.session_dir / "metadata").mkdir(exist_ok=True)
        
        self._log(f"Checkpoint directory setup: {self.session_dir}")
    
    def save_section_checkpoint(
        self, 
        section: FullSectionResponseSchema, 
        chunk_index: int,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """
        Save a section checkpoint.
        
        Args:
            section: The completed section to save
            chunk_index: Current chunk index when section was completed
            additional_metadata: Additional metadata to save with checkpoint
            
        Returns:
            Path to saved checkpoint file or None if disabled
        """
        if not self.enable_checkpoints or not self.checkpoint_dir:
            return None
        
        try:
            checkpoint_data = {
                "type": "section",
                "checkpoint_index": self.checkpoint_index,
                "chunk_index": chunk_index,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "section_data": section.dict(),
                "metadata": additional_metadata or {}
            }
            
            # Generate filename
            section_code = section.code or f"section_{self.checkpoint_index}"
            filename = f"section_{self.checkpoint_index:04d}_{section_code}.json"
            filepath = self.session_dir / "sections" / filename
            
            # Save checkpoint
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Update tracking
            self.sections_saved.append({
                "checkpoint_index": self.checkpoint_index,
                "section_code": section_code,
                "filepath": str(filepath),
                "chunk_index": chunk_index,
                "timestamp": checkpoint_data["timestamp"]
            })
            
            self.checkpoint_index += 1
            self._log(f"Section checkpoint saved: {filename}")
            
            # Save metadata update
            self._save_checkpoint_metadata()
            
            return filepath
            
        except Exception as e:
            self._log(f"Error saving section checkpoint: {e}")
            return None
    
    def save_element_checkpoint(
        self, 
        element: FullSectionElementSchema, 
        section_code: str,
        chunk_index: int,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """
        Save an element checkpoint.
        
        Args:
            element: The completed element to save
            section_code: Code of the parent section
            chunk_index: Current chunk index when element was completed
            additional_metadata: Additional metadata to save with checkpoint
            
        Returns:
            Path to saved checkpoint file or None if disabled
        """
        if not self.enable_checkpoints or not self.checkpoint_dir:
            return None
        
        try:
            checkpoint_data = {
                "type": "element",
                "checkpoint_index": self.checkpoint_index,
                "chunk_index": chunk_index,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "parent_section_code": section_code,
                "element_data": element.dict(),
                "metadata": additional_metadata or {}
            }
            
            # Generate filename
            element_code = element.code or f"element_{self.checkpoint_index}"
            filename = f"element_{self.checkpoint_index:04d}_{section_code}_{element_code}.json"
            filepath = self.session_dir / "elements" / filename
            
            # Save checkpoint
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Update tracking
            self.elements_saved.append({
                "checkpoint_index": self.checkpoint_index,
                "element_code": element_code,
                "section_code": section_code,
                "filepath": str(filepath),
                "chunk_index": chunk_index,
                "timestamp": checkpoint_data["timestamp"]
            })
            
            self.checkpoint_index += 1
            self._log(f"Element checkpoint saved: {filename}")
            
            # Save metadata update
            self._save_checkpoint_metadata()
            
            return filepath
            
        except Exception as e:
            self._log(f"Error saving element checkpoint: {e}")
            return None
    
    def save_partial_state_checkpoint(
        self,
        current_section: Optional[PartialSection],
        current_element: Optional[PartialElement],
        chunk_index: int,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """
        Save current partial state as checkpoint for recovery.
        
        Args:
            current_section: Current partial section being processed
            current_element: Current partial element being processed
            chunk_index: Current chunk index
            additional_metadata: Additional metadata to save
            
        Returns:
            Path to saved checkpoint file or None if disabled
        """
        if not self.enable_checkpoints or not self.checkpoint_dir:
            return None
        
        try:
            checkpoint_data = {
                "type": "partial_state",
                "checkpoint_index": self.checkpoint_index,
                "chunk_index": chunk_index,
                "timestamp": datetime.now().isoformat(),
                "session_id": self.session_id,
                "current_section": current_section.dict() if current_section else None,
                "current_element": current_element.dict() if current_element else None,
                "metadata": additional_metadata or {}
            }
            
            filename = f"partial_state_{self.checkpoint_index:04d}_chunk_{chunk_index:04d}.json"
            filepath = self.session_dir / "metadata" / filename
            
            # Save checkpoint
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.checkpoint_index += 1
            self._log(f"Partial state checkpoint saved: {filename}")
            
            return filepath
            
        except Exception as e:
            self._log(f"Error saving partial state checkpoint: {e}")
            return None
    
    def _save_checkpoint_metadata(self) -> None:
        """Save checkpoint metadata summary."""
        if not self.enable_checkpoints or not self.checkpoint_dir:
            return
        
        try:
            metadata = {
                "session_id": self.session_id,
                "last_updated": datetime.now().isoformat(),
                "checkpoint_index": self.checkpoint_index,
                "sections_saved": self.sections_saved,
                "elements_saved": self.elements_saved,
                "total_sections": len(self.sections_saved),
                "total_elements": len(self.elements_saved),
                "checkpoint_directory": str(self.session_dir)
            }
            
            metadata_file = self.session_dir / "metadata" / "checkpoint_summary.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
                
        except Exception as e:
            self._log(f"Error saving checkpoint metadata: {e}")
    
    def load_checkpoint_metadata(self, session_dir: Path) -> Optional[Dict[str, Any]]:
        """
        Load checkpoint metadata from a previous session.
        
        Args:
            session_dir: Path to the session directory
            
        Returns:
            Checkpoint metadata or None if not found
        """
        try:
            metadata_file = session_dir / "metadata" / "checkpoint_summary.json"
            if metadata_file.exists():
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self._log(f"Error loading checkpoint metadata: {e}")
        
        return None
    
    def list_available_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available checkpoint sessions.
        
        Returns:
            List of session information
        """
        if not self.checkpoint_dir or not self.checkpoint_dir.exists():
            return []
        
        sessions = []
        for session_dir in self.checkpoint_dir.iterdir():
            if session_dir.is_dir() and session_dir.name.startswith("session_"):
                metadata = self.load_checkpoint_metadata(session_dir)
                if metadata:
                    sessions.append({
                        "session_id": session_dir.name,
                        "session_dir": str(session_dir),
                        "metadata": metadata
                    })
        
        return sorted(sessions, key=lambda x: x["metadata"].get("last_updated", ""), reverse=True)
    
    def get_checkpoint_summary(self) -> Dict[str, Any]:
        """Get summary of current checkpoint session."""
        return {
            "session_id": self.session_id,
            "checkpoint_dir": str(self.checkpoint_dir) if self.checkpoint_dir else None,
            "session_dir": str(self.session_dir) if hasattr(self, "session_dir") else None,
            "enabled": self.enable_checkpoints,
            "checkpoint_index": self.checkpoint_index,
            "sections_saved": len(self.sections_saved),
            "elements_saved": len(self.elements_saved),
            "sections_details": self.sections_saved,
            "elements_details": self.elements_saved
        }
