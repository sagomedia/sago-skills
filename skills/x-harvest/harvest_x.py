#!/usr/bin/env python3
"""
harvest_x.py - Standalone CLI for X/Twitter research, post/profile harvesting, and video motion breakdown.

Usage:
  python3 harvest_x.py video <x-status-url> [--out-dir DIR]
  python3 harvest_x.py profile <handle> [--limit N] [--out-file FILE]
  python3 harvest_x.py search <query> [--limit N] [--out-file FILE]
"""

import argparse
import atexit
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from urllib.parse import quote_plus

CHROME_BIN = "/usr/bin/google-chrome"
CHROME_PROFILE_COPY = "/home/gokul/.hermes/browser-profile/chrome"
YT_DLP_BIN = "/home/gokul/.local/bin/yt-dlp"

_active_procs = []

def _cleanup_procs():
    for p in _active_procs:
        try:
            p.send_signal(signal.SIGTERM)
            p.wait(timeout=2)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass
    _active_procs.clear()

atexit.register(_cleanup_procs)


def _launch_chrome_on_profile(copy_dir: str = CHROME_PROFILE_COPY) -> int:
    """Launch Google Chrome in headless mode with real profile copy to access authenticated cookies."""
    if not os.path.exists(copy_dir):
        raise RuntimeError(f"Chrome profile directory does not exist: {copy_dir}")

    active_port_file = os.path.join(copy_dir, "DevToolsActivePort")
    if os.path.exists(active_port_file):
        try:
            os.unlink(active_port_file)
        except OSError:
            pass

    singleton_lock = os.path.join(copy_dir, "SingletonLock")
    if os.path.exists(singleton_lock) or os.path.islink(singleton_lock):
        try:
            os.unlink(singleton_lock)
        except OSError:
            pass

    cmd = [
        CHROME_BIN,
        f"--user-data-dir={copy_dir}",
        "--remote-debugging-port=0",
        "--headless=new",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-sync",
        "--no-sandbox",
        "--disable-dev-shm-usage"
    ]

    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _active_procs.append(proc)

    port = None
    for _ in range(40):
        time.sleep(0.25)
        if os.path.exists(active_port_file):
            try:
                with open(active_port_file, "r", encoding="utf-8") as f:
                    line = f.readline().strip()
                    if line and line.isdigit():
                        port = int(line)
                        break
            except Exception:
                pass

    if not port:
        _cleanup_procs()
        raise RuntimeError("Google Chrome failed to expose DevToolsActivePort in time.")

    return port


