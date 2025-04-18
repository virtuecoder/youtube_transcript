import os
import re
from typing import List, Tuple, Optional
from pathlib import Path

class FileSplitter:
    """Utility class for splitting large files while preserving H2 sections."""
    
    def __init__(self, max_chars: int = 2500000, max_size_mb: int = 200):
        """
        Initialize with size constraints.
        
        Args:
            max_chars: Maximum characters per output file
            max_size_mb: Maximum file size in MB
        """
        self.max_chars = max_chars
        self.max_bytes = max_size_mb * 1024 * 1024
        
    def split_file(self, input_path: str, output_dir: str = None) -> List[str]:
        """
        Split input file into smaller files while preserving H2 sections.
        
        Args:
            input_path: Path to input file
            output_dir: Directory for output files (default: same as input)
            
        Returns:
            List of paths to created output files
        """
        input_path = Path(input_path)
        if not output_dir:
            output_dir = input_path.parent
        else:
            output_dir = Path(output_dir)
            
        # Read input file
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Split into H2 sections
        sections = self._split_into_sections(content)
        
        # Group sections into chunks that fit size constraints
        chunks = self._create_chunks(sections)
        
        # Write chunks to files
        output_files = []
        for i, chunk in enumerate(chunks, 1):
            output_path = output_dir / f"{input_path.stem}_part{i}{input_path.suffix}"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(chunk)
            output_files.append(str(output_path))
            
        return output_files
        
    def _split_into_sections(self, content: str) -> List[Tuple[str, int]]:
        """
        Split content into H2 sections with their sizes.
        
        Args:
            content: Input file content
            
        Returns:
            List of (section_content, section_size) tuples
        """
        # Try Markdown H2 first (##)
        markdown_sections = re.split(r'(?=\n##\s)', content)
        if len(markdown_sections) > 1:
            return [(s, len(s.encode('utf-8'))) for s in markdown_sections]
            
        # Fall back to HTML H2
        html_sections = re.split(r'(?=<h2[^>]*>)', content, flags=re.IGNORECASE)
        if len(html_sections) > 1:
            return [(s, len(s.encode('utf-8'))) for s in html_sections]
            
        # No H2 sections found - treat whole content as one section
        return [(content, len(content.encode('utf-8')))]
        
    def _create_chunks(self, sections: List[Tuple[str, int]]) -> List[str]:
        """
        Combine sections into chunks that fit size constraints.
        
        Args:
            sections: List of (content, size) tuples
            
        Returns:
            List of chunk contents
        """
        chunks = []
        current_chunk = []
        current_size = 0
        current_length = 0
        
        for section, size in sections:
            section_length = len(section)
            
            # If section alone exceeds limits, we have to split it
            if size > self.max_bytes or section_length > self.max_chars:
                # Split the oversized section into smaller parts
                split_sections = self._split_oversized_section(section)
                for sub_section, sub_size in split_sections:
                    sub_length = len(sub_section)
                    if (current_size + sub_size > self.max_bytes or 
                        current_length + sub_length > self.max_chars):
                        if current_chunk:  # Only create new chunk if we have content
                            chunks.append(''.join(current_chunk))
                        current_chunk = [sub_section]
                        current_size = sub_size
                        current_length = sub_length
                    else:
                        current_chunk.append(sub_section)
                        current_size += sub_size
                        current_length += sub_length
            else:
                # Try to add to current chunk if possible
                if (current_size + size > self.max_bytes or 
                    current_length + section_length > self.max_chars):
                    if current_chunk:  # Only create new chunk if we have content
                        chunks.append(''.join(current_chunk))
                    current_chunk = [section]
                    current_size = size
                    current_length = section_length
                else:
                    current_chunk.append(section)
                    current_size += size
                    current_length += section_length
                    
        if current_chunk:
            chunks.append(''.join(current_chunk))
            
        # Optimize chunk sizes by redistributing content if we have many small chunks
        if len(chunks) > 1:
            optimized_chunks = []
            temp_chunk = []
            temp_size = 0
            temp_length = 0
            
            for chunk in chunks:
                chunk_size = len(chunk.encode('utf-8'))
                chunk_length = len(chunk)
                
                if (temp_size + chunk_size > self.max_bytes or
                    temp_length + chunk_length > self.max_chars):
                    if temp_chunk:
                        optimized_chunks.append(''.join(temp_chunk))
                    temp_chunk = [chunk]
                    temp_size = chunk_size
                    temp_length = chunk_length
                else:
                    temp_chunk.append(chunk)
                    temp_size += chunk_size
                    temp_length += chunk_length
            
            if temp_chunk:
                optimized_chunks.append(''.join(temp_chunk))
                
            # Only return optimized chunks if we actually reduced the number
            if len(optimized_chunks) < len(chunks):
                return optimized_chunks
                
        return chunks
        
    def _split_oversized_section(self, section: str) -> List[Tuple[str, int]]:
        """
        Split a section that exceeds size limits into smaller parts.
        
        Args:
            section: Section content that's too large
            
        Returns:
            List of (content, size) tuples
        """
        # Split by paragraphs first
        paragraphs = re.split(r'(?<=\n\n)', section)
        if len(paragraphs) > 1:
            return [(p, len(p.encode('utf-8'))) for p in paragraphs]
            
        # Fall back to splitting by sentences
        sentences = re.split(r'(?<=[.!?])\s+', section)
        if len(sentences) > 1:
            return [(s, len(s.encode('utf-8'))) for s in sentences]
            
        # Last resort - split by arbitrary chunks
        chunk_size = min(self.max_chars, self.max_bytes // 2)
        return [
            (section[i:i+chunk_size], len(section[i:i+chunk_size].encode('utf-8')))
            for i in range(0, len(section), chunk_size)
        ]
