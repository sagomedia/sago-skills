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


### 4. `bulk-product-verification` (Bulk E-Commerce Catalog Verification & Database Staging)
- **Path:** `skills/bulk-product-verification/`
- **Capabilities:**
  - Automated verification of bulk retail/e-commerce product catalogs before database ingestion.
  - Strict schema hygiene: lowercase `snake_case` specification keys, multilingual validation (`localNames.ta`, `localNames["ta-Latn"]`).
  - Physical selling basis & unit mechanics: decoupling pack contents from ordered unit, preventing volume-to-weight conversions, enforcing conservative cutting policies.
  - Visual provenance audit: category matching, OCR/marking inspection against nominal dimensions, and AI hallucination detection.
  - Search taxonomy defense: flags and sanitizes brand name bleeding in category aliases to prevent search routing hijack.
  - Multi-batch non-destructive duplicate and physical variant reconciliation (`canonical-sku-map.json`).
  - Zero-trust commercial defaults (`pricePaise: 0`, `priceStatus: "confirm"`, `stock: null`, `active: false`, `verified: false`).
- **CLI Tools:**
  ```bash
  # Validate a catalog batch against draft schema, selling basis, and commercial honesty
  python3 skills/bulk-product-verification/scripts/validate_catalog.py path/to/batch_folder

  # Non-destructively reconcile duplicates across multiple batches
  python3 skills/bulk-product-verification/scripts/reconcile_duplicates.py canonical-sku-map.json batch1 batch2 batch3
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
