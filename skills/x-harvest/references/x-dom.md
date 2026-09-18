# X DOM cheat sheet (for x-browser-harvest)

Load this before writing any harvest JS. Selectors observed 2026-09-11;
re-verify with one probe read if X looks redesigned.

## Selectors

- Posts: `document.querySelectorAll('article')` — zero hits before settle is
  NORMAL. Scroll past headers, then re-read.
- Bio: `div[data-testid="UserDescription"]` → `innerText`.
- Post text: per-`article` `innerText`, slice 200–300 chars, newlines → ` | `.
- Permalinks: `article a[href*="/status/"]`, skip `/analytics` suffixed.
- Login check: `!!document.querySelector('a[href="/login"]')` must be false
  on an authed session; home timeline shows real posts.
- Search URL shape:
  `https://x.com/search?q=<urlencoded>&src=typed_query&f=live`

## Proven call shapes (browser_exec, local: true)

```python
# Login proof
new_tab("https://x.com/home")
wait_for_load()
info = page_info()  # title/url
print(js("(document.body ? document.body.innerText.slice(0, 400) : 'NO_BODY')"))
```

```python
# Profile harvest (sync scrolls only — no async sleeps)
goto_url("https://x.com/<handle>")
wait_for_load()
js("window.scrollBy(0, 2500)")
js("window.scrollBy(0, 2500)")
print("ARTICLES:", js("document.querySelectorAll('article').length"))
posts = js("(() => Array.from(document.querySelectorAll('article')).slice(0, 8).map(a => (a.innerText || '').slice(0, 300).replace(/\\n/g, ' | ')))()")
links = js("(() => { const out = []; document.querySelectorAll('article a[href*=\"/status/\"]').forEach(a => { const h = a.getAttribute('href'); if (h && h.indexOf('/analytics') < 0 && !out.includes(h)) out.push(h); }); return out.slice(0, 8); })()")
```

```python
# Search sweep — ALWAYS re-read; first read is usually empty
goto_url("https://x.com/search?q=<q>&src=typed_query&f=live")
wait_for_load()
js("window.scrollBy(0, 2000)")
# ...re-read articles on the NEXT call, not this one...
```

## Video pull (terminal, no API)

```bash
# Title-only probe first (validates cookies without downloading)
~/.local/bin/yt-dlp --cookies-from-browser chrome --skip-download --print title "https://x.com/<user>/status/<id>"
# Real pull, best mp4 ≤720p into the brief's film folder
~/.local/bin/yt-dlp --cookies-from-browser chrome -f "bv*[height<=720]+ba/b[height<=720]/b" \
  --merge-output-format mp4 -o "film/<slug>_xref.%(ext)s" "https://x.com/<user>/status/<id>"
ffprobe -v error -show_entries stream=width,height,duration,codec_name -of default=noprint_wrappers=1 film/<slug>_xref.mp4
```

If `--cookies-from-browser` fails headless (keyring locked), run the same
line in a desktop terminal with Chrome unlocked. Never paste cookie values
or profile files into chat.
