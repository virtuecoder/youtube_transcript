
class YouTubeTranscriptError(Exception):
    """Base exception class for all YouTube transcript related errors."""
    pass

class ChannelInfoError(YouTubeTranscriptError):
    """Raised when there's an error fetching channel information."""
    pass

class VideoFetchError(YouTubeTranscriptError):
    """Raised when there's an error fetching videos from a channel."""
    pass

class TranscriptError(YouTubeTranscriptError):
    """Base exception for transcript-related errors."""
    pass

class TranscriptsDisabled(TranscriptError):
    """Raised when transcripts are disabled for a video."""
    pass

class NoTranscriptFound(TranscriptError):
    """Raised when no transcript is found for a video."""
    pass

class AudioDownloadError(YouTubeTranscriptError):
    """Raised when there's an error downloading audio."""
    pass

class TranscriptionError(YouTubeTranscriptError):
    """Raised when there's an error transcribing audio."""
    pass

class RateLimitError(YouTubeTranscriptError):
    """Raised when rate limited by YouTube."""
    pass

class InvalidVideoError(YouTubeTranscriptError):
    """Raised when a video is invalid or unavailable."""
    pass

class CookieError(YouTubeTranscriptError):
    """Raised when there are issues with cookies."""
    pass

class OutputError(YouTubeTranscriptError):
    """Raised when there's an error with output operations."""
    pass
