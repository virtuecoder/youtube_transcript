import os
import sys
import time
import argparse
from datetime import timedelta
from typing import List, Dict, Any, Optional
from .channel import Channel
from .video import Video
from .transcript import Transcript
from .audio import Audio
from .output import Output
from .utils.exceptions import (
    YouTubeTranscriptError,
    ChannelInfoError,
    VideoFetchError,
    TranscriptError,
    AudioDownloadError
)


class YouTubeTranscriptCLI:
    """Command-line interface for YouTube transcript downloader."""
    
    def __init__(self):
        import logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # Create console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)
        
        self.progress = {
            'status': 'initializing',
            'completed': 0,
            'failed': []
        }
        self.stats = {
            'success': 0,
            'skipped': 0,
            'disabled': 0,
            'disabled_with_audio': 0,
            'not_found': 0,
            'not_found_with_audio': 0,
            'error': 0,
            'live': 0
        }
        self.successful_transcripts = []
        
    def parse_args(self, args: List[str] = None) -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(
            description='Download YouTube transcripts and optionally audio/transcriptions'
        )
        parser.add_argument('channel_url', help='URL of the YouTube channel')
        parser.add_argument('--audio', action='store_true', 
                          help='Download audio when transcripts are unavailable')
        parser.add_argument('--cookies', help='Path to cookies file (e.g., cookies.txt)')
        parser.add_argument('--cookies-from-browser', 
                          choices=['chrome', 'firefox', 'opera', 'edge', 'safari'],
                          help='Extract cookies from browser')
        parser.add_argument('--output-format', choices=['markdown', 'html'], default='markdown',
                          help='Output format for merged transcripts')
        parser.add_argument('--output-file', help='Custom output filename (without extension)')
        return parser.parse_args(args)
        
    def run(self, args: List[str] = None) -> int:
        """Main entry point for the CLI application."""
        start_time = time.time()
        self.args = self.parse_args(args)
        
        try:
            # Handle cookies
            cookies_file = self._handle_cookies(self.args)
            
            # Initialize channel
            channel = Channel(self.args.channel_url, cookies_file)
            self._update_progress(channel_url=self.args.channel_url)
            
            print(f"Processing channel: {self.args.channel_url}")
            self._print_channel_info(channel)
            
            # Fetch all videos
            video_urls = self._fetch_all_videos(channel)
            if not video_urls:
                print("No videos found for this channel")
                return 1
                
            print(f"\nFound {len(video_urls)} videos to process")
            self._update_progress(total_videos=len(video_urls), status='processing')
            
            # Process each video
            self._process_videos(video_urls, channel, self.args.audio, cookies_file)
            
            # Print summary
            self._print_summary(self.args.audio)
            
            # Process audio transcripts if requested
            if self.args.audio:
                self._process_audio_transcripts(video_urls)
                
            # Create merged output file
            output_file = self._create_output_file(channel.name, self.args.channel_url, self.args.output_format, self.args.output_file)
            if output_file:
                print(f"\nTranscripts merged into: {output_file}")
                
        except KeyboardInterrupt:
            print("\nProcess interrupted. Partial results saved.")
            self._update_progress(status='interrupted')
            if self.successful_transcripts:
                output_file = self._create_output_file(
                    channel.name, self.args.channel_url, self.args.output_format, self.args.output_file
                )
                if output_file:
                    print(f"Partial transcripts merged into: {output_file}")
            return 1
        except YouTubeTranscriptError as e:
            print(f"\nError: {e}", file=sys.stderr)
            return 1
            
        elapsed = time.time() - start_time
        print(f"\nTotal execution time: {timedelta(seconds=elapsed)}")
        return 0
        
    def _handle_cookies(self, args: argparse.Namespace) -> Optional[str]:
        """Handle cookie-related arguments and return cookies file path."""
        cookies_file = args.cookies
        
        # Try to extract cookies from browser if requested
        if args.cookies_from_browser and not cookies_file:
            cookies_file = self._get_cookies_from_browser(args.cookies_from_browser)
            
        # Check if cookies file exists
        if cookies_file and not os.path.exists(cookies_file):
            print(f"Warning: Cookies file '{cookies_file}' not found!")
            cookies_file = None
            
        # Check for default cookies.txt
        if not cookies_file and os.path.exists('cookies.txt'):
            cookies_file = 'cookies.txt'
            
        if cookies_file:
            print(f"Using cookies from: {cookies_file}")
        else:
            print("No cookies provided. You may encounter 'Sign in to confirm you're not a bot' errors.")
            print("Use --cookies or --cookies-from-browser to provide authentication.")
            
        return cookies_file
        
    def _get_cookies_from_browser(self, browser: str) -> Optional[str]:
        """Extract cookies from browser using yt-dlp."""
        temp_cookie_file = f"youtube_cookies_{int(time.time())}.txt"
        try:
            ydl_opts = {
                'quiet': True,
                'skip_download': True,
                'cookiesfrombrowser': (browser, None, None, None),
                'cookiefile': temp_cookie_file
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info('https://www.youtube.com/feed/trending', download=False, process=False)
            
            if os.path.exists(temp_cookie_file):
                print(f"Successfully extracted cookies from {browser} to {temp_cookie_file}")
                return temp_cookie_file
            else:
                print(f"Failed to extract cookies from {browser}")
                return None
        except Exception as e:
            print(f"Error extracting cookies from {browser}: {e}")
            return None
            
    def _print_channel_info(self, channel: Channel) -> None:
        """Print channel information."""
        print(f"\nChannel Info:")
        if channel.id:
            print(f"- ID: {channel.id}")
        print(f"- Name: {channel.name}")
        
    def _fetch_all_videos(self, channel: Channel) -> List[str]:
        """Fetch all videos from channel with progress reporting."""
        print("Starting to fetch all videos from channel")
        
        try:
            # Use the improved get_all_videos method
            all_videos = channel.get_all_videos()
            
            if not all_videos:
                print("No videos found for this channel")
                return []
                
            print(f"Successfully fetched {len(all_videos)} videos from channel")
            return all_videos
            
        except Exception as e:
            print(f"Error fetching videos: {e}")
            return []
            
        
    def _process_videos(self, video_urls: List[str], channel: Channel, download_audio: bool, cookies: Optional[str]) -> None:
        """Process each video in the channel."""
        start_time = time.time()
        total_videos = len(video_urls)
        
        print(f"\nStarting to process {total_videos} videos...")
        
        for i, url in enumerate(video_urls, 1):
            video_id = url.split('/')[-1]
            video = Video(video_id, cookies, self.args.channel_url)
            transcript = Transcript(video)
            
            # Calculate progress metrics
            elapsed = time.time() - start_time
            avg_time_per_video = elapsed / i if i > 1 else 0
            remaining = avg_time_per_video * (total_videos - i)
            
            print(f"\nProcessing video {i}/{total_videos} ({i/total_videos:.1%}) - {video_id}")
            print(f"Elapsed: {timedelta(seconds=int(elapsed))} | Remaining: ~{timedelta(seconds=int(remaining))}")
            
            try:
                status, transcript_data = transcript.download()
                self._update_stats(status)
                
                if transcript_data:
                    self.successful_transcripts.append(transcript_data)
                    
                # Handle audio download if transcript unavailable
                if download_audio and status in ('disabled', 'not_found'):
                    print(f"Transcript {status}, attempting audio download...")
                    audio = Audio(video)
                    if audio.download():
                        print("Audio downloaded successfully")
                        if status == 'disabled':
                            self.stats['disabled_with_audio'] += 1
                            self.stats['disabled'] -= 1
                        else:
                            self.stats['not_found_with_audio'] += 1
                            self.stats['not_found'] -= 1
                            
            except Exception as e:
                print(f"\n⚠️ Skipping video {video_id} due to error: {str(e)}")
                self.stats['skipped'] += 1
                self.progress['failed'].append({
                    'video_id': video_id,
                    'error': str(e),
                    'retry': True
                })
                
            # Update progress
            self._update_progress(
                completed=i,
                last_processed=video_id,
                status=f'processing {i}/{total_videos}',
                stats=self.stats
            )
            
    def _process_audio_transcripts(self, video_urls: List[str]) -> None:
        """Process audio transcripts for videos."""
        print("\nProcessing audio transcripts...")
        audio_transcripts = 0
        
        for url in video_urls:
            video_id = url.split('/')[-1]
            audio = Audio(Video(video_id, channel_url=self.args.channel_url))
            
            if audio.transcribe():
                audio_transcripts += 1
                
        print(f"Successfully transcribed {audio_transcripts} audio files")
        
    def _create_output_file(self, channel_name: str, channel_url: str, output_format: str, filename: Optional[str]) -> Optional[str]:
        """Create merged output file in specified format."""
        if not self.successful_transcripts:
            print("No transcripts to merge")
            return None
            
        output = Output()
        
        if output_format == 'html':
            return output.create_html(
                channel_name,
                channel_url,
                self.successful_transcripts,
                filename
            )
        else:  # markdown
            return output.create_markdown(
                channel_name,
                channel_url,
                self.successful_transcripts,
                filename
            )
            
    def _update_progress(self, **kwargs) -> None:
        """Update progress dictionary."""
        self.progress.update(kwargs)
        # In a real implementation, we might save this to a file
        
    def _update_stats(self, status: str) -> None:
        """Update statistics counters."""
        if status not in self.stats:
            self.stats[status] = 0
        self.stats[status] += 1
        
    def _print_summary(self, audio_enabled: bool) -> None:
        """Print processing summary."""
        print("\nDownload summary:")
        print(f"- Successfully downloaded transcripts: {self.stats.get('success', 0)}")
        print(f"- Skipped (already exists): {self.stats.get('skipped', 0)}")
        print(f"- Live events skipped: {self.stats.get('live', 0)}")
        if audio_enabled:
            print(f"- Transcripts disabled (audio downloaded): {self.stats.get('disabled_with_audio', 0)}")
            print(f"- No transcript found (audio downloaded): {self.stats.get('not_found_with_audio', 0)}")
        print(f"- Transcripts disabled: {self.stats.get('disabled', 0)}")
        print(f"- No transcript found: {self.stats.get('not_found', 0)}")
        print(f"- Errors: {self.stats.get('error', 0)}")


def main():
    """Entry point for console script."""
    cli = YouTubeTranscriptCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()