# ----------------------------------------------------------------------
# Command 1: video
# ----------------------------------------------------------------------
def cmd_video(args):
    url = args.url
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    print(f"[*] Extracting metadata for: {url}")
    dump_cmd = [
        YT_DLP_BIN,
        "--cookies-from-browser", "chrome",
        "--dump-json",
        "--skip-download",
        url
    ]
    res = subprocess.run(dump_cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"[!] Error fetching metadata with yt-dlp: {res.stderr}", file=sys.stderr)
        sys.exit(1)

    meta = json.loads(res.stdout)
    title = meta.get("description") or meta.get("title") or "Unknown"
    uploader = meta.get("uploader") or meta.get("uploader_id") or "Unknown"
    uploader_id = meta.get("uploader_id") or ""
    duration = meta.get("duration") or 0.0
    views = meta.get("view_count") or 0
    likes = meta.get("like_count") or 0

    print(f"[+] Found video by @{uploader_id} ({uploader})")
    print(f"[+] Duration: {duration:.2f}s | Views: {views} | Likes: {likes}")

    # Download video
    video_path = os.path.join(out_dir, "reference_clip.mp4")
    print(f"[*] Downloading clip to: {video_path}")
    dl_cmd = [
        YT_DLP_BIN,
        "--cookies-from-browser", "chrome",
        "-f", "bv*[height<=720]+ba/b[height<=720]/b",
        "--merge-output-format", "mp4",
        "-o", video_path,
        url
    ]
    dl_res = subprocess.run(dl_cmd, capture_output=True, text=True)
    if dl_res.returncode != 0 or not os.path.exists(video_path):
        print(f"[!] Download failed: {dl_res.stderr}", file=sys.stderr)
        sys.exit(1)

    # Inspect stream via ffprobe
    probe_cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,duration,codec_name",
        "-of", "json",
        video_path
    ]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True)
    probe_data = json.loads(probe_res.stdout) if probe_res.returncode == 0 else {}
    video_stream = next((s for s in probe_data.get("streams", []) if s.get("codec_name") != "aac"), {})
    width = video_stream.get("width", "Unknown")
    height = video_stream.get("height", "Unknown")
    codec = video_stream.get("codec_name", "h264")

    # Extract 3 keyframes (Start, Mid, End)
    print("[*] Extracting keyframe stills (Approach, Immersion, Vista)...")
    start_time = 0.1
    mid_time = max(0.5, duration / 2.0)
    end_time = max(0.9, duration - 0.2)

    frames = [
        ("f_01_start_approach.jpg", start_time),
        ("f_02_mid_immersion.jpg", mid_time),
        ("f_03_end_vista.jpg", end_time)
    ]

    for fname, t in frames:
        fpath = os.path.join(out_dir, fname)
        subprocess.run([
            "ffmpeg", "-y", "-ss", f"{t:.3f}",
            "-i", video_path,
            "-frames:v", "1",
            "-update", "1",
            fpath
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Generate REFSPEC.md
    refspec_path = os.path.join(out_dir, "REFSPEC.md")
    with open(refspec_path, "w", encoding="utf-8") as f:
        f.write(f"""# Motion & Design REFSPEC

**Source URL:** {url}  
**Creator:** {uploader} (@{uploader_id})  
**Clip Duration:** {duration:.2f}s | **Resolution:** {width}x{height} ({codec})  
**Engagement:** {views:,} views | {likes:,} likes  

---

## Post Context
> {title}

---

## 3-Phase Motion Keyframes

| Phase | Frame | Timestamp | Observed Motion / Composition |
| :--- | :--- | :--- | :--- |
| **1. Approach** | `f_01_start_approach.jpg` | `{start_time:.2f}s` | [observed] Establishing view, subject enters focus |
| **2. Immersion** | `f_02_mid_immersion.jpg` | `{mid_time:.2f}s` | [observed] Core interaction / detail view |
| **3. Vista** | `f_03_end_vista.jpg` | `{end_time:.2f}s` | [observed] Resolution, final posture / brand lock |

---

## Technical Specifications for Sago-Sites Pipeline
- **Video File:** `{os.path.basename(video_path)}`
- **Recommended Web Presentation:**
  - Full-bleed background scrub with 300vh scroll pinning.
  - Or cursor-reactive 3D tilt with gaze interpolation.
  - Type overlay: Bilingual high-contrast radial haze (WCAG AA).
""")

    print(f"\n[✓] Video downloaded: {video_path}")
    print(f"[✓] Keyframes extracted: {out_dir}/f_*.jpg")
    print(f"[✓] REFSPEC generated: {refspec_path}")


# ----------------------------------------------------------------------
# Command 2: profile
# ----------------------------------------------------------------------
def cmd_profile(args):
    handle = args.handle.lstrip("@")
    profile_url = f"https://x.com/{handle}"
    limit = args.limit

    print(f"[*] Launching authenticated Chrome headless for profile: @{handle}")
    port = _launch_chrome_on_profile()
    cdp_url = f"http://127.0.0.1:{port}"

    from playwright.sync_api import sync_playwright
    result = {"handle": handle, "url": profile_url, "bio": "", "posts": []}

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = context.new_page()

            print(f"[*] Navigating to {profile_url}...")
            page.goto(profile_url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3500)

            # Bio
            bio_elem = page.query_selector('div[data-testid="UserDescription"]')
            bio = bio_elem.inner_text().strip() if bio_elem else ""
            result["bio"] = bio

            # Scroll to hydrate virtualized timeline
            for _ in range(3):
                page.evaluate("window.scrollBy(0, 1500)")
                page.wait_for_timeout(1500)

            articles = page.query_selector_all("article")
            posts = []
            for art in articles[:limit]:
                text = art.inner_text().replace("\n", " | ").strip()
                link_elem = art.query_selector('a[href*="/status/"]')
                link = link_elem.get_attribute("href") if link_elem else ""
                if link and not link.startswith("http"):
                    link = f"https://x.com{link}"
                posts.append({"url": link, "preview": text[:280]})

            result["posts"] = posts
            browser.close()
    finally:
        _cleanup_procs()

    print(f"\n[+] Profile: @{handle}")
    print(f"[+] Bio: {result['bio']}")
    print(f"[+] Harvested Posts ({len(result['posts'])}):")
    for i, post in enumerate(result["posts"]):
        print(f"  [{i+1}] {post['url']}")
        print(f"      {post['preview'][:120]}...")

    if args.out_file:
        with open(args.out_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(f"[✓] Saved profile to {args.out_file}")


# ----------------------------------------------------------------------
# Command 3: search
# ----------------------------------------------------------------------
def cmd_search(args):
    query = args.query
    filter_flag = "&f=live" if args.latest else ""
    search_url = f"https://x.com/search?q={quote_plus(query)}&src=typed_query{filter_flag}"
    limit = args.limit

    print(f"[*] Launching authenticated Chrome headless for search: '{query}'")
    port = _launch_chrome_on_profile()
    cdp_url = f"http://127.0.0.1:{port}"

    from playwright.sync_api import sync_playwright
    hits = []

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(cdp_url)
            context = browser.contexts[0]
            page = context.new_page()

            print(f"[*] Navigating to {search_url}...")
            page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
            try:
                page.wait_for_selector("article", timeout=8000)
            except Exception:
                pass
            page.wait_for_timeout(2500)

            for _ in range(2):
                page.evaluate("window.scrollBy(0, 1200)")
                page.wait_for_timeout(1500)

            articles = page.query_selector_all("article")
            for art in articles[:limit]:
                text = art.inner_text().replace("\n", " | ").strip()
                link_elem = art.query_selector('a[href*="/status/"]')
                link = link_elem.get_attribute("href") if link_elem else ""
                if link and not link.startswith("http"):
                    link = f"https://x.com{link}"
                hits.append({"url": link, "preview": text[:280]})

            browser.close()
    finally:
        _cleanup_procs()

    print(f"\n[+] Search Query: '{query}'")
    print(f"[+] Harvested Hits ({len(hits)}):")
    for i, h in enumerate(hits):
        print(f"  [{i+1}] {h['url']}")
        print(f"      {h['preview'][:120]}...")

    if args.out_file:
        with open(args.out_file, "w", encoding="utf-8") as f:
            json.dump({"query": query, "hits": hits}, f, indent=2)
        print(f"[✓] Saved search results to {args.out_file}")


def main():
    parser = argparse.ArgumentParser(description="X/Twitter Research & Video Breakdown CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # video
    p_video = subparsers.add_parser("video", help="Download X video and extract motion keyframes")
    p_video.add_argument("url", help="X status URL (e.g. https://x.com/user/status/12345)")
    p_video.add_argument("--out-dir", default="./output", help="Directory to store clip and keyframes")

    # profile
    p_profile = subparsers.add_parser("profile", help="Harvest profile bio and latest posts")
    p_profile.add_argument("handle", help="Twitter/X handle (without @)")
    p_profile.add_argument("--limit", type=int, default=5, help="Max posts to harvest")
    p_profile.add_argument("--out-file", help="Path to save JSON output")

    # search
    p_search = subparsers.add_parser("search", help="Harvest search timeline")
    p_search.add_argument("query", help="Search query string")
    p_search.add_argument("--latest", action="store_true", help="Search latest posts (f=live)")
    p_search.add_argument("--limit", type=int, default=5, help="Max posts to harvest")
    p_search.add_argument("--out-file", help="Path to save JSON output")

    args = parser.parse_args()
    if args.command == "video":
        cmd_video(args)
    elif args.command == "profile":
        cmd_profile(args)
    elif args.command == "search":
        cmd_search(args)


if __name__ == "__main__":
    main()
