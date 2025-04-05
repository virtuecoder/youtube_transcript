import os
import subprocess
from typing import Optional, Tuple
import speech_recognition as sr
import yt_dlp
from .video import Video
from .utils.exceptions import (
    AudioDownloadError,
    TranscriptionError,
    InvalidVideoError
)


class Audio:
    """Handles YouTube audio downloading and transcription."""
    
    def __init__(self, video: Video, audio_dir: str = 'audio_files', transcript_dir: str = 'audio_transcripts'):
        """
        Initialize with a Video instance and output directories.
        
        Args:
            video: Video instance
            audio_dir: Directory for storing downloaded audio files
            transcript_dir: Directory for storing audio transcriptions
        """
        self.video = video
        self.audio_dir = audio_dir
        self.transcript_dir = transcript_dir
        os.makedirs(audio_dir, exist_ok=True)
        os.makedirs(transcript_dir, exist_ok=True)
        
    @property
    def audio_path(self) -> str:
        """Get path to audio file for this video."""
        return os.path.join(self.audio_dir, f'{self.video.video_id}.mp3')
        
    @property
    def transcript_path(self) -> str:
        """Get path to transcript file for this video."""
        return os.path.join(self.transcript_dir, f'{self.video.video_id}.txt')
        
    def download(self) -> bool:
        """
        Download audio for the video.
        
        Returns:
            True if audio was downloaded successfully, False otherwise
        """
        if os.path.exists(self.audio_path):
            return True
            
        if self.video.is_live or self.video.is_unavailable:
            return False
            
        # Try multiple download approaches
        attempts = [
            {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                }],
                'outtmpl': f'{self.audio_dir}/{self.video.video_id}.%(ext)s',
                'quiet': True
            },
            {
                'format': 'm4a/bestaudio/best',
                'outtmpl': f'{self.audio_dir}/{self.video.video_id}.%(ext)s',
                'quiet': True
            }
        ]

        for ydl_opts in attempts:
            # Add cookies if provided
            if self.video.cookies:
                ydl_opts['cookiefile'] = self.video.cookies
                
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([self.video.url])
                
                # Check if any file was downloaded
                if os.path.exists(self.audio_path):
                    return True
                    
            except yt_dlp.DownloadError as e:
                if 'age restricted' in str(e).lower():
                    raise AudioDownloadError(
                        "Age-restricted video. Provide cookies for authentication."
                    ) from e
                continue
            except Exception as e:
                raise AudioDownloadError(f"Audio download failed: {e}") from e
                
        return False
        
    def transcribe(self) -> bool:
        """
        Transcribe downloaded audio to text.
        
        Returns:
            True if transcription was successful, False otherwise
        """
        if not os.path.exists(self.audio_path):
            return False
            
        if os.path.exists(self.transcript_path):
            return True
            
        # Convert MP3 to WAV format for speech recognition
        wav_path = os.path.join(self.audio_dir, f'{self.video.video_id}.wav')
        try:
            subprocess.run([
                'ffmpeg',
                '-y',  # Overwrite without asking
                '-i', self.audio_path,
                '-acodec', 'pcm_s16le',  # WAV format
                '-ac', '1',  # Mono channel
                '-ar', '16000',  # 16kHz sample rate
                wav_path
            ], check=True)
        except Exception as e:
            raise TranscriptionError(f"Failed to convert audio to WAV format: {e}") from e
            
        recognizer = sr.Recognizer()
        for _ in range(3):  # Retry up to 3 times
            try:
                with sr.AudioFile(wav_path) as source:
                    # Adjust for ambient noise and read the entire file
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.record(source)
                    
                    try:
                        text = recognizer.recognize_google(audio, show_all=False)
                    except sr.UnknownValueError:
                        raise TranscriptionError("Speech recognition could not understand audio")
                    except sr.RequestError as e:
                        raise TranscriptionError(f"Speech recognition service error: {e}")
                        
                with open(self.transcript_path, 'w') as f:
                    f.write(text)
                    
                # Clean up temporary WAV file
                try:
                    os.remove(wav_path)
                except:
                    pass
                    
                return True
                
            except Exception as e:
                continue
                
        return False
        
    def get_transcription(self) -> Optional[str]:
        """Get the transcription text if available."""
        if not os.path.exists(self.transcript_path):
            return None
            
        with open(self.transcript_path, 'r') as f:
            return f.read()
