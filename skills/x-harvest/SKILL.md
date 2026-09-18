---
name: sago-x-harvest
description: "Harvest X/Twitter profiles, timelines, and download video clips with automated 3-phase motion keyframe extraction (Approach, Immersion, Vista) without official API keys."
version: 1.0.0
author: Sago Automation
license: MIT
platforms: [linux]
metadata:
  tags: [twitter, x, scraping, video, motion-analysis, scout, reference]
---

# Sago X Harvest Skill

Autonomous CLI and protocol to research X/Twitter profiles, live search timelines, and download video references with instant motion extraction.

No API keys or Developer Portal subscriptions required. Uses local authenticated Chrome profiles and cookie vaults.

---

## Capabilities

1. **Clip & Motion Breakdown (`video`)**:
   - Downloads MP4 ($\le 720$p) using `yt-dlp` and decrypted Chrome session cookies.
   - Extracts 3 core motion keyframes via `ffmpeg`:
     - `f_01_start_approach.jpg`: The establishing scene.
     - `f_02_mid_immersion.jpg`: The core interaction / therapy / product scene.
     - `f_03_end_vista.jpg`: The resolution / final brand shot.
   - Automatically generates a structured `REFSPEC.md` ready for the `sago-sites` website builder.

2. **Profile Scouting (`profile`)**:
   - Launches headless Google Chrome using the authenticated profile copy.
   - Connects Playwright via dynamic DevTools port.
   - Extracts user bio, handle, and latest posts with direct `/status/` permalinks.

3. **Search Sweep (`search`)**:
   - Searches live X timelines for fresh topics, client references, or viral web templates.
   - Exports results to JSON or stdout.

---

## CLI Usage

```bash
# 1. Download video and extract motion keyframes:
python3 harvest_x.py video https://x.com/Google/status/2098084519320383940 --out-dir ./research/gemini_desktop

# 2. Scout a profile for research:
python3 harvest_x.py profile Teknium --limit 5 --out-file profile_teknium.json

# 3. Live search query:
python3 harvest_x.py search "scrollytelling website" --limit 5
```

---

## Generated Artifacts

When executing `harvest_x.py video <url> --out-dir <dir>`:
- `<dir>/reference_clip.mp4`
- `<dir>/f_01_start_approach.jpg`
- `<dir>/f_02_mid_immersion.jpg`
- `<dir>/f_03_end_vista.jpg`
- `<dir>/REFSPEC.md`
