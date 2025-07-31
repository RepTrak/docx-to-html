"""
Utility functions for monitoring and partial reports.
"""

import json
import threading
import time
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from datetime import datetime

from ..models.monitoring import PartialReport, ProcessingPhase

def print_progress_callback(report: PartialReport) -> None:
    """Simple console progress callback."""
    completion = report.get_completion_percentage()
    phase = report.progress.current_phase.value
    
    print(f"\r[{completion:5.1f}%] Phase: {phase} | "
          f"Chunks: {report.progress.chunks_completed}/{report.progress.total_chunks} | "
          f"Sections: {report.progress.sections_found} | "
          f"Elements: {report.progress.elements_found}", end="")
    
    if report.progress.current_phase == ProcessingPhase.COMPLETED:
        print()  # New line at completion

def save_report_callback(output_dir: str) -> Callable[[PartialReport], None]:
    """Create a callback that saves reports to file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    def callback(report: PartialReport) -> None:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"partial_report_{timestamp}.json"
            filepath = output_path / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report.dict(), f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            print(f"Error saving partial report: {e}")
    
    return callback

def create_dashboard_callback(update_interval: float = 2.0) -> Callable[[PartialReport], None]:
    """Create a callback that displays a live dashboard."""
    last_update = [0.0]  # Use list for mutable reference
    
    def callback(report: PartialReport) -> None:
        current_time = time.time()
        if current_time - last_update[0] < update_interval:
            return  # Skip update if too soon
        
        last_update[0] = current_time
        
        # Clear screen (works on most terminals)
        print("\033[2J\033[H", end="")
        
        # Header
        print("=" * 80)
        print(f"📊 MARKDOWN PROCESSING DASHBOARD")
        print("=" * 80)
        print()
        
        # File info
        print(f"📄 File: {Path(report.file_path).name}")
        print(f"⏰ Started: {report.progress.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔄 Phase: {report.progress.current_phase.value.upper()}")
        print()
        
        # Progress bar
        completion = report.get_completion_percentage()
        bar_width = 50
        filled = int(bar_width * completion / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        print(f"Progress: [{bar}] {completion:5.1f}%")
        print()
        
        # Statistics
        print("📈 STATISTICS:")
        print(f"  Chunks:    {report.progress.chunks_completed:4d} / {report.progress.total_chunks}")
        print(f"  Sections:  {report.progress.sections_found:4d}")
        print(f"  Elements:  {report.progress.elements_found:4d}")
        print(f"  Variables: {report.progress.variables_found:4d}")
        print(f"  Columns:   {report.progress.columns_found:4d}")
        print()
        
        # Performance
        if report.progress.processing_rate_chunks_per_minute:
            rate = report.progress.processing_rate_chunks_per_minute
            print(f"⚡ Processing Rate: {rate:.1f} chunks/min")
            
        if report.progress.estimated_completion:
            eta = report.progress.estimated_completion.strftime('%H:%M:%S')
            print(f"⏱️  Estimated Completion: {eta}")
        print()
        
        # Current chunk info
        if report.progress.current_chunk:
            chunk = report.progress.current_chunk
            print(f"🔍 Current Chunk #{chunk.chunk_index}:")
            print(f"  Size: {chunk.chunk_size} chars")
            if chunk.chunk_type:
                print(f"  Type: {chunk.chunk_type}")
            if chunk.confidence is not None:
                print(f"  Confidence: {chunk.confidence:.2f}")
        print()
        
        # Current content previews
        if report.current_section_preview:
            section = report.current_section_preview
            print(f"📝 Current Section: {section.get('code', 'N/A')} - {section.get('label', 'N/A')[:50]}")
            
        if report.current_element_preview:
            element = report.current_element_preview
            print(f"❓ Current Element: {element.get('code', 'N/A')} - {element.get('label', 'N/A')[:50]}")
        print()
        
        # Errors and warnings
        if report.errors:
            print(f"❌ Errors: {len(report.errors)}")
            for error in report.errors[-3:]:  # Show last 3 errors
                print(f"  • {error[:70]}...")
            print()
            
        if report.warnings:
            print(f"⚠️  Warnings: {len(report.warnings)}")
            for warning in report.warnings[-3:]:  # Show last 3 warnings
                print(f"  • {warning[:70]}...")
            print()
        
        # Token usage
        if report.token_usage:
            total_tokens = report.token_usage.get('input', 0) + report.token_usage.get('output', 0)
            print(f"🪙 Tokens Used: {total_tokens:,} (In: {report.token_usage.get('input', 0):,}, Out: {report.token_usage.get('output', 0):,})")
            print()
        
        print("-" * 80)
        if report.progress.current_phase != ProcessingPhase.COMPLETED:
            print("Press Ctrl+C to stop monitoring...")
    
    return callback

def load_partial_report(filepath: str) -> Optional[PartialReport]:
    """Load a partial report from file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return PartialReport(**data)
    except Exception as e:
        print(f"Error loading partial report: {e}")
        return None

def merge_partial_reports(reports: list[PartialReport]) -> Optional[PartialReport]:
    """Merge multiple partial reports into one (useful for resuming processing)."""
    if not reports:
        return None
    
    # Use the latest report as base
    latest_report = max(reports, key=lambda r: r.progress.last_update)
    
    # Merge completed sections from all reports
    all_sections = []
    seen_section_codes = set()
    
    for report in sorted(reports, key=lambda r: r.progress.chunks_completed):
        for section in report.completed_sections:
            section_code = section.get('code')
            if section_code and section_code not in seen_section_codes:
                all_sections.append(section)
                seen_section_codes.add(section_code)
    
    latest_report.completed_sections = all_sections
    
    # Merge errors and warnings
    all_errors = []
    all_warnings = []
    
    for report in reports:
        all_errors.extend(report.errors)
        all_warnings.extend(report.warnings)
    
    latest_report.errors = list(set(all_errors))  # Remove duplicates
    latest_report.warnings = list(set(all_warnings))
    
    return latest_report

class ProgressMonitoringThread:
    """Background thread for monitoring processing progress."""
    
    def __init__(
        self, 
        processor, 
        update_interval: float = 1.0,
        dashboard: bool = True
    ):
        self.processor = processor
        self.update_interval = update_interval
        self.dashboard = dashboard
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
    def start(self) -> None:
        """Start monitoring in background thread."""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        
    def stop(self) -> None:
        """Stop monitoring."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        callback = create_dashboard_callback() if self.dashboard else print_progress_callback
        
        while self.running:
            try:
                report = self.processor.get_partial_report()
                if report:
                    callback(report)
                    
                    # Stop if processing is complete
                    if report.progress.current_phase == ProcessingPhase.COMPLETED:
                        break
                        
                time.sleep(self.update_interval)
                
            except Exception as e:
                print(f"Error in monitoring thread: {e}")
                break
