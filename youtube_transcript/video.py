from typing import Optional
import yt_dlp
from .utils.exceptions import InvalidVideoError, CookieError


class Video:
    """Handles YouTube video information and operations."""
    
    def __init__(self, video_id: str, cookies: Optional[str] = None, channel_url: Optional[str] = None):
        """
        Initialize with video ID and optional cookies file.
        
        Args:
            video_id: YouTube video ID
            cookies: Path to cookies file for authenticated requests
            channel_url: URL of the YouTube channel this video belongs to
        """
        self.video_id = video_id
        self.cookies = cookies
        self.channel_url = channel_url
        self._title = None
        self._is_live = None
        self._is_unavailable = None
        self._published_date = None
        
    @property
    def url(self) -> str:
        """Get the full YouTube URL for this video."""
        return f"https://www.youtube.com/watch?v={self.video_id}"
        
    @property
    def title(self) -> str:
        """Get video title (fetches if not already cached)."""
        if self._title is None:
            self._fetch_video_info()
        return self._title
        
    @property
    def is_live(self) -> bool:
        """Check if video is a live stream (fetches if not already cached)."""
        if self._is_live is None:
            self._fetch_video_info()
        return self._is_live
        
    @property
    def is_unavailable(self) -> bool:
        """Check if video is unavailable (fetches if not already cached)."""
        if self._is_unavailable is None:
            self._fetch_video_info()
        return self._is_unavailable
        
    def _fetch_video_info(self) -> None:
        """Fetch and cache video information."""
        ydl_opts = {
            'quiet': True,
            'skip_download': True
        }
        
        if self.cookies:
            ydl_opts['cookiefile'] = self.cookies
            
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.url, download=False)
                
                # Get video title (sanitize for filesystem)
                self._title = info.get('title', 'unknown').replace('/', '-').replace('\\', '-')[:100]
                
                # Check live status
                self._is_live = info.get('is_live') or info.get('live_status') in ('upcoming', 'live')
                
                # Check availability
                self._is_unavailable = info.get('availability') == 'unavailable' or 'Video unavailable' in str(info)
                
                # Get published date
                self._published_date = info.get('upload_date')
                
        except yt_dlp.utils.DownloadError as e:
            if 'Video unavailable' in str(e):
                self._is_unavailable = True
                self._title = 'unavailable'
                return
            raise InvalidVideoError(f"Error getting video info: {e}") from e
        except Exception as e:
            if self.cookies and 'cookies' in str(e).lower():
                raise CookieError(f"Cookie error: {e}") from e
            raise InvalidVideoError(f"Error getting video info: {e}") from e
            
    @property
    def published_date(self) -> Optional[str]:
        """Get video published date (fetches if not already cached)."""
        if self._published_date is None:
            self._fetch_video_info()
        return self._published_date

    def get_safe_title(self) -> str:
        """
        Get a filesystem-safe version of the video title.
        
        Returns:
            Safe title string with special characters replaced
        """
        safe_chars = (' ', '-', '_')
        safe_title = "".join(
            c if c.isalnum() or c in safe_chars else '_' 
            for c in self.title
        ).rstrip()
        
        return safe_title[:100] if safe_title else f"video_{self.video_id}"
