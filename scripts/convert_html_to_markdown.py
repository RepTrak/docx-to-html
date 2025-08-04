#!/usr/bin/env python3
"""
Command-line script for converting HTML files to Markdown format.
"""

import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.html.html_to_markdown_service import HtmlToMarkdownService


def convert_file(args):
    """Convert a single HTML file to Markdown."""
    service = HtmlToMarkdownService(verbose=args.verbose)
    
    try:
        output_path = service.convert_file(
            input_path=Path(args.input_file),
            output_dir=Path(args.output_dir) if args.output_dir else None
        )
        print(f"✓ Successfully converted: {args.input_file}")
        print(f"✓ Output file: {output_path}")
        return 0
    except Exception as e:
        print(f"✗ Error converting file: {e}", file=sys.stderr)
        return 1


def convert_batch(args):
    """Convert all HTML files in a directory to Markdown."""
    service = HtmlToMarkdownService(verbose=args.verbose)
    
    try:
        results = service.convert_batch(
            input_dir=Path(args.input_dir),
            output_dir=Path(args.output_dir) if args.output_dir else None
        )
        
        successful = sum(1 for r in results if r['status'] == 'success')
        failed = sum(1 for r in results if r['status'] == 'error')
        
        print(f"\n✓ Batch conversion completed:")
        print(f"  - Successfully converted: {successful} files")
        if failed > 0:
            print(f"  - Failed conversions: {failed} files")
            for result in results:
                if result['status'] == 'error':
                    print(f"    ✗ {result['file']}: {result['error']}")
        
        return 0 if failed == 0 else 1
        
    except Exception as e:
        print(f"✗ Error during batch conversion: {e}", file=sys.stderr)
        return 1


def convert_from_mapping(args):
    """Convert HTML files to Markdown using a mapping file."""
    service = HtmlToMarkdownService(verbose=args.verbose)
    
    try:
        mapping = service.convert_from_mapping(
            mapping_file=Path(args.mapping_file),
            output_dir=Path(args.output_dir) if args.output_dir else None
        )
        
        stats = mapping['metadata']['conversion_stats']
        print(f"\n✓ Mapping-based conversion completed:")
        print(f"  - Sections converted: {stats['sections_converted']}")
        print(f"  - Questions converted: {stats['questions_converted']}")
        
        if stats['errors']:
            print(f"  - Errors encountered: {len(stats['errors'])}")
            for error in stats['errors'][:5]:  # Show first 5 errors
                print(f"    ✗ {error}")
            if len(stats['errors']) > 5:
                print(f"    ... and {len(stats['errors']) - 5} more errors")
        
        return 0 if not stats['errors'] else 1
        
    except Exception as e:
        print(f"✗ Error during mapping-based conversion: {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert HTML files to Markdown format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single HTML file
  %(prog)s convert-file input.html
  
  # Convert a single HTML file to specific output directory
  %(prog)s convert-file input.html --output-dir ./markdown_output
  
  # Convert all HTML files in a directory
  %(prog)s convert-batch ./html_files
  
  # Convert using a mapping file (from HTML splitting)
  %(prog)s convert-from-mapping sections_questions_mapping.json
        """
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='COMMAND'
    )
    
    # Convert single file command
    file_parser = subparsers.add_parser(
        'convert-file',
        help='Convert a single HTML file to Markdown'
    )
    file_parser.add_argument(
        'input_file',
        help='Path to the HTML file to convert'
    )
    file_parser.add_argument(
        '--output-dir', '-o',
        help='Output directory for the markdown file (default: same as input file)'
    )
    
    # Convert batch command
    batch_parser = subparsers.add_parser(
        'convert-batch',
        help='Convert all HTML files in a directory to Markdown'
    )
    batch_parser.add_argument(
        'input_dir',
        help='Directory containing HTML files to convert'
    )
    batch_parser.add_argument(
        '--output-dir', '-o',
        help='Output directory for markdown files (default: same as input directory)'
    )
    
    # Convert from mapping command
    mapping_parser = subparsers.add_parser(
        'convert-from-mapping',
        help='Convert HTML files to Markdown using a mapping file'
    )
    mapping_parser.add_argument(
        'mapping_file',
        help='Path to the sections_questions_mapping.json file'
    )
    mapping_parser.add_argument(
        '--output-dir', '-o',
        help='Output directory for markdown files (default: same directory as mapping file)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute the appropriate command
    if args.command == 'convert-file':
        return convert_file(args)
    elif args.command == 'convert-batch':
        return convert_batch(args)
    elif args.command == 'convert-from-mapping':
        return convert_from_mapping(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
