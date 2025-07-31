#!/usr/bin/env python3
"""
CLI script to split HTML files into sections and questions.
"""
import click
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.html.processor import HTMLProcessor


@click.command()
@click.argument('input_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output-dir', '-o',
    type=click.Path(path_type=Path),
    default=None,
    help='Output directory for processed files. Defaults to input file directory + "_processed"'
)
@click.option(
    '--sections/--no-sections',
    default=True,
    help='Extract sections from HTML (default: True)'
)
@click.option(
    '--questions/--no-questions',
    default=True,
    help='Extract questions from HTML (default: True)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
def split_html(input_file: Path, output_dir: Path, sections: bool, questions: bool, verbose: bool):
    """
    Split HTML files into sections and questions.
    
    INPUT_FILE: Path to the HTML file to process
    """
    if verbose:
        click.echo(f"Input file: {input_file}")
    
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = input_file.parent / f"{input_file.stem}_processed"
    
    if verbose:
        click.echo(f"Output directory: {output_dir}")
        click.echo(f"Extract sections: {sections}")
        click.echo(f"Extract questions: {questions}")
    
    try:
        processor = HTMLProcessor(str(input_file), str(output_dir))
        processor.process(extract_sections=sections, extract_questions=questions)
        
        click.echo(click.style("✓ Processing completed successfully!", fg='green'))
        
    except FileNotFoundError as e:
        click.echo(click.style(f"Error: {e}", fg='red'), err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(click.style(f"Unexpected error: {e}", fg='red'), err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@click.command()
@click.argument('input_dir', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--output-dir', '-o',
    type=click.Path(path_type=Path),
    default=None,
    help='Output directory for processed files. Defaults to input directory + "_processed"'
)
@click.option(
    '--sections/--no-sections',
    default=True,
    help='Extract sections from HTML files (default: True)'
)
@click.option(
    '--questions/--no-questions',
    default=True,
    help='Extract questions from HTML files (default: True)'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
def split_html_batch(input_dir: Path, output_dir: Path, sections: bool, questions: bool, verbose: bool):
    """
    Split multiple HTML files in a directory into sections and questions.
    
    INPUT_DIR: Path to directory containing HTML files to process
    """
    html_files = list(input_dir.glob("*.html"))
    
    if not html_files:
        click.echo(click.style("No HTML files found in the input directory.", fg='yellow'))
        return
    
    if verbose:
        click.echo(f"Found {len(html_files)} HTML file(s) to process")
    
    # Set default output directory if not provided
    if output_dir is None:
        output_dir = input_dir / "processed"
    
    for html_file in html_files:
        if verbose:
            click.echo(f"\nProcessing: {html_file.name}")
        
        file_output_dir = output_dir / html_file.stem
        
        try:
            processor = HTMLProcessor(str(html_file), str(file_output_dir))
            processor.process(extract_sections=sections, extract_questions=questions)
            
        except Exception as e:
            click.echo(click.style(f"Error processing {html_file.name}: {e}", fg='red'), err=True)
            if verbose:
                import traceback
                traceback.print_exc()
    
    click.echo(click.style(f"\n✓ Batch processing completed! Output in: {output_dir}", fg='green'))


@click.group()
def cli():
    """HTML processing tools for DOCX to HTML conversion pipeline."""
    pass


cli.add_command(split_html)
cli.add_command(split_html_batch)


if __name__ == '__main__':
    cli()
