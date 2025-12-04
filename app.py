#!/usr/bin/env python3
"""Video processing pipeline with step-based architecture."""

import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class StepResult:
    """Result of a pipeline step execution."""
    success: bool
    message: str


class PipelineStep(ABC):
    """Abstract base class for pipeline steps."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the step."""
        pass

    @abstractmethod
    def execute(self) -> StepResult:
        """Execute the step and return the result."""
        pass


class CleanupStep(PipelineStep):
    """Step for cleaning up previous run artifacts."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.extensions = [".mp4", ".csv", ".srt"]

    @property
    def name(self) -> str:
        return "Cleanup"

    def execute(self) -> StepResult:
        """Remove .mp4, .csv, .srt files from data directory."""
        if not self.data_dir.exists():
            return StepResult(success=True, message="Data directory does not exist, nothing to clean")

        removed = []
        for ext in self.extensions:
            for file in self.data_dir.glob(f"*{ext}"):
                file.unlink()
                removed.append(file.name)

        if removed:
            return StepResult(success=True, message=f"Removed: {', '.join(removed)}")
        return StepResult(success=True, message="No files to clean up")


class DownloadStep(PipelineStep):
    """Step for downloading video and subtitles using yt-dlp."""

    def __init__(self, url: str, output_dir: Path, subtitle_langs: list[str] | None = None):
        # Strip backslashes that shell escaping may add
        self.url = url.replace("\\", "")
        self.output_dir = output_dir
        self.subtitle_langs = subtitle_langs or ["ru", "en"]
        self.video_path = output_dir / "video.mp4"
        self.subtitles_path = output_dir / "subtitles.srt"

    @property
    def name(self) -> str:
        return "Download"

    def execute(self) -> StepResult:
        """Download video and subtitles using yt-dlp."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Download subtitles
        subtitle_result = self._download_subtitles()
        if not subtitle_result.success:
            return subtitle_result

        # Download video
        video_result = self._download_video()
        if not video_result.success:
            return video_result

        return StepResult(
            success=True,
            message=f"Downloaded video to {self.video_path} and subtitles to {self.subtitles_path}"
        )

    def _download_subtitles(self) -> StepResult:
        """Download subtitles, trying languages in order of preference."""
        for lang in self.subtitle_langs:
            # Try regular subtitles first, then auto-generated
            result = self._try_download_subtitle(lang, auto=False)
            if result.success:
                return result

            result = self._try_download_subtitle(lang, auto=True)
            if result.success:
                return result

            print(f"  No {lang} subtitles available, trying next...")

        return StepResult(
            success=False,
            message=f"No subtitles found in any of: {', '.join(self.subtitle_langs)}"
        )

    def _try_download_subtitle(self, lang: str, auto: bool = False) -> StepResult:
        """Try to download subtitles for a specific language."""
        sub_flag = "--write-auto-sub" if auto else "--write-sub"
        cmd = [
            "yt-dlp",
            "--skip-download",
            sub_flag,
            "--sub-lang", lang,
            "--convert-subs", "srt",
            "-o", str(self.output_dir / "subtitles"),
            self.url
        ]

        try:
            # Run yt-dlp - don't check return code, check for files instead
            subprocess.run(cmd, capture_output=True, text=True)

            # yt-dlp creates file with language suffix, look for srt or vtt
            subtitle_files = list(self.output_dir.glob(f"subtitles.{lang}*.srt"))
            if not subtitle_files:
                subtitle_files = list(self.output_dir.glob(f"subtitles.{lang}*.vtt"))

            if not subtitle_files:
                return StepResult(success=False, message=f"No {lang} subtitles found")

            # Rename to target path, keeping original extension
            src_file = subtitle_files[0]
            self.subtitles_path = self.subtitles_path.with_suffix(src_file.suffix)
            src_file.rename(self.subtitles_path)

            sub_type = "auto-generated" if auto else "manual"
            return StepResult(success=True, message=f"Subtitles downloaded ({lang}, {sub_type})")

        except FileNotFoundError:
            return StepResult(
                success=False,
                message="yt-dlp not found. Please install it with: uv add yt-dlp"
            )

    def _download_video(self) -> StepResult:
        """Download video only."""
        cmd = [
            "yt-dlp",
            "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "--merge-output-format", "mp4",
            "-o", str(self.video_path),
            self.url
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return StepResult(
                    success=False,
                    message=f"Failed to download video: {result.stderr}"
                )

            if not self.video_path.exists():
                return StepResult(
                    success=False,
                    message="Video file was not created"
                )

            return StepResult(success=True, message="Video downloaded")

        except FileNotFoundError:
            return StepResult(
                success=False,
                message="yt-dlp not found. Please install it with: uv add yt-dlp"
            )


class CompressAnalysisStep(PipelineStep):
    """Step for analyzing subtitles with Claude to produce compression CSV."""

    def __init__(self, data_dir: Path, prompt_file: Path):
        self.data_dir = data_dir
        self.prompt_file = prompt_file
        self.csv_path = data_dir / "video.csv"

    @property
    def name(self) -> str:
        return "CompressAnalysis"

    def execute(self) -> StepResult:
        """Run Claude to analyze subtitles and produce CSV."""
        # Verify subtitles exist
        srt_files = list(self.data_dir.glob("subtitles.*"))
        if not srt_files:
            return StepResult(
                success=False,
                message="No subtitles file found in data directory"
            )

        # Read prompt from file
        if not self.prompt_file.exists():
            return StepResult(
                success=False,
                message=f"Prompt file not found: {self.prompt_file}"
            )

        prompt = self.prompt_file.read_text()

        # Run Claude with the prompt
        cmd = [
            "claude",
            "--dangerously-skip-permissions",
            "-p", prompt
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.data_dir,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return StepResult(
                    success=False,
                    message=f"Claude failed: {result.stderr}"
                )

            # Verify CSV was created
            if not self.csv_path.exists():
                return StepResult(
                    success=False,
                    message="Claude did not create video.csv"
                )

            return StepResult(
                success=True,
                message=f"Analysis complete, CSV saved to {self.csv_path}"
            )

        except FileNotFoundError:
            return StepResult(
                success=False,
                message="claude CLI not found. Please install Claude Code."
            )


def timestamp_to_seconds(ts: str) -> float:
    """Convert HH:MM:SS or HH:MM:SS.mmm to seconds."""
    parts = ts.split(":")
    h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
    return h * 3600 + m * 60 + s


class NormalizeCSVStep(PipelineStep):
    """Step for normalizing CSV by merging adjacent segments within 3 seconds."""

    def __init__(self, data_dir: Path, gap_threshold: float = 3.0):
        self.data_dir = data_dir
        self.csv_path = data_dir / "video.csv"
        self.gap_threshold = gap_threshold

    @property
    def name(self) -> str:
        return "NormalizeCSV"

    def execute(self) -> StepResult:
        """Merge adjacent segments if gap between them is <= threshold."""
        import csv

        if not self.csv_path.exists():
            return StepResult(success=False, message="video.csv not found")

        # Read segments
        segments = []
        with open(self.csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                segments.append({
                    "from": row["from_timestamp"],
                    "to": row["to_timestamp"],
                    "desc": row.get("short_description", ""),
                })

        if not segments:
            return StepResult(success=False, message="No segments in CSV")

        # Merge adjacent segments within threshold
        merged = [segments[0]]
        for seg in segments[1:]:
            prev = merged[-1]
            prev_end = timestamp_to_seconds(prev["to"])
            curr_start = timestamp_to_seconds(seg["from"])
            gap = curr_start - prev_end

            if gap <= self.gap_threshold:
                # Merge: extend previous segment to current's end
                prev["to"] = seg["to"]
                prev["desc"] = f"{prev['desc']}; {seg['desc']}"
            else:
                merged.append(seg)

        # Write back with renumbered files
        with open(self.csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["from_timestamp", "to_timestamp", "file", "short_description"])
            for i, seg in enumerate(merged, 1):
                writer.writerow([seg["from"], seg["to"], f"{i:04d}.mp4", seg["desc"]])

        merged_count = len(segments) - len(merged)
        return StepResult(
            success=True,
            message=f"Normalized: {len(segments)} -> {len(merged)} segments ({merged_count} merged)"
        )


class CutVideoStep(PipelineStep):
    """Step for cutting video into chunks and merging based on CSV."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.video_path = data_dir / "video.mp4"
        self.csv_path = data_dir / "video.csv"
        self.output_path = data_dir / "compressed.mp4"

    @property
    def name(self) -> str:
        return "CutVideo"

    def _calc_duration(self, from_ts: str, to_ts: str) -> str:
        """Calculate duration between two timestamps."""
        duration = timestamp_to_seconds(to_ts) - timestamp_to_seconds(from_ts)
        h = int(duration // 3600)
        m = int((duration % 3600) // 60)
        s = duration % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}"

    def execute(self) -> StepResult:
        """Cut video into chunks and merge them."""
        import csv

        if not self.video_path.exists():
            return StepResult(success=False, message="video.mp4 not found")

        if not self.csv_path.exists():
            return StepResult(success=False, message="video.csv not found")

        # Parse CSV
        segments = []
        with open(self.csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                segments.append({
                    "from": row["from_timestamp"],
                    "to": row["to_timestamp"],
                    "file": row["file"],
                })

        if not segments:
            return StepResult(success=False, message="No segments found in CSV")

        # Cut each segment
        chunk_files = []
        for i, seg in enumerate(segments):
            chunk_path = self.data_dir / seg["file"]
            chunk_files.append(chunk_path)

            duration = self._calc_duration(seg["from"], seg["to"])
            cmd = [
                "ffmpeg", "-y",
                "-ss", seg["from"],
                "-i", str(self.video_path),
                "-t", duration,
                "-c", "copy",
                "-avoid_negative_ts", "make_zero",
                str(chunk_path)
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return StepResult(
                    success=False,
                    message=f"Failed to cut segment {i+1}: {result.stderr}"
                )
            print(f"  Cut segment {i+1}/{len(segments)}: {seg['file']}")

        # Create concat file for ffmpeg
        concat_file = self.data_dir / "concat.txt"
        with open(concat_file, "w") as f:
            for chunk in chunk_files:
                f.write(f"file '{chunk.name}'\n")

        # Merge all chunks
        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(self.output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            return StepResult(
                success=False,
                message=f"Failed to merge segments: {result.stderr}"
            )

        # Clean up chunk files and concat file
        for chunk in chunk_files:
            chunk.unlink()
        concat_file.unlink()

        return StepResult(
            success=True,
            message=f"Created {self.output_path.name} from {len(segments)} segments"
        )


class Pipeline:
    """Pipeline that executes steps sequentially."""

    def __init__(self):
        self.steps: list[PipelineStep] = []

    def add_step(self, step: PipelineStep) -> "Pipeline":
        """Add a step to the pipeline."""
        self.steps.append(step)
        return self

    def run(self) -> bool:
        """Run all steps. Stop on first failure."""
        for step in self.steps:
            print(f"[{step.name}] Starting...")
            result = step.execute()

            if result.success:
                print(f"[{step.name}] ✓ {result.message}")
            else:
                print(f"[{step.name}] ✗ {result.message}")
                return False

        print("\nPipeline completed successfully!")
        return True


def main():
    if len(sys.argv) < 2:
        print("Usage: python app.py <youtube_url>")
        sys.exit(1)

    url = sys.argv[1]
    base_dir = Path(__file__).parent
    output_dir = base_dir / "data"
    prompt_file = base_dir / "PROMPT.md"

    pipeline = Pipeline()
    pipeline.add_step(CleanupStep(output_dir))
    pipeline.add_step(DownloadStep(url, output_dir, subtitle_langs=["ru", "en"]))
    pipeline.add_step(CompressAnalysisStep(output_dir, prompt_file))
    pipeline.add_step(NormalizeCSVStep(output_dir))
    pipeline.add_step(CutVideoStep(output_dir))

    success = pipeline.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
