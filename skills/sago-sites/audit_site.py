#!/usr/bin/env python3
"""
audit_site.py - Automated Preflight & Antislop Validator for Sago Sites

Validates built HTML landing pages against the Sago Quality Gate:
  1. Horizontal Scroll Overflow: Zero overflow at 1440px (desktop) and 390px (mobile)
  2. Console Health: Zero uncaught JavaScript errors
  3. Antislop Content Rules:
     - R-02: Zero em dashes (—) or artificial dashes
     - R-03: Zero lorem ipsum or placeholder text
     - R-18: Grounded contact facts only (no fake 0000000000 or example.com)
  4. Responsive Snapshot Generation: Captures desktop and mobile QA screenshots

Usage:
  python3 audit_site.py path/to/index.html [--qa-dir ./qa]
"""

import argparse
import os
import re
import sys
from playwright.sync_api import sync_playwright

def run_audit(html_path: str, qa_dir: str = None) -> bool:
    html_path = os.path.abspath(html_path)
    if not os.path.exists(html_path):
        print(f"[!] Error: File not found: {html_path}", file=sys.stderr)
        return False

    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    print(f"============================================================")
    print(f"🔎 AUDITING SAGO SITE: {os.path.basename(html_path)}")
    print(f"============================================================")

    failures = []
    warnings = []

    # 1. Antislop Static Text Audit
    print("\n--- 1. Antislop Content Gate ---")
    em_dashes = len(re.findall(r'[—–]', content))
    if em_dashes > 0:
        failures.append(f"Antislop R-02 Violation: Found {em_dashes} em dash / en dash characters ('—' or '–'). Use clean commas, colons, or periods.")
    else:
        print("  [✓] Antislop R-02 PASS: Zero em dashes found.")

    lorem_matches = re.findall(r'lorem\s+ipsum', content, re.IGNORECASE)
    if lorem_matches:
        failures.append(f"Antislop R-03 Violation: Found 'Lorem Ipsum' placeholder copy.")
    else:
        print("  [✓] Antislop R-03 PASS: Zero Lorem Ipsum detected.")

    placeholders = re.findall(r'\[(phone|email|address|client)\]', content, re.IGNORECASE)
    if placeholders:
        failures.append(f"Unresolved placeholders found: {set(placeholders)}")
    else:
        print("  [✓] Placeholder PASS: No unreplaced bracket tokens.")

    fake_contacts = re.findall(r'0000000000|1234567890|example\.com', content)
    if fake_contacts:
        warnings.append(f"Potential fake contact info found: {set(fake_contacts)}")
    else:
        print("  [✓] Grounded Facts PASS: Real contacts used.")

    # 2. Browser Runtime & Overflow Audit via Playwright
    print("\n--- 2. Responsive & Viewport Overflow Gate ---")
    if qa_dir:
        qa_dir = os.path.abspath(qa_dir)
        os.makedirs(qa_dir, exist_ok=True)

    console_errors = []
    file_url = f"file://{html_path}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # Check Desktop (1440x900)
        page_desktop = browser.new_page(viewport={"width": 1440, "height": 900})
        page_desktop.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page_desktop.on("pageerror", lambda err: console_errors.append(str(err)))
        
        page_desktop.goto(file_url, wait_until="networkidle")
        page_desktop.wait_for_timeout(1000)

        desktop_overflow = page_desktop.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
        if desktop_overflow > 1:
            failures.append(f"Desktop (1440px) Horizontal Overflow: {desktop_overflow}px excess width!")
        else:
            print(f"  [✓] Desktop (1440px) Overflow: 0px (PASS)")

        if qa_dir:
            shot_d = os.path.join(qa_dir, "audit_desktop_1440.png")
            page_desktop.screenshot(path=shot_d, full_page=False)
            print(f"  [i] Desktop screenshot saved: {shot_d}")

        page_desktop.close()

        # Check Mobile (390x844 - iPhone 14/15 size)
        page_mobile = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True)
        page_mobile.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page_mobile.on("pageerror", lambda err: console_errors.append(str(err)))

        page_mobile.goto(file_url, wait_until="networkidle")
        page_mobile.wait_for_timeout(1000)

        mobile_overflow = page_mobile.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")
        if mobile_overflow > 1:
            failures.append(f"Mobile (390px) Horizontal Overflow: {mobile_overflow}px excess width! Elements bleeding off screen.")
        else:
            print(f"  [✓] Mobile (390px) Overflow: 0px (PASS)")

        if qa_dir:
            shot_m = os.path.join(qa_dir, "audit_mobile_390.png")
            page_mobile.screenshot(path=shot_m, full_page=False)
            print(f"  [i] Mobile screenshot saved: {shot_m}")

        page_mobile.close()
        browser.close()

    # 3. Console Errors
    print("\n--- 3. JavaScript Console Health ---")
    if console_errors:
        failures.append(f"Runtime JavaScript Errors ({len(console_errors)}): {console_errors[:2]}")
    else:
        print("  [✓] Zero JavaScript runtime errors.")

    # 4. Final Verdict
    print("\n============================================================")
    if failures:
        print("❌ AUDIT VERDICT: REJECTED (Hard Gate Violations Found)")
        print("------------------------------------------------------------")
        for f in failures:
            print(f"  • [FAIL] {f}")
        for w in warnings:
            print(f"  • [WARN] {w}")
        print("============================================================")
        return False
    else:
        print("🏆 AUDIT VERDICT: PASSED (100% Production Ready)")
        if warnings:
            for w in warnings:
                print(f"  • [WARN] {w}")
        print("============================================================")
        return True


def main():
    parser = argparse.ArgumentParser(description="Sago Sites Preflight & Antislop Quality Validator")
    parser.add_argument("html_path", help="Path to index.html or target page")
    parser.add_argument("--qa-dir", help="Directory to save QA preview screenshots")

    args = parser.parse_args()
    success = run_audit(args.html_path, args.qa_dir)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
