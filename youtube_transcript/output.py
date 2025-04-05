import os
import re
from typing import List, Optional, Dict, Any
from pathlib import Path
from .video import Video
from .transcript import Transcript
from .audio import Audio
from .utils.exceptions import OutputError


class Output:
    """Handles generating output files from transcripts and audio."""
    
    def __init__(self, output_dir: str = '.'):
        """
        Initialize with output directory.
        
        Args:
            output_dir: Base directory for output files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def create_markdown(
        self,
        channel_name: str,
        channel_url: str,
        transcripts: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Create a merged markdown file with all transcripts.
        
        Args:
            channel_name: Name of the YouTube channel
            channel_url: URL of the YouTube channel
            transcripts: List of transcript dictionaries
            filename: Optional custom filename (without extension)
            
        Returns:
            Path to the created markdown file
        """
        if not transcripts:
            raise OutputError("No transcripts provided for markdown generation")
            
        # Generate safe filename
        safe_chars = (' ', '-', '_')
        safe_channel_name = "".join(
            c if c.isalnum() or c in safe_chars else '_' 
            for c in channel_name
        ).rstrip()
        
        if not safe_channel_name:
            safe_channel_name = "YouTube_Channel"
            
        output_file = os.path.join(
            self.output_dir,
            f"{filename or safe_channel_name}.md"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# Transcripts for YouTube channel: {channel_name}\n\n")
            f.write(f"Channel URL: {channel_url}\n\n")
            
            # Process each transcript
            for transcript_data in transcripts:
                video_title = transcript_data.get('title', 'Unknown Video')
                video_id = transcript_data.get('video_id', '')
                video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ''
                
                # Video header with title and URL
                f.write(f"## {video_title} - {video_url}\n\n")
                
                # Write transcript text
                transcript_items = transcript_data.get('transcript', [])
                if transcript_items:
                    full_text = " ".join(item.get('text', '') for item in transcript_items)
                    
                    # Split into paragraphs for better readability
                    paragraphs = re.split(r'(?<=[.!?])\s+', full_text)
                    for para in paragraphs:
                        if para.strip():
                            f.write(f"{para.strip()}\n\n")
                else:
                    f.write("No transcript available for this video.\n\n")
                
                # Add separator between videos
                f.write("---\n\n")
        
        return output_file
        
    def create_html(
        self,
        channel_name: str,
        channel_url: str,
        transcripts: List[Dict[str, Any]],
        filename: Optional[str] = None
    ) -> str:
        """
        Create an HTML file with all transcripts.
        
        Args:
            channel_name: Name of the YouTube channel
            channel_url: URL of the YouTube channel
            transcripts: List of transcript dictionaries
            filename: Optional custom filename (without extension)
            
        Returns:
            Path to the created HTML file
        """
        if not transcripts:
            raise OutputError("No transcripts provided for HTML generation")
            
        # Generate safe filename
        safe_chars = (' ', '-', '_')
        safe_channel_name = "".join(
            c if c.isalnum() or c in safe_chars else '_' 
            for c in channel_name
        ).rstrip()
        
        if not safe_channel_name:
            safe_channel_name = "YouTube_Channel"
            
        output_file = os.path.join(
            self.output_dir,
            f"{filename or safe_channel_name}.html"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write HTML header
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcripts for {}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #333; border-bottom: 1px solid #eee; }}
        h2 {{ color: #444; margin-top: 30px; }}
        .video-transcript {{ margin-bottom: 40px; }}
        .separator {{ border-top: 1px dashed #ccc; margin: 30px 0; }}
    </style>
</head>
<body>
    <h1>Transcripts for YouTube channel: {}</h1>
    <p>Channel URL: <a href="{}">{}</a></p>
""".format(channel_name, channel_name, channel_url, channel_url))
            
            # Process each transcript
            for transcript_data in transcripts:
                video_title = transcript_data.get('title', 'Unknown Video')
                video_id = transcript_data.get('video_id', '')
                video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else ''
                
                # Video section
                f.write(f"""
    <div class="video-transcript">
        <h2><a href="{video_url}">{video_title}</a></h2>
""")
                
                # Write transcript text
                transcript_items = transcript_data.get('transcript', [])
                if transcript_items:
                    full_text = " ".join(item.get('text', '') for item in transcript_items)
                    
                    # Split into paragraphs
                    paragraphs = re.split(r'(?<=[.!?])\s+', full_text)
                    for para in paragraphs:
                        if para.strip():
                            f.write(f"        <p>{para.strip()}</p>\n")
                else:
                    f.write("        <p>No transcript available for this video.</p>\n")
                
                f.write("    </div>\n")
                f.write('    <div class="separator"></div>\n')
            
            # Close HTML
            f.write("</body>\n</html>")
        
        return output_file
