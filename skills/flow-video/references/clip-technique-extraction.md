# Learning Prompt Techniques from Viral AI-Video Clips

When reference techniques live inside social-video posts (any generator app — harvest the technique, never the tool), run this loop: download, watch via multimodal model, distill to conditional rules.

## 1. Download without platform auth
X thread pages hydrate shells but often withhold video players and replies from automation. Pull the source mp4s through the public mirror instead (no credentials):

```bash
curl -s "https://api.fxtwitter.com/<handle>/status/<id>" | python3 -c "import json,sys; [print(m.get('url')) for m in json.load(sys.stdin).get('tweet',{}).get('media',{}).get('videos',[])]"
```

## 2. Watch via Gemini through the Antigravity proxy
Local transcription models are slow and weak on multilingual audio; prefer a multimodal model that sees frames and hears audio together. If the Gemini CLI free tier is ineligible, use the local Antigravity Claude proxy (`http://127.0.0.1:8080/v1/messages`, Anthropic schema) with a flash-tier Gemini model (e.g. `gemini-3.8-flash-tiered`). Full video files exceed message limits — `ffmpeg -vf fps=1` frames (3 representative frames per clip, base64 jpeg) suffice for visual technique analysis:

```bash
ffmpeg -y -i clip.mp4 -vf fps=1 clip_%02d.jpg
```

Prompt the model per clip for: on-screen content, camera language (shot size, lens feel, movement, depth of field), lighting design (named sources, direction, contrast), visible realism tricks (skin, grain, imperfections, physics, atmosphere), likely prompt techniques — then demand N concrete prompt rules for YOUR domain. End by tiering each rule through the fit-gate (SKILL.md): always / conditional / never.

## 3. Feed the pipeline, not the archive
Distilled rules go into the prompt-construction step as conditional blocks, never pasted wholesale. One clip-mining pass should change prompt wording measurably (e.g. diegetic light sources, material-mass tags, atmosphere particles) — if nothing changed, the pass was entertainment, not research.
