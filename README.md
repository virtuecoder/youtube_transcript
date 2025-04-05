# YouTube Transcript Downloader

A Python package for downloading YouTube transcripts and audio with multiple output formats.

## Features

- Download transcripts from YouTube videos and channels
- Fallback to audio download and transcription when transcripts are unavailable
- Multiple output formats (Markdown, HTML)
- Channel-wide processing
- Progress tracking and resumable downloads
- Cookie authentication support

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Usage

### Basic channel transcript download
```bash
yt-transcript https://www.youtube.com/c/ChannelName
```

### With audio fallback
```bash
yt-transcript https://www.youtube.com/c/ChannelName --audio
```

### Using cookies for authentication
```bash
yt-transcript https://www.youtube.com/c/ChannelName --cookies cookies.txt
```

### HTML output format
```bash
yt-transcript https://www.youtube.com/c/ChannelName --output-format html
```

### Extract cookies from browser
```bash
yt-transcript https://www.youtube.com/c/ChannelName --cookies-from-browser chrome
```

## Configuration

The following options are available:

| Option | Description |
|--------|-------------|
| `--audio` | Download audio when transcripts are unavailable |
| `--cookies` | Path to cookies file for authentication |
| `--cookies-from-browser` | Extract cookies from browser (chrome, firefox, etc) |
| `--output-format` | Output format (markdown or html) |
| `--output-file` | Custom output filename |

## Development

### Running tests
```bash
pytest
```

### Building package
```bash
python setup.py sdist bdist_wheel
```

## License

MIT
