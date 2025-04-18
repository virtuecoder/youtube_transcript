#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from typing import Optional
from youtube_transcript.utils.file_splitter import FileSplitter

def main() -> int:
    """Main entry point for the file splitter CLI."""
    parser = argparse.ArgumentParser(
        description='Split large files while preserving H2 sections'
    )
    parser.add_argument('file_path', help='Path to file to split')
    parser.add_argument('--output-dir', help='Output directory (default: same as input)')
    parser.add_argument('--max-chars', type=int, default=500000,
                      help='Maximum characters per output file (default: 500000)')
    parser.add_argument('--max-size-mb', type=int, default=200,
                      help='Maximum file size in MB (default: 200)')

    args = parser.parse_args()
    
    try:
        splitter = FileSplitter(
            max_chars=args.max_chars,
            max_size_mb=args.max_size_mb
        )
        
        print(f"Splitting file: {args.file_path}")
        output_files = splitter.split_file(
            args.file_path,
            args.output_dir
        )
        
        print("\nSuccessfully created:")
        for file_path in output_files:
            print(f"- {file_path}")
            
        return 0
        
    except Exception as e:
        print(f"\nError splitting file: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
