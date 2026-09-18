---
name: sago-flow-video
description: "Autonomous Google Flow (Veo 2 & Gemini Omni 1.1 Flash) programmatic video generation via Chrome DevTools Protocol (CDP), synthetic clipboard paste conditioning, and zero-touch in-memory blob extraction."
version: 1.0.0
author: Sago Automation
license: MIT
platforms: [linux]
metadata:
  tags: [video, google-flow, veo, omni-flash, cdp, automation, synthetic-conditioning]
---

# Sago Flow Video Generation Skill

Autonomous browser automation and programmatic video production engine for Google Flow (Veo 2 and Gemini Omni 1.1 Flash) over Chrome DevTools Protocol (CDP).

---

## Core Innovations

1. **Persistent Authentication over CDP**:
   - Eliminates login walls by connecting to Google Chrome running with the user's authenticated Google Account on port `9222`.
2. **Synthetic Clipboard Conditioning (`ClipboardEvent('paste')`)**:
   - Bypasses the absence of standard `<input type="file">` elements on Google Flow.
   - Dispatches a synthetic paste event carrying image binary buffers directly into ProseMirror to render conditioning reference chips.
3. **Zero-Touch In-Memory Blob Interception**:
   - Eliminates fragile OS file-save dialogs.
   - Monkeypatches `URL.createObjectURL` inside the page context, extracts generated MP4 data as base64 via `FileReader`, and transmits it over CDP.
4. **Autonomous Watchdog & Keyframe Extraction**:
   - Detects policy errors (`flow-error-tile`) and auto-cleans generation queues.
   - Verifies stream integrity with `ffprobe` and extracts Start, Mid, and Vista keyframes with `ffmpeg`.

---

## CLI Usage

```bash
# 1. Quick video generation with Gemini Omni 1.1 Flash (360p / 9:16 vertical):
python3 flow_driver.py \
  --prompt "Cinematic camera pan across modern dental clinic examination bay" \
  --out-dir ./output/clinic_pan

# 2. Conditioned generation with character / reference image consistency:
python3 flow_driver.py \
  --prompt "Doctor in white coat smiling and explaining treatment plan" \
  --ref-image ./mascot.png \
  --out-dir ./output/doctor_scene

# 3. High-fidelity generation with Veo 2:
python3 flow_driver.py \
  --prompt "Aerial sunset drone shot of college campus quadrangle" \
  --model veo \
  --out-dir ./output/campus_vista
```

---

## Generated Artifacts

- `master_film.mp4`: The clean generated MP4 video.
- `f_start.jpg`: Opening establishing frame.
- `f_mid.jpg`: Mid-sequence immersion frame.
- `f_end.jpg`: Closing vista frame.
