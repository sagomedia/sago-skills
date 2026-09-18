#!/usr/bin/env python3
"""
flow_driver.py - Autonomous CLI driver for Google Flow (Veo 2 & Gemini Omni 1.1 Flash) via Chrome DevTools Protocol (CDP).

Features:
  - Connects to or launches Chrome on port 9222 with persistent profile
  - Synthetic ClipboardEvent paste for character consistency conditioning
  - In-memory Blob interception (URL.createObjectURL hook)
  - Post-generation verification (ffprobe) & 3-phase keyframe extraction

Usage:
  python3 flow_driver.py --prompt "Modern physical therapy clinic room" --out-dir ./output/clinic_scene
  python3 flow_driver.py --prompt "Doctor inspecting back posture" --ref-image ./mascot.png --out-dir ./output/doctor
"""

import argparse
import atexit
import base64
import json
import os
import signal
import subprocess
import sys
import time
from urllib.request import urlopen

CDP_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"
CHROME_BIN = "/usr/bin/google-chrome"
USER_DATA_DIR = os.path.expanduser("~/.config/google-chrome-remote")

_launched_proc = None

def _is_cdp_ready() -> bool:
    try:
        with urlopen(f"{CDP_URL}/json/version", timeout=1.5) as res:
            return res.status == 200
    except Exception:
        return False

