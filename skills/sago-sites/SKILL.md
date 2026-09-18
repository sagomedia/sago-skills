---
name: sago-sites
description: "Build high-converting client demo landing pages and scrollytelling sites in 30 minutes via Human-in-the-Loop blueprints and automated Antislop Quality Gate validation."
version: 1.0.0
author: Sago Automation
license: MIT
platforms: [linux, macos, windows]
metadata:
  tags: [webdev, landing-pages, antislop, blueprints, scrollytelling, audit]
---

# Sago Sites Skill

A deterministic, zero-hallucination framework for autonomous AI coding agents to build high-converting, mobile-optimized single-page client demo sites for local businesses, clinics, colleges, and studios in **30 minutes**.

Paired with an automated preflight Antislop Quality Gate validator (`audit_site.py`).

---

## 30-Minute Human-in-the-Loop Protocol

```
[Min 0–5]   Phase 1: Lead Research & Fact Grounding (Agent reads briefs/<slug>.json)
[Min 5–8]   Phase 2: Blueprint Selection (Agent routes industry to verified template)
[Min 8–20]  Phase 3: Code Assembly (Slotting client facts, video scrub / hero film)
[Min 20–25] Phase 4: Antislop Gate Audit (audit_site.py runs headless Playwright)
[Min 25–30] Phase 5: Live GitHub Pages / Cloudflare Deployment
```

---

## The Antislop Quality Gate

Every site must pass `audit_site.py` before presenting to a client:

1. **Horizontal Viewport Gate**:
   - `scrollWidth == innerWidth` at 1440px desktop.
   - `scrollWidth == innerWidth` at 390px mobile (iPhone 14/15 portrait).
   - Zero horizontal scrollbars or element bleed.
2. **Antislop Copywriting Gate**:
   - **R-02**: Zero em dashes (`—`) or synthetic en dashes (`–`). Use natural commas or periods.
   - **R-03**: Zero Lorem Ipsum or placeholder copy.
   - **R-18**: Grounded data only (verified phone numbers, real ratings, actual street addresses).
3. **Console Health Gate**:
   - Zero uncaught JavaScript errors on load.

---

## CLI Validator Usage

```bash
# Run the automated preflight audit:
python3 audit_site.py path/to/index.html --qa-dir ./qa

# Exit code 0 = 100% Production Ready (PASS)
# Exit code 1 = Hard Gate Violations (REJECTED)
```
