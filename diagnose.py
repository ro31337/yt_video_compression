#!/usr/bin/env python3
"""Diagnostic script for yt-dlp subtitle download issues."""

import subprocess
import sys
import os
from pathlib import Path

URL = "https://www.youtube.com/watch?v=O0ShHdRQkQg"
DATA_DIR = Path(__file__).parent / "data"

def run(cmd, capture=True):
    """Run command and return (returncode, stdout, stderr)."""
    result = subprocess.run(cmd, capture_output=capture, text=True)
    return result.returncode, result.stdout or "", result.stderr or ""

def main():
    print("=" * 60)
    print("YT-DLP DIAGNOSTIC")
    print("=" * 60)

    # 1. Environment
    print("\n[1] ENVIRONMENT")
    print(f"  Python: {sys.executable}")
    print(f"  PATH: {os.environ.get('PATH', 'N/A')[:200]}...")
    print(f"  CWD: {os.getcwd()}")
    print(f"  Script dir: {Path(__file__).parent}")

    # 2. yt-dlp location
    print("\n[2] YT-DLP LOCATION")
    rc, out, err = run(["which", "yt-dlp"])
    print(f"  which yt-dlp: {out.strip() or 'NOT FOUND'}")

    # 3. yt-dlp version
    print("\n[3] YT-DLP VERSION")
    rc, out, err = run(["yt-dlp", "--version"])
    print(f"  Version: {out.strip() or f'ERROR: {err}'}")

    # 4. Check curl_cffi
    print("\n[4] CURL_CFFI (impersonation)")
    try:
        import curl_cffi
        print(f"  curl_cffi: INSTALLED ({curl_cffi.__version__})")
    except ImportError:
        print("  curl_cffi: NOT INSTALLED")

    # 5. List available subs
    print("\n[5] AVAILABLE SUBTITLES")
    rc, out, err = run(["yt-dlp", "--list-subs", URL])
    if "has no subtitles" in out:
        print("  Manual subs: NONE")
    else:
        print("  Manual subs: YES")
    if "automatic captions" in out.lower():
        # Check for ru and en
        has_ru = " ru " in out or "ru-orig" in out
        has_en = " en " in out
        print(f"  Auto-captions RU: {'YES' if has_ru else 'NO'}")
        print(f"  Auto-captions EN: {'YES' if has_en else 'NO'}")
    else:
        print("  Auto-captions: NONE")

    # 6. Clean test dir
    print("\n[6] TEST DOWNLOAD")
    for f in DATA_DIR.glob("subtitles*"):
        f.unlink()
        print(f"  Cleaned: {f.name}")

    # 7. Try manual subs
    print("\n  Trying --write-sub (manual)...")
    cmd = [
        "yt-dlp", "--skip-download", "--write-sub",
        "--sub-lang", "ru", "--convert-subs", "srt",
        "-o", str(DATA_DIR / "subtitles"), URL
    ]
    rc, out, err = run(cmd)
    files = list(DATA_DIR.glob("subtitles.ru*"))
    print(f"    Return code: {rc}")
    print(f"    Files created: {[f.name for f in files]}")

    # 8. Try auto subs
    if not files:
        print("\n  Trying --write-auto-sub...")
        cmd = [
            "yt-dlp", "--skip-download", "--write-auto-sub",
            "--sub-lang", "ru", "--convert-subs", "srt",
            "-o", str(DATA_DIR / "subtitles"), URL
        ]
        rc, out, err = run(cmd)
        files = list(DATA_DIR.glob("subtitles.ru*"))
        print(f"    Return code: {rc}")
        print(f"    Files created: {[f.name for f in files]}")
        if not files:
            print(f"    STDERR: {err[:500]}")
            print(f"    STDOUT: {out[:500]}")

    # 9. Final result
    print("\n" + "=" * 60)
    if files:
        print("RESULT: SUCCESS - subtitles downloaded")
    else:
        print("RESULT: FAILED - no subtitles")
    print("=" * 60)

if __name__ == "__main__":
    main()