def _ensure_chrome():
    global _launched_proc
    if _is_cdp_ready():
        print(f"[+] Attached to existing Chrome CDP on port {CDP_PORT}")
        return

    print(f"[*] Launching Chrome with CDP on port {CDP_PORT}...")
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    
    # Remove stale locks
    for fname in os.listdir(USER_DATA_DIR):
        if fname.startswith("Singleton"):
            try:
                os.unlink(os.path.join(USER_DATA_DIR, fname))
            except Exception:
                pass

    cmd = [
        CHROME_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={USER_DATA_DIR}",
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-background-timer-throttling",
        "--disable-backgrounding-occluded-windows",
        "--disable-renderer-backgrounding",
        "https://flow.google.com/?pli=1"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _launched_proc = proc

    for _ in range(30):
        time.sleep(0.3)
        if _is_cdp_ready():
            print(f"[+] Chrome CDP is ready at {CDP_URL}")
            return

    raise RuntimeError("Timed out waiting for Chrome CDP on port 9222.")

def _cleanup():
    global _launched_proc
    if _launched_proc:
        try:
            _launched_proc.send_signal(signal.SIGTERM)
            _launched_proc.wait(timeout=2)
        except Exception:
            try:
                _launched_proc.kill()
            except Exception:
                pass

atexit.register(_cleanup)


def generate_flow_video(prompt: str, ref_image: str = None, out_dir: str = "./output", model_choice: str = "omni", duration_timeout: int = 180):
    from playwright.sync_api import sync_playwright

    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    _ensure_chrome()

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0]
        page = context.new_page()

        print("[*] Navigating to Google Flow...")
        page.goto("https://flow.google.com/?pli=1", timeout=45000, wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        # Ensure active prompt editor
        print("[*] Checking prompt editor...")
        editor = page.wait_for_selector('.ProseMirror[contenteditable="true"]', timeout=30000)

        # Inject Synthetic Blob Interception
        page.evaluate("""() => {
            window.__capturedBlobs = [];
            const origCreate = URL.createObjectURL;
            URL.createObjectURL = function(obj) {
                const url = origCreate.call(this, obj);
                if (obj && (obj.type.includes('video') || (obj.size && obj.size > 100000))) {
                    const reader = new FileReader();
                    reader.onloadend = () => {
                        window.__capturedBlobs.push({
                            data: reader.result,
                            size: obj.size,
                            type: obj.type
                        });
                    };
                    reader.readAsDataURL(obj);
                }
                return url;
            };
        }""")

        # If reference image supplied, inject via synthetic ClipboardEvent('paste')
        if ref_image and os.path.exists(ref_image):
            print(f"[*] Injecting reference image via synthetic paste: {ref_image}")
            with open(ref_image, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            mime_type = "image/png" if ref_image.endswith(".png") else "image/jpeg"

            page.evaluate(f"""() => {{
                const b64Data = "{img_b64}";
                const mimeType = "{mime_type}";
                const byteCharacters = atob(b64Data);
                const byteNumbers = new Array(byteCharacters.length);
                for (let i = 0; i < byteCharacters.length; i++) {{
                    byteNumbers[i] = byteCharacters.charCodeAt(i);
                }}
                const byteArray = new Uint8Array(byteNumbers);
                const file = new File([byteArray], "reference.png", {{ type: mimeType }});

                const dt = new DataTransfer();
                dt.items.add(file);
                const event = new ClipboardEvent("paste", {{
                    clipboardData: dt,
                    bubbles: true,
                    cancelable: true
                }});
                const editor = document.querySelector('.ProseMirror[contenteditable="true"]');
                editor.dispatchEvent(event);
            }}""")
            page.wait_for_timeout(3000)

        # Prepare formatted prompt
        if model_choice == "omni":
            full_prompt = f"Use Gemini Omni 1.1 Flash, do not use Veo. Vertical (9:16) aspect ratio, 360p fast render. {prompt}"
        else:
            full_prompt = prompt

        print(f"[*] Entering prompt: {full_prompt}")
        editor.click()
        editor.fill("")
        editor.fill(full_prompt)
        page.wait_for_timeout(1000)

        # Submit generation
        submit_btn = page.query_selector('button[aria-label="Generate"], button:has-text("Generate"), button.submit-button')
        if submit_btn:
            submit_btn.click()
        else:
            page.keyboard.press("Enter")

        print("[*] Generation submitted. Awaiting render completion...")
        start_t = time.time()
        video_blob_data = None

        while time.time() - start_t < duration_timeout:
            # Check for policy errors
            has_error = page.evaluate("""() => {
                const err = document.querySelector('.error-message, flow-error-tile');
                return err ? err.innerText : null;
            }""")
            if has_error and "policies" in has_error.lower():
                raise RuntimeError(f"Google Flow Policy Rejection: {has_error}")

            # Check if video tile rendered
            tile_rendered = page.evaluate("""() => {
                const video = document.querySelector('flow-video-tile video, video');
                return !!video;
            }""")

            if tile_rendered:
                print("[+] Video tile detected! Triggering download for blob capture...")
                page.evaluate("""() => {
                    const tile = document.querySelector('flow-video-tile') || document.body;
                    const moreBtn = tile.querySelector('button[aria-label="More options"], button.mat-mdc-menu-trigger');
                    if (moreBtn) moreBtn.click();
                }""")
                page.wait_for_timeout(1500)

                # Click download menu option
                page.evaluate("""() => {
                    const items = Array.from(document.querySelectorAll('.mat-mdc-menu-item, button'));
                    const dl = items.find(el => el.innerText && el.innerText.includes('Download'));
                    if (dl) dl.click();
                }""")
                page.wait_for_timeout(2000)

                # Poll captured blobs
                blobs = page.evaluate("() => window.__capturedBlobs || []")
                if blobs:
                    video_blob_data = blobs[0]["data"]
                    print(f"[+] Successfully captured video blob ({blobs[0]['size']} bytes)!")
                    break

            time.sleep(3)

        if not video_blob_data:
            # Fallback: pull video src directly if blob monkeypatch was missed
            video_src = page.evaluate("""() => {
                const v = document.querySelector('video');
                return v ? v.src : null;
            }""")
            if video_src and video_src.startswith("http"):
                print(f"[*] Downloading direct video src: {video_src}")
                subprocess.run(["curl", "-s", "-o", os.path.join(out_dir, "master_film.mp4"), video_src])
            else:
                raise TimeoutError("Failed to extract video within timeout window.")
        else:
            # Decode base64 and write
            header, encoded = video_blob_data.split(",", 1)
            video_bytes = base64.b64decode(encoded)
            video_out = os.path.join(out_dir, "master_film.mp4")
            with open(video_out, "wb") as f:
                f.write(video_bytes)
            print(f"[✓] Saved master video to: {video_out}")

        page.close()

    # Preflight and frame extraction
    video_out = os.path.join(out_dir, "master_film.mp4")
    if os.path.exists(video_out):
        probe = subprocess.run([
            "ffprobe", "-v", "error",
            "-show_entries", "stream=width,height,duration,codec_name",
            "-of", "json", video_out
        ], capture_output=True, text=True)
        probe_json = json.loads(probe.stdout) if probe.returncode == 0 else {}
        print(f"[✓] Stream Specs: {probe_json.get('streams', [{}])[0]}")

        print("[*] Extracting keyframe stills...")
        subprocess.run(["ffmpeg", "-y", "-ss", "00:00:00.500", "-i", video_out, "-frames:v", "1", "-update", "1", os.path.join(out_dir, "f_start.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-ss", "00:00:03.500", "-i", video_out, "-frames:v", "1", "-update", "1", os.path.join(out_dir, "f_mid.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["ffmpeg", "-y", "-ss", "00:00:06.500", "-i", video_out, "-frames:v", "1", "-update", "1", os.path.join(out_dir, "f_end.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"[✓] Keyframes extracted in {out_dir}/f_*.jpg")


def main():
    parser = argparse.ArgumentParser(description="Autonomous Google Flow Video Generation CLI")
    parser.add_argument("--prompt", required=True, help="Video prompt description")
    parser.add_argument("--ref-image", help="Path to character / reference image for conditioning")
    parser.add_argument("--model", choices=["omni", "veo"], default="omni", help="Model engine: omni (Flash) or veo (Veo 2)")
    parser.add_argument("--out-dir", default="./output/flow_generation", help="Output directory")
    parser.add_argument("--timeout", type=int, default=180, help="Max generation timeout in seconds")

    args = parser.parse_args()
    generate_flow_video(
        prompt=args.prompt,
        ref_image=args.ref_image,
        out_dir=args.out_dir,
        model_choice=args.model,
        duration_timeout=args.timeout
    )

if __name__ == "__main__":
    main()
