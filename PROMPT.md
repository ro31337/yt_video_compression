# Video Compression Analysis Task

You are analyzing a video's subtitles to identify the most valuable segments. Your goal is to compress the video by at least 50% while keeping all the essential content.

## Instructions

1. Read the `subtitles.srt` file in the current directory
2. Analyze the content to identify:
   - Key insights and main points
   - Important discussions and arguments
   - Valuable information worth keeping
3. Identify segments to REMOVE:
   - Filler content, intros/outros
   - Repetitive explanations
   - Off-topic tangents
   - Small talk and transitions
4. Create segments that capture the "juice" - the most valuable parts

## Output Requirements

Create a file called `video.csv` with the following format:
```
from_timestamp,to_timestamp,file,short_description
```

- `from_timestamp`: Start time in format HH:MM:SS or MM:SS
- `to_timestamp`: End time in format HH:MM:SS or MM:SS
- `file`: Sequential filename like 0001.mp4, 0002.mp4, etc.
- `short_description`: Brief description of segment content (in quotes if contains commas)

Example:
```csv
from_timestamp,to_timestamp,file,short_description
00:00:45,00:02:30,0001.mp4,"introduction to main concept"
00:03:15,00:05:40,0002.mp4,"key insight about performance"
00:07:00,00:09:20,0003.mp4,"practical example demonstration"
```

## Important

- Keep segments that contain the core value of the video
- Total kept content should be 50% or less of original duration
- Prefer many tiny cohesive clips that would represent the juice of the topic. No need for chit-chat or unrelated topics.
- Ensure segments have complete thoughts (don't cut mid-sentence)
- **CRITICAL**: If two valuable segments are back-to-back (less than 2 seconds gap), MERGE them into one segment. Never create adjacent segments that touch or nearly touch.
- Leave at least 1-2 seconds gap between segments to avoid overlap during video cutting
