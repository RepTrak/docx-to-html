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
from src.utils.file_manager import FileManager, ResultsManager

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
    default=2000,
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
    
    # Initialize file management
    file_manager = FileManager()
    directories = file_manager.setup_output_directories(input_file, output_dir)
    results_manager = ResultsManager(file_manager)
    
    monitoring_dir = ctx.obj['monitoring_dir'] or directories['monitoring']
    
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
    
    logging.info(f"Processing markdown file: {input_file} with chunk size {ctx.obj['chunk_size']} and overlap {ctx.obj['chunk_overlap']}")
    
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
        auto_save_dir=str(directories['temp'])
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
            output_dir=directories['output']
        )
        
        # Stop monitoring thread
        if monitor_thread:
            monitor_thread.stop()
            time.sleep(1)  # Give it time to clean up
        
        # Save results
        try:
            output_path = results_manager.save_processing_result(result, input_file, directories['output'])
            
            # Save error report if there are errors or warnings
            if result.errors or result.warnings:
                results_manager.save_error_report(
                    result.errors, result.warnings, input_file, monitoring_dir
                )
                
        except Exception as e:
            logger.error(f"Failed to save results: {e}")
            click.echo(f"✗ Failed to save results: {e}", err=True)
        
        # Print final results
        if not monitor_only:
            click.echo(f"\n{'='*60}")
            click.echo(f"✓ Successfully processed: {input_file}")
            click.echo(f"✓ Sections found: {result.sections_found}")
            click.echo(f"✓ Elements found: {result.elements_found}")
            click.echo(f"✓ Chunks processed: {result.chunks_processed}")
            click.echo(f"✓ Token usage: {result.total_tokens_used.get('input', 0)} input, {result.total_tokens_used.get('output', 0)} output")
            click.echo(f"💾 Results saved to: {output_path}")
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
            click.echo(f"💾 Results saved to: {output_path}")
            
            if save_progress:
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
        
        # Cleanup temp files
        cleaned_count = file_manager.cleanup_temp_files(directories['temp'])
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} temporary files")
        
        sys.exit(0 if not result.errors else 1)
        
    except KeyboardInterrupt:
        if monitor_thread:
            monitor_thread.stop()
        click.echo(f"\n\n⚠ Processing interrupted by user")
        
        # Try to get partial report and save it
        partial_report = processor.get_partial_report()
        if partial_report and save_progress:
            try:
                filepath = file_manager.save_partial_progress(
                    partial_report.dict() if hasattr(partial_report, 'dict') else partial_report,
                    monitoring_dir,
                    prefix="interrupted_report"
                )
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
    
    # Initialize file management
    file_manager = FileManager()
    directories = file_manager.setup_output_directories(input_dir, output_dir)
    results_manager = ResultsManager(file_manager)
    
    # Find all markdown files
    markdown_files = file_manager.find_markdown_files(input_dir)
    
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
    results = []
    processing_times = []
    successful_files = 0
    
    for i, file_path in enumerate(markdown_files, 1):
        click.echo(f"\n{'='*60}")
        click.echo(f"[{i}/{len(markdown_files)}] Processing: {file_path.name}")
        click.echo(f"{'='*60}")
        
        # Set up directories for this file
        file_directories = file_manager.setup_output_directories(file_path, directories['output'] / file_path.stem)
        monitoring_dir = ctx.obj['monitoring_dir'] or file_directories['monitoring']
        
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
            auto_save_dir=str(file_directories['temp'])
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
                output_dir=file_directories['output']
            )
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            results.append(result)
            
            # Stop monitoring thread
            if monitor_thread:
                monitor_thread.stop()
                time.sleep(0.5)  # Give it time to clean up
            
            # Save results
            try:
                results_manager.save_processing_result(result, file_path, file_directories['output'])
                
                # Save error report if there are errors or warnings
                if result.errors or result.warnings:
                    results_manager.save_error_report(
                        result.errors, result.warnings, file_path, monitoring_dir
                    )
                    
            except Exception as e:
                logger.error(f"Failed to save results for {file_path}: {e}")
            
            if not result.errors:
                successful_files += 1
                click.echo(f"\n  ✓ Success: {result.sections_found} sections, {result.elements_found} elements ({processing_time:.1f}s)")
            else:
                click.echo(f"\n  ⚠ Completed with errors: {len(result.errors)} errors ({processing_time:.1f}s)", err=True)
                if ctx.obj['verbose']:
                    for error in result.errors[:2]:
                        click.echo(f"    ✗ {error}", err=True)
            
            # Cleanup temp files for this file
            file_manager.cleanup_temp_files(file_directories['temp'])
            
        except KeyboardInterrupt:
            if monitor_thread:
                monitor_thread.stop()
            click.echo(f"\n\n⚠ Batch processing interrupted by user")
            break
            
        except Exception as e:
            if monitor_thread:
                monitor_thread.stop()
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
            
            # Create a dummy result for failed processing
            failed_result = type('FailedResult', (), {
                'sections_found': 0, 'elements_found': 0, 'chunks_processed': 0,
                'total_tokens_used': {'input': 0, 'output': 0},
                'errors': [str(e)], 'warnings': []
            })()
            results.append(failed_result)
            
            click.echo(f"\n  ✗ Error: {e} ({processing_time:.1f}s)", err=True)
            if ctx.obj['verbose']:
                import traceback
                traceback.print_exc()
            
            if not continue_on_error:
                click.echo(f"Stopping batch processing due to error. Use --continue-on-error to process remaining files.")
                break
    
    # Generate and save batch summary
    try:
        summary_data = results_manager.generate_processing_summary(results, processing_times, len(markdown_files))
        summary_path = results_manager.save_batch_summary(summary_data, directories['output'])
        
        # Print summary
        click.echo(f"\n{'='*60}")
        click.echo(f"🎯 BATCH PROCESSING SUMMARY")
        click.echo(f"{'='*60}")
        summary = summary_data['processing_summary']
        content = summary_data['content_summary']
        timing = summary_data['timing_summary']
        
        click.echo(f"Files processed: {summary['processed_files']}/{summary['total_files']}")
        click.echo(f"Successful: {summary['successful_files']}")
        click.echo(f"Failed: {summary['failed_files']}")
        click.echo(f"Success rate: {summary['success_rate']:.1f}%")
        click.echo(f"Total sections found: {content['total_sections']}")
        click.echo(f"Total elements found: {content['total_elements']}")
        click.echo(f"Average processing time: {timing['average_processing_time']:.1f}s")
        click.echo(f"Total processing time: {timing['total_processing_time']:.1f}s")
        click.echo(f"💾 Summary saved to: {summary_path}")
        
    except Exception as e:
        logger.error(f"Failed to save batch summary: {e}")
        click.echo(f"✗ Failed to save batch summary: {e}", err=True)
    
    # Cleanup main temp directory
    cleaned_count = file_manager.cleanup_temp_files(directories['temp'])
    if cleaned_count > 0:
        logger.info(f"Cleaned up {cleaned_count} temporary files")
    
    total_errors = sum(len(getattr(r, 'errors', [])) for r in results)
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
