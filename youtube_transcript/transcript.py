import os
import json
import time
from typing import Optional, Tuple, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from .video import Video
from .utils.exceptions import (
    TranscriptError,
    TranscriptsDisabled,
    NoTranscriptFound,
    InvalidVideoError
)


class Transcript:
    """Handles YouTube transcript downloading and processing."""
    
    def __init__(self, video: Video, output_dir: str = 'output'):
        """
        Initialize with a Video instance and output directory.
        
        Args:
            video: Video instance
            output_dir: Base directory for transcript storage
        """
        self.video = video
        self.output_dir = output_dir
        self._transcript_data = None
        
    @property
    def transcript_path(self) -> str:
        """Get the full path where transcript should be stored."""
        # Get channel username from URL (after @ symbol)
        channel_url = self.video.channel_url
        channel_username = channel_url.split('@')[-1].split('/')[0] if '@' in channel_url else 'channel'
        
        channel_subfolder = os.path.join(self.output_dir, channel_username)
        os.makedirs(channel_subfolder, exist_ok=True)
        return os.path.join(
            channel_subfolder,
            f'{self.video.video_id}.json'
        )
        
    def download(self) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Download and save transcript for the video.
        
        Returns:
            Tuple of (status, transcript_data)
            Status can be: 'success', 'skipped', 'disabled', 'not_found', 'error'
        """
        if os.path.exists(self.transcript_path):
            try:
                with open(self.transcript_path, 'r') as f:
                    existing_data = json.load(f)
                    return 'skipped', existing_data
            except Exception as e:
                return 'skipped', None
                
        if self.video.is_live:
            return self._save_error_status('live_event')
            
        if self.video.is_unavailable:
            return self._save_error_status('video_unavailable')
            
        try:
            transcript = YouTubeTranscriptApi.get_transcript(self.video.video_id)
            
            # Remove duration from transcripts
            for item in transcript:
                if 'duration' in item:
                    del item['duration']
                    
            self._transcript_data = {
                'title': self.video.title,
                'video_id': self.video.video_id,
                'published_date': self.video.published_date,
                'transcript': transcript
            }
            
            # Save to temporary file first
            temp_path = f'{self.transcript_path}.tmp'
            with open(temp_path, 'w') as f:
                json.dump(self._transcript_data, f, indent=2)
                
            # Verify and rename
            if not os.path.exists(temp_path):
                raise TranscriptError("Failed to write transcript file")
                
            os.rename(temp_path, self.transcript_path)
            return 'success', self._transcript_data
            
        except TranscriptsDisabled:
            return self._save_error_status('transcripts_disabled')
        except NoTranscriptFound:
            return self._save_error_status('no_transcript_found')
        except Exception as e:
            return self._save_error_status(str(e))
            
    def _save_error_status(self, error_type: str) -> Tuple[str, None]:
        """Save error status to transcript file and return status."""
        error_data = {
            'title': self.video.title,
            'video_id': self.video.video_id,
            'error': error_type,
            'published_date': self.video.published_date
        }
        
        with open(self.transcript_path, 'w') as f:
            json.dump(error_data, f)
            
        return error_type.split('_')[0] if '_' in error_type else 'error', None
        
    def get_transcript_text(self) -> Optional[str]:
        """Get the full transcript text if available."""
        if self._transcript_data is None:
            if not os.path.exists(self.transcript_path):
                return None
                
            with open(self.transcript_path, 'r') as f:
                data = json.load(f)
                
            if 'transcript' not in data:
                return None
                
            self._transcript_data = data
            
        return ' '.join(item['text'] for item in self._transcript_data['transcript'])
