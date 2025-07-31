#!/usr/bin/env python3
"""
Command-line script for processing markdown files in chunks to build survey schemas.
"""

import logging
import sys
import re
import threading
import time
from pathlib import Path

import click

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.json.markdown_chunk_processor import MarkdownChunkProcessor
from src.llm import LLMClient
from src.utils.monitoring_utils import (
    print_progress_callback, 
    create_dashboard_callback, 
    save_report_callback,
    ProgressMonitoringThread
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
# Set up logging
logger = logging.getLogger(__name__)


@click.group()
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.option(
    '--chunk-size',
    type=int,
    default=4000,
    help='Size of each chunk in characters (default: 2000)'
)
@click.option(
    '--chunk-overlap',
    type=int,
    default=200,
    help='Overlap between chunks in characters (default: 200)'
)
@click.option(
    '--retry-attempts',
    type=int,
    default=3,
    help='Number of retry attempts for LLM calls (default: 3)'
)
@click.option(
    '--providers',
    multiple=True,
    type=click.Choice(['openai', 'anthropic'], case_sensitive=False),
    help='LLM providers to use (can specify multiple)'
)
@click.option(
    '--dashboard/--no-dashboard',
    default=True,
    help='Enable/disable live dashboard (default: enabled)'
)
@click.option(
    '--auto-save-interval',
    type=int,
    default=10,
    help='Auto-save partial results every N chunks (default: 10)'
)
@click.option(
    '--monitoring-dir',
    type=click.Path(path_type=Path),
    help='Directory for saving monitoring reports (default: same as output)'
)
@click.pass_context
def cli(ctx, verbose, chunk_size, chunk_overlap, retry_attempts, providers, dashboard, auto_save_interval, monitoring_dir):
    """Process markdown files in chunks to build survey schemas using LLM."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    ctx.obj['chunk_size'] = chunk_size
    ctx.obj['chunk_overlap'] = chunk_overlap
    ctx.obj['retry_attempts'] = retry_attempts
    ctx.obj['providers'] = list(providers) if providers else ['anthropic', 'openai']
    ctx.obj['dashboard'] = dashboard
    ctx.obj['auto_save_interval'] = auto_save_interval
    ctx.obj['monitoring_dir'] = monitoring_dir


@cli.command('process-file')
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output-dir', '-o',
    type=click.Path(path_type=Path),
    help='Output directory for JSON results (default: same as input file)'
)
@click.option(
    '--monitor-only',
    is_flag=True,
    help='Only show monitoring, do not display verbose logs'
)
@click.option(
    '--save-progress',
    is_flag=True,
    help='Save progress reports to files'
)
@click.pass_context
def process_file(ctx, input_file, output_dir, monitor_only, save_progress):
    """Process a single markdown file to build survey schema with monitoring."""
    
    if monitor_only and ctx.obj['verbose']:
        click.echo("Note: --monitor-only overrides --verbose for cleaner monitoring display")
        ctx.obj['verbose'] = False
    
    # Determine monitoring directory
    monitoring_dir = ctx.obj['monitoring_dir'] or output_dir or input_file.parent / "monitoring"
    
    # Create progress callback
    progress_callback = None
    if ctx.obj['dashboard'] and not monitor_only:
        progress_callback = create_dashboard_callback(update_interval=1.0)
    elif not ctx.obj['dashboard']:
        progress_callback = print_progress_callback
    
    # Add file saving callback if requested
    if save_progress:
        file_callback = save_report_callback(str(monitoring_dir))
        if progress_callback:
            def combined_callback(report):
                progress_callback(report)
                file_callback(report)
            progress_callback = combined_callback
        else:
            progress_callback = file_callback
    
    logging.info(f"Processing markdown file: {input_file}")
    
    # Initialize LLM client with specified providers
    llm_client = LLMClient(
        providers=ctx.obj['providers'],
        retry_attempts=ctx.obj['retry_attempts'],
        retry_delay=1.0,
        retry_backoff=2.0
    )
    
    # Initialize processor with monitoring
    processor = MarkdownChunkProcessor(
        llm_client=llm_client,
        chunk_size=ctx.obj['chunk_size'],
        chunk_overlap=ctx.obj['chunk_overlap'],
        verbose=ctx.obj['verbose'],
        retry_attempts=ctx.obj['retry_attempts'],
        progress_callback=progress_callback,
        auto_save_interval=ctx.obj['auto_save_interval'],
        auto_save_dir=str(monitoring_dir) if monitoring_dir else None
    )
    
    # Start monitoring thread if using dashboard and monitor_only
    monitor_thread = None
    if ctx.obj['dashboard'] and monitor_only:
        monitor_thread = ProgressMonitoringThread(
            processor, 
            update_interval=0.5,
            dashboard=True
        )
        monitor_thread.start()
    
    try:
        result = processor.process_markdown_file(
            file_path=input_file,
            output_dir=output_dir
        )
        
        # Stop monitoring thread
        if monitor_thread:
            monitor_thread.stop()
            time.sleep(1)  # Give it time to clean up
        
        # Print final results
        if not monitor_only:
            click.echo(f"\n{'='*60}")
            click.echo(f"✓ Successfully processed: {input_file}")
            click.echo(f"✓ Sections found: {result.sections_found}")
            click.echo(f"✓ Elements found: {result.elements_found}")
            click.echo(f"✓ Chunks processed: {result.chunks_processed}")
            click.echo(f"✓ Token usage: {result.total_tokens_used.get('input', 0)} input, {result.total_tokens_used.get('output', 0)} output")
        else:
            # Clear screen and show final summary
            print("\033[2J\033[H", end="")
            click.echo(f"{'='*80}")
            click.echo(f"🎉 PROCESSING COMPLETED!")
            click.echo(f"{'='*80}")
            click.echo(f"📄 File: {input_file.name}")
            click.echo(f"✅ Sections found: {result.sections_found}")
            click.echo(f"✅ Elements found: {result.elements_found}")
            click.echo(f"✅ Chunks processed: {result.chunks_processed}")
            click.echo(f"🪙 Token usage: {result.total_tokens_used.get('input', 0):,} input, {result.total_tokens_used.get('output', 0):,} output")
            
            if output_dir:
                click.echo(f"💾 Results saved to: {output_dir}")
            if monitoring_dir and save_progress:
                click.echo(f"📊 Monitoring reports saved to: {monitoring_dir}")
        
        if result.errors:
            click.echo(f"\n⚠ Errors encountered: {len(result.errors)}", err=True)
            for error in result.errors[:3]:  # Show first 3 errors
                click.echo(f"  ✗ {error}", err=True)
            if len(result.errors) > 3:
                click.echo(f"  ... and {len(result.errors) - 3} more errors", err=True)
        
        if result.warnings:
            click.echo(f"\n⚠ Warnings: {len(result.warnings)}")
            for warning in result.warnings[:3]:  # Show first 3 warnings
                click.echo(f"  ⚠ {warning}")
            if len(result.warnings) > 3:
                click.echo(f"  ... and {len(result.warnings) - 3} more warnings")
        
        sys.exit(0 if not result.errors else 1)
        
    except KeyboardInterrupt:
        if monitor_thread:
            monitor_thread.stop()
        click.echo(f"\n\n⚠ Processing interrupted by user")
        
        # Try to get partial report
        partial_report = processor.get_partial_report()
        if partial_report:
            click.echo(f"📊 Progress when interrupted:")
            click.echo(f"  Chunks completed: {partial_report.progress.chunks_completed}/{partial_report.progress.total_chunks}")
            click.echo(f"  Sections found: {partial_report.progress.sections_found}")
            click.echo(f"  Elements found: {partial_report.progress.elements_found}")
            
            if save_progress and monitoring_dir:
                # Save final partial report
                import json
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"interrupted_report_{timestamp}.json"
                filepath = monitoring_dir / filename
                monitoring_dir.mkdir(parents=True, exist_ok=True)
                
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        json.dump(partial_report.dict(), f, indent=2, ensure_ascii=False, default=str)
                    click.echo(f"💾 Partial progress saved to: {filepath}")
                except Exception as e:
                    click.echo(f"❌ Failed to save partial progress: {e}", err=True)
        
        sys.exit(130)  # Standard exit code for Ctrl+C
        
    except Exception as e:
        if monitor_thread:
            monitor_thread.stop()
        logging.exception(f"Error processing file {input_file}: {e}")
        click.echo(f"✗ Error processing file: {e}", err=True)
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command('process-batch')
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    '--output-dir', '-o',
    type=click.Path(path_type=Path),
    help='Output directory for JSON results (default: input_dir/json_output)'
)
@click.option(
    '--monitor-only',
    is_flag=True,
    help='Only show monitoring, do not display verbose logs'
)
@click.option(
    '--save-progress',
    is_flag=True,
    help='Save progress reports to files'
)
@click.option(
    '--continue-on-error',
    is_flag=True,
    help='Continue processing other files if one fails'
)
@click.pass_context
def process_batch(ctx, input_dir, output_dir, monitor_only, save_progress, continue_on_error):
    """Process all markdown files in a directory with monitoring."""
    
    # Find all markdown files
    markdown_files = list(input_dir.glob("*.md")) + list(input_dir.glob("*.markdown"))
    
    if not markdown_files:
        click.echo(f"✗ No markdown files found in: {input_dir}", err=True)
        sys.exit(1)
    
    click.echo(f"Found {len(markdown_files)} markdown files to process")
    
    # Initialize LLM client with specified providers
    llm_client = LLMClient(
        providers=ctx.obj['providers'],
        retry_attempts=ctx.obj['retry_attempts'],
        retry_delay=1.0,
        retry_backoff=2.0
    )
    
    # Process each file
    total_sections = 0
    total_elements = 0
    total_errors = 0
    successful_files = 0
    processing_times = []
    
    for i, file_path in enumerate(markdown_files, 1):
        click.echo(f"\n{'='*60}")
        click.echo(f"[{i}/{len(markdown_files)}] Processing: {file_path.name}")
        click.echo(f"{'='*60}")
        
        # Determine directories for this file
        file_output_dir = output_dir or file_path.parent / "json_output"
        monitoring_dir = ctx.obj['monitoring_dir'] or file_output_dir / "monitoring"
        
        # Create progress callback for this file
        progress_callback = None
        if ctx.obj['dashboard'] and not monitor_only:
            progress_callback = create_dashboard_callback(update_interval=1.0)
        elif not ctx.obj['dashboard']:
            def file_progress_callback(report):
                completion = report.get_completion_percentage()
                phase = report.progress.current_phase.value
                print(f"\r  [{completion:5.1f}%] {file_path.name} - Phase: {phase} | "
                      f"Chunks: {report.progress.chunks_completed}/{report.progress.total_chunks}", end="")
            progress_callback = file_progress_callback
        
        # Add file saving callback if requested
        if save_progress:
            file_callback = save_report_callback(str(monitoring_dir))
            if progress_callback:
                def combined_callback(report):
                    progress_callback(report)
                    file_callback(report)
                progress_callback = combined_callback
            else:
                progress_callback = file_callback
        
        # Initialize processor
        processor = MarkdownChunkProcessor(
            llm_client=llm_client,
            chunk_size=ctx.obj['chunk_size'],
            chunk_overlap=ctx.obj['chunk_overlap'],
            verbose=ctx.obj['verbose'] and not monitor_only,
            retry_attempts=ctx.obj['retry_attempts'],
            progress_callback=progress_callback,
            auto_save_interval=ctx.obj['auto_save_interval'],
            auto_save_dir=str(monitoring_dir) if monitoring_dir else None
        )
        
        # Start monitoring thread if using dashboard and monitor_only
        monitor_thread = None
        if ctx.obj['dashboard'] and monitor_only:
            monitor_thread = ProgressMonitoringThread(
                processor, 
                update_interval=0.5,
                dashboard=True
            )
            monitor_thread.start()
        
        start_time = time.time()
        
        try:
            result = processor.process_markdown_file(
                file_path=file_path,
                output_dir=file_output_dir
            )
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            # Stop monitoring thread
            if monitor_thread:
                monitor_thread.stop()
                time.sleep(0.5)  # Give it time to clean up
            
            total_sections += result.sections_found
            total_elements += result.elements_found
            total_errors += len(result.errors)
            
            if not result.errors:
                successful_files += 1
                click.echo(f"\n  ✓ Success: {result.sections_found} sections, {result.elements_found} elements ({processing_time:.1f}s)")
            else:
                click.echo(f"\n  ⚠ Completed with errors: {len(result.errors)} errors ({processing_time:.1f}s)", err=True)
                if ctx.obj['verbose']:
                    for error in result.errors[:2]:
                        click.echo(f"    ✗ {error}", err=True)
            
        except KeyboardInterrupt:
            if monitor_thread:
                monitor_thread.stop()
            click.echo(f"\n\n⚠ Batch processing interrupted by user")
            break
            
        except Exception as e:
            if monitor_thread:
                monitor_thread.stop()
                
            total_errors += 1
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            click.echo(f"\n  ✗ Error: {e} ({processing_time:.1f}s)", err=True)
            if ctx.obj['verbose']:
                import traceback
                traceback.print_exc()
            
            if not continue_on_error:
                click.echo(f"Stopping batch processing due to error. Use --continue-on-error to process remaining files.")
                break
    
    # Print summary
    click.echo(f"\n{'='*60}")
    click.echo(f"🎯 BATCH PROCESSING SUMMARY")
    click.echo(f"{'='*60}")
    click.echo(f"Files processed: {len(processing_times)}/{len(markdown_files)}")
    click.echo(f"Successful: {successful_files}")
    click.echo(f"Failed: {len(processing_times) - successful_files}")
    click.echo(f"Total sections found: {total_sections}")
    click.echo(f"Total elements found: {total_elements}")
    click.echo(f"Total errors: {total_errors}")
    
    if processing_times:
        avg_time = sum(processing_times) / len(processing_times)
        total_time = sum(processing_times)
        click.echo(f"Average processing time: {avg_time:.1f}s")
        click.echo(f"Total processing time: {total_time:.1f}s")
    
    sys.exit(0 if total_errors == 0 else 1)


@cli.command('validate')
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--show-chunks',
    is_flag=True,
    help='Show preview of chunks'
)
@click.option(
    '--analyze-patterns',
    is_flag=True,
    help='Analyze content patterns in detail'
)
@click.pass_context
def validate_file(ctx, input_file, show_chunks, analyze_patterns):
    """Validate a markdown file structure without full processing."""
    
    # Initialize processor with minimal settings for validation
    processor = MarkdownChunkProcessor(
        chunk_size=ctx.obj['chunk_size'],
        chunk_overlap=ctx.obj['chunk_overlap'],
        verbose=ctx.obj['verbose']
    )
    
    try:
        click.echo(f"Validating markdown file: {input_file}")
        
        # Read and chunk the file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = processor._chunk_markdown(content)
        
        click.echo(f"✓ File successfully read: {len(content):,} characters")
        click.echo(f"✓ Split into {len(chunks)} chunks")
        click.echo(f"✓ Chunk size: {ctx.obj['chunk_size']:,} characters")
        click.echo(f"✓ Chunk overlap: {ctx.obj['chunk_overlap']:,} characters")
        
        # Analyze chunk distribution
        chunk_sizes = [len(chunk) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        min_size = min(chunk_sizes)
        max_size = max(chunk_sizes)
        
        click.echo(f"\n📊 Chunk Analysis:")
        click.echo(f"  Average size: {avg_size:,.0f} characters")
        click.echo(f"  Size range: {min_size:,} - {max_size:,} characters")
        
        # Look for potential section/element patterns
        section_pattern = r'^#\s+.*$'
        element_pattern = r'^\*\*.*\*\*'
        table_pattern = r'^\|.*\|.*\|'
        
        sections_found = len(re.findall(section_pattern, content, re.MULTILINE))
        elements_found = len(re.findall(element_pattern, content, re.MULTILINE))
        tables_found = len(re.findall(table_pattern, content, re.MULTILINE))
        
        click.echo(f"\n🔍 Content Analysis (patterns only):")
        click.echo(f"  Potential sections (# headers): {sections_found}")
        click.echo(f"  Potential elements (**bold**): {elements_found}")
        click.echo(f"  Potential tables (| ... |): {tables_found}")
        
        if analyze_patterns:
            click.echo(f"\n📋 Detailed Pattern Analysis:")
            
            # Find section headers
            section_matches = re.finditer(section_pattern, content, re.MULTILINE)
            section_previews = []
            for i, match in enumerate(section_matches):
                if i < 5:  # Show first 5
                    section_previews.append(match.group().strip()[:60] + "..." if len(match.group().strip()) > 60 else match.group().strip())
            
            if section_previews:
                click.echo(f"  Sample sections:")
                for preview in section_previews:
                    click.echo(f"    • {preview}")
                if sections_found > 5:
                    click.echo(f"    ... and {sections_found - 5} more sections")
            
            # Find element headers
            element_matches = re.finditer(element_pattern, content, re.MULTILINE)
            element_previews = []
            for i, match in enumerate(element_matches):
                if i < 5:  # Show first 5
                    element_previews.append(match.group().strip()[:60] + "..." if len(match.group().strip()) > 60 else match.group().strip())
            
            if element_previews:
                click.echo(f"  Sample elements:")
                for preview in element_previews:
                    click.echo(f"    • {preview}")
                if elements_found > 5:
                    click.echo(f"    ... and {elements_found - 5} more elements")
        
        if show_chunks:
            click.echo(f"\n📝 Chunk Preview:")
            for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
                click.echo(f"  Chunk {i+1} ({len(chunk):,} chars):")
                preview = chunk[:200].replace('\n', '\\n')
                if len(chunk) > 200:
                    preview += "..."
                click.echo(f"    {preview}")
                click.echo()
            if len(chunks) > 3:
                click.echo(f"  ... and {len(chunks) - 3} more chunks")
        
        # Estimate processing time
        estimated_chunks_per_minute = 6  # Conservative estimate
        estimated_minutes = len(chunks) / estimated_chunks_per_minute
        
        click.echo(f"\n⏱️  Processing Estimates:")
        click.echo(f"  Estimated processing time: {estimated_minutes:.1f} minutes")
        click.echo(f"  Estimated tokens (rough): {len(content) * 0.75:,.0f}")
        
        sys.exit(0)
        
    except Exception as e:
        click.echo(f"✗ Error validating file: {e}", err=True)
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command('monitor')
@click.argument('partial_report_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--update-interval',
    type=float,
    default=2.0,
    help='Update interval in seconds (default: 2.0)'
)
def monitor_report(partial_report_file, update_interval):
    """Monitor a saved partial report file (for debugging or analysis)."""
    
    from src.utils.monitoring_utils import load_partial_report
    
    try:
        click.echo(f"Loading partial report: {partial_report_file}")
        
        report = load_partial_report(str(partial_report_file))
        if not report:
            click.echo(f"✗ Failed to load partial report", err=True)
            sys.exit(1)
        
        # Create dashboard callback
        dashboard_callback = create_dashboard_callback(update_interval=0)
        
        # Display the report
        dashboard_callback(report)
        
        click.echo(f"\n📊 Report Analysis:")
        click.echo(f"  File: {Path(report.file_path).name}")
        click.echo(f"  Processing phase: {report.progress.current_phase.value}")
        click.echo(f"  Completion: {report.get_completion_percentage():.1f}%")
        click.echo(f"  Start time: {report.progress.start_time}")
        click.echo(f"  Last update: {report.progress.last_update}")
        
        if report.errors:
            click.echo(f"\n❌ Errors ({len(report.errors)}):")
            for error in report.errors[:5]:
                click.echo(f"  • {error}")
            if len(report.errors) > 5:
                click.echo(f"  ... and {len(report.errors) - 5} more errors")
        
        if report.warnings:
            click.echo(f"\n⚠️  Warnings ({len(report.warnings)}):")
            for warning in report.warnings[:5]:
                click.echo(f"  • {warning}")
            if len(report.warnings) > 5:
                click.echo(f"  ... and {len(report.warnings) - 5} more warnings")
        
    except Exception as e:
        click.echo(f"✗ Error monitoring report: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
