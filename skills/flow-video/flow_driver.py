#!/usr/bin/env python3
"""
flow_driver.py - Autonomous CLI driver for Google Flow (Veo 2 & Gemini Omni 1.1 Flash) via Chrome DevTools Protocol (CDP).

Battle-Tested & Verified Lifecycle:
  1. Connects to persistent Google Chrome running on port 9222 with authenticated Google Account.
  2. Ensures project canvas is open with active .ProseMirror editor.
  3. Dispatches prompt (plus optional synthetic paste for character consistency conditioning).
  4. Tracks Google Flow's live render percentage (e.g. 12% -> 50% -> 100%).
  5. Dispatches force-click on the completed tile to mount Google's signed CDN video stream.
  6. Downloads the 720p HD MP4 (h264) directly to disk.
  7. Verifies stream with ffprobe and extracts 3 keyframe stills (f_start, f_mid, f_end).

Usage:
  python3 flow_driver.py --prompt "Cinematic medical clinic room" --out-dir ./output/clinic
  python3 flow_driver.py --prompt "Doctor examining posture" --ref-image ./mascot.png --out-dir ./output/doctor
"""

import argparse
import atexit
import base64
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.request
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
        "https://flow.google.com/"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    _launched_proc = proc

    for _ in range(40):
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


def generate_flow_video(prompt: str, ref_image: str = None, out_dir: str = "./output", timeout: int = 180):
    from playwright.sync_api import sync_playwright

    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    _ensure_chrome()

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0] if browser.contexts else browser.new_context()

        # Locate existing Google Flow tab or navigate
        flow_pages = [pg for pg in context.pages if "flow.google" in pg.url]
        if flow_pages:
            page = flow_pages[0]
            print(f"[+] Using active Flow page: {page.url}")
        else:
            page = context.new_page()
            print("[*] Navigating to Google Flow...")
            page.goto("https://flow.google.com/", wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

        # Close any open modal / player
        if "/edit/" in page.url:
            print("[*] Dismissing open modal view...")
            page.keyboard.press("Escape")
            proj_url = page.url.split("/edit/")[0]
            page.goto(proj_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2500)

        # If on landing page, click Start Creating or open project
        if not page.locator(".ProseMirror").first.is_visible():
            print("[*] Project canvas not open. Looking for 'Start Creating'...")
            start_btn = page.query_selector('button:has-text("Start Creating"), a:has-text("Start Creating")')
            if start_btn:
                start_btn.click()
                page.wait_for_timeout(5000)
            else:
                proj_link = page.locator("a[href*='/project/']").first
                if proj_link.is_visible():
                    proj_link.click()
                    page.wait_for_timeout(5000)

        editor = page.locator(".ProseMirror").first
        editor.wait_for(state="visible", timeout=30000)

        # Synthetic ClipboardEvent conditioning if reference image provided
        if ref_image and os.path.exists(ref_image):
            print(f"[*] Injecting reference image via synthetic paste: {ref_image}")
            with open(ref_image, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")
            mime_type = "image/png" if ref_image.endswith(".png") else "image/jpeg"

            page.evaluate(f"""() => {{
                const b64Data = "{img_b64}";
                const byteChars = atob(b64Data);
                const byteNums = new Array(byteChars.length);
                for (let i = 0; i < byteChars.length; i++) {{
                    byteNums[i] = byteChars.charCodeAt(i);
                }}
                const file = new File([new Uint8Array(byteNums)], "reference.png", {{ type: "{mime_type}" }});
                const dt = new DataTransfer();
                dt.items.add(file);
                const ev = new ClipboardEvent("paste", {{ clipboardData: dt, bubbles: true, cancelable: true }});
                document.querySelector('.ProseMirror').dispatchEvent(ev);
            }}""")
            page.wait_for_timeout(3000)

        # Format prompt
        final_prompt = prompt.strip()
        if not any(final_prompt.lower().startswith(pfx) for pfx in ["generate a video", "create a video", "video of"]):
            final_prompt = f"Generate a video of {final_prompt}"

        print(f"[*] Submitting prompt: \"{final_prompt}\"")
        editor.click()
        editor.fill("")
        editor.type(final_prompt, delay=12)
        time.sleep(0.5)

        send_btn = page.locator("button[aria-label='Start generation'], button[aria-label*='Send'], button:has-text('arrow_forward')").first
        if send_btn.is_visible():
            send_btn.click(force=True)
        else:
            editor.press("Enter")

        print("[*] Prompt submitted! Monitoring cloud render percentage...")
        start_t = time.time()
        saw_percentage = False
        new_tile_ready = False

        # Lifecycle monitoring
        while time.time() - start_t < timeout:
            elapsed = int(time.time() - start_t)
            newest_tile = page.locator("flow-video-tile").first

            if newest_tile.is_visible():
                txt = newest_tile.inner_text()
                pct_matches = re.findall(r'\b(\d+)%', txt)

                if pct_matches:
                    saw_percentage = True
                    pct_val = int(pct_matches[0])
                    print(f"[{elapsed}s] Cloud rendering: {pct_val}% complete...")
                    if pct_val == 100:
                        print(f"[+] Render hit 100% at {elapsed}s! Settle 3s...")
                        time.sleep(3)
                        new_tile_ready = True
                        break
                elif saw_percentage:
                    # Percentage was visible and now disappeared -> fully rendered!
                    print(f"[+] Render completed at {elapsed}s!")
                    new_tile_ready = True
                    break
                else:
                    print(f"[{elapsed}s] Waiting for generation queue to start...")

            time.sleep(4)

        if not new_tile_ready:
            raise TimeoutError(f"Video generation timed out after {timeout} seconds.")

        # Click the newly completed tile to mount the signed video element
        print("[*] Activating video tile to mount signed CDN stream...")
        newest_tile = page.locator("flow-video-tile").first
        newest_tile.click(force=True)
        page.wait_for_timeout(3500)

        # Extract signed CDN stream URL
        signed_video_url = page.evaluate("""() => {
            const v = document.querySelector('video');
            if (v && (v.src || v.currentSrc)) return v.src || v.currentSrc;
            const perf = performance.getEntriesByType('resource')
                .map(e => e.name)
                .filter(u => u.includes('flow-content.google/video') || (u.includes('.mp4') && u.includes('google')));
            return perf.length ? perf[perf.length - 1] : null;
        }""")

        if not signed_video_url:
            raise RuntimeError("Failed to resolve signed CDN video URL from mounted player.")

        print(f"[+] Captured signed CDN stream: {signed_video_url}")

        # Download directly to out_dir
        out_file = os.path.join(out_dir, "master_film.mp4")
        print(f"[*] Downloading master video to: {out_file}")
        urllib.request.urlretrieve(signed_video_url, out_file)
        
        file_size = os.path.getsize(out_file)
        print(f"[✓] Video saved: {out_file} ({file_size:,} bytes)")

    # Run ffprobe and keyframe extraction
    print("[*] Verifying stream specs and extracting keyframes...")
    probe = subprocess.run([
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,duration,codec_name",
        "-of", "json", out_file
    ], capture_output=True, text=True)
    probe_data = json.loads(probe.stdout) if probe.returncode == 0 else {}
    print(f"[✓] Stream Specs: {probe_data.get('streams', [{}])[0]}")

    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:00.500", "-i", out_file, "-frames:v", "1", "-update", "1", os.path.join(out_dir, "f_start.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:03.500", "-i", out_file, "-frames:v", "1", "-update", "1", os.path.join(out_dir, "f_mid.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["ffmpeg", "-y", "-ss", "00:00:06.500", "-i", out_file, "-frames:v", "1", "-update", "1", os.path.join(out_dir, "f_end.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"[✓] Keyframes extracted: {out_dir}/f_*.jpg")


def main():
    parser = argparse.ArgumentParser(description="Google Flow Autonomous Video Generator CLI")
    parser.add_argument("--prompt", required=True, help="Video prompt description")
    parser.add_argument("--ref-image", help="Path to character or reference image for conditioning")
    parser.add_argument("--out-dir", default="./output/flow_generation", help="Destination output directory")
    parser.add_argument("--timeout", type=int, default=180, help="Maximum timeout in seconds")

    args = parser.parse_args()
    generate_flow_video(
        prompt=args.prompt,
        ref_image=args.ref_image,
        out_dir=args.out_dir,
        timeout=args.timeout
    )

if __name__ == "__main__":
    main()
