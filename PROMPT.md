# Video Compression Task

Compress the video by at least 50%, keeping only the most valuable content.

## Task

1. Read `subtitles.srt`
2. Find and KEEP only:
   - Key insights and main ideas
   - Concrete examples and practical advice
   - Important facts and numbers
3. REMOVE ruthlessly:
   - Intros, greetings, outros
   - Repetition of the same idea in different words
   - Filler: "as I said before", "let's take a look", "so", "well", "you know"
   - Pauses, mumbling, verbal fillers
   - Off-topic tangents
   - Obvious statements and platitudes
   - Transitions between topics

## Output Format

Create file `video.csv`:

```csv
from_timestamp,to_timestamp,file,short_description
00:01:15,00:02:45,0001.mp4,Key insight about X
00:04:30,00:05:10,0002.mp4,Practical example of Y
00:08:00,00:09:30,0003.mp4,Core conclusion about Z
```

Time format: `HH:MM:SS` (always include hours, e.g. `00:01:30`)

## Critical Rules

1. **Target: 50% or less of original.** If video is 20 min — result is 10 min max.

2. **Merge adjacent segments.** If gap between two valuable parts is less than 3 seconds — make ONE segment. Never create segments that touch or nearly touch.

3. **Minimum 2 second gap.** Between end of one segment and start of next must be at least 2 seconds. Example:
   - Segment 1: `00:01:00` → `00:01:30`
   - Segment 2: `00:01:33` → `00:02:00` (3 sec gap — OK)

4. **Fewer segments = better.** Prefer 5-10 long meaningful segments over 30 short ones.

5. **Only the essence.** Each segment must contain concrete value. When in doubt — leave it out.
