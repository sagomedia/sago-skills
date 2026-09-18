# Sago Skills ⚡

A curated, battle-tested suite of agentic skills and automation CLI drivers for **Sago Automation**. Built for autonomous coding agents (Hermes, Pi, Claude Code, Codex, Cursor) and human operators.

---

## 📦 Included Skills

### 1. `sago-x-harvest` (X/Twitter Research & Motion Breakdown)
- **Path:** `skills/x-harvest/`
- **Capabilities:**
  - Harvest profiles, bios, and timeline posts without paid API keys via authenticated browser cookies.
  - Pull $\le 720$p video clips via `yt-dlp`.
  - Automatically extract 3-phase motion keyframes (**Approach**, **Immersion**, **Vista**) using `ffmpeg`.
  - Generates a grounded `REFSPEC.md` for downstream website and animation pipelines.
- **CLI:**
  ```bash
  python3 skills/x-harvest/harvest_x.py video https://x.com/status/123 --out-dir ./research
  python3 skills/x-harvest/harvest_x.py profile Teknium --limit 5
  python3 skills/x-harvest/harvest_x.py search "scrollytelling" --limit 5
  ```

---

### 2. `sago-flow-video` (Autonomous Google Flow Video Generation)
- **Path:** `skills/flow-video/`
- **Capabilities:**
  - Fully autonomous browser automation for Google Flow (Veo 2 & Gemini Omni 1.1 Flash) over Chrome DevTools Protocol (CDP port 9222).
  - Synthetic `ClipboardEvent('paste')` conditioning for 100% character and mascot consistency without file pickers.
  - Zero-touch in-memory blob interception (`URL.createObjectURL` hook) to extract MP4s without OS download shelves.
  - Automatic stream verification with `ffprobe` and keyframe extraction.
- **CLI:**
  ```bash
  python3 skills/flow-video/flow_driver.py --prompt "Cinematic clinic interior" --out-dir ./output/scene1
  python3 skills/flow-video/flow_driver.py --prompt "Doctor examining spine" --ref-image ./mascot.png
  ```

---

### 3. `sago-sites` (30-Minute Engine & Antislop Validator)
- **Path:** `skills/sago-sites/`
- **Capabilities:**
  - 30-minute Human-in-the-Loop website build protocol.
  - Automated Antislop Quality Gate audit tool (`audit_site.py`).
  - Viewport overflow checks at 1440px (desktop) and 390px (mobile).
  - Antislop R-02 (em dash ban), R-03 (lorem ipsum ban), and grounded facts verification.
- **CLI:**
  ```bash
  python3 skills/sago-sites/audit_site.py path/to/index.html --qa-dir ./qa
  ```

---

## 🛠️ Requirements & Setup

- **Python 3.10+**
- **System tools:** `ffmpeg`, `ffprobe`, `google-chrome`
- **Python packages:**
  ```bash
  pip install playwright yt-dlp
  playwright install chromium
  ```

---

## 🏢 Author & License

Developed by **Gokula Krishnan** & **Sago Automation**.  
Licensed under the [MIT License](LICENSE).
