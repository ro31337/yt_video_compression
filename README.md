# YouTube Video Compression

AI-powered tool that downloads YouTube videos and compresses them by extracting only the most valuable segments using Claude.

## How it works

1. **Cleanup** - Removes previous output files
2. **Download** - Downloads video and subtitles using yt-dlp
3. **CompressAnalysis** - Claude analyzes subtitles and identifies valuable segments, outputs `video.csv`
4. **CutVideo** - Uses ffmpeg to cut and merge segments into `compressed.mp4`

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) - Python package manager
- [ffmpeg](https://ffmpeg.org/) - Video processing
- [Claude Code](https://github.com/anthropics/claude-code) - AI analysis

## Installation

```bash
# Clone the repository
git clone https://github.com/ro31337/yt_video_compression.git
cd yt_video_compression

# Install dependencies
uv sync
```

## Usage

```bash
uv run python app.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Output

Files are saved to `./data/`:
- `video.mp4` - Original video
- `subtitles.srt` - Downloaded subtitles
- `video.csv` - Segment analysis (timestamps and descriptions)
- `compressed.mp4` - Final compressed video

## Customization

Edit `PROMPT.md` to customize how Claude analyzes and selects video segments.

## CSV Format

```csv
from_timestamp,to_timestamp,file,short_description
00:00:45,00:02:30,0001.mp4,"introduction to main concept"
00:03:15,00:05:40,0002.mp4,"key insight about performance"
```
