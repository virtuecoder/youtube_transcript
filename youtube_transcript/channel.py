import os
import time
from typing import Optional, Tuple, List
import yt_dlp
from .utils.exceptions import ChannelInfoError, VideoFetchError


class Channel:
    """Handles YouTube channel information and video listing operations."""
    
    def __init__(self, url: str, cookies: Optional[str] = None):
        """
        Initialize with channel URL and optional cookies file.
        
        Args:
            url: YouTube channel URL
            cookies: Path to cookies file for authenticated requests
        """
        self.url = url
        self.cookies = cookies
        self._id = None
        self._name = None
        
    @property
    def id(self) -> str:
        """Get channel ID (fetches if not already cached)."""
        if not self._id:
            self._fetch_channel_info()
        return self._id
        
    @property
    def name(self) -> str:
        """Get channel name (fetches if not already cached)."""
        if not self._name:
            self._fetch_channel_info()
        return self._name
        
    def _fetch_channel_info(self) -> None:
        """Fetch and cache channel ID and name."""
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'skip_download': True
        }
        
        if self.cookies:
            ydl_opts['cookiefile'] = self.cookies
            
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                
                # Handle different channel URL formats
                if info.get('channel_id'):
                    self._id = info['channel_id']
                elif info.get('uploader_id'):
                    self._id = info['uploader_id']
                else:
                    raise ChannelInfoError("Could not determine channel ID")
                    
                # Get channel name (fall back to uploader if needed)
                self._name = info.get('channel', info.get('uploader', 'Unknown Channel'))
                
        except Exception as e:
            raise ChannelInfoError(f"Error getting channel info: {e}") from e
            
    def get_videos_page(self, page_token: Optional[str] = None, max_per_page: int = 100) -> Tuple[List[str], Optional[str]]:
        """
        Get a single page of videos from channel.
        
        Args:
            page_token: Continuation token for pagination
            max_per_page: Maximum number of videos to return per page
            
        Returns:
            Tuple of (video_urls, next_page_token)
        """
        if not self.id:
            return [], None

        # Configure retries with delays
        max_retries = 3
        retry_delay = 5  # seconds between retries
        
        ydl_opts = {
            'extract_flat': True,
            'quiet': True,
            # 'playlist_items': f'1-{max_per_page}',
            'extractor_args': {
                'youtube': {
                    'player_client': 'all',
                    'player_skip': ['webpage'],
                    'max_videos': max_per_page
                }
            }
        }
        
        if self.cookies:
            ydl_opts['cookiefile'] = self.cookies
            
        # Use channel videos endpoint 
        base_url = f'https://www.youtube.com/channel/{self.id}/videos'
        if page_token:
            ydl_opts['extractor_args']['youtube']['continuation'] = page_token
        
        # Retry logic with delays    
        for attempt in range(max_retries):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(base_url, download=False)
                    if not info.get('entries'):
                        if attempt < max_retries - 1:
                            time.sleep(retry_delay)
                            continue
                        return [], None
                    
                    videos = [f"https://youtu.be/{entry['id']}" for entry in info['entries']]
                    next_page = info.get('continuation')
                    return videos, next_page
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise VideoFetchError(f"Failed to get videos after {max_retries} attempts: {e}") from e
        
        return [], None

    def get_all_videos(self) -> List[str]:
        """
        Get all videos from channel using pagination.
        
        Returns:
            List of all video URLs
        """
        all_videos = []
        next_page = None
        
        while True:
            page_videos, next_page = self.get_videos_page(next_page)
            all_videos.extend(page_videos)
            if not next_page:
                break
                
        return all_videos
