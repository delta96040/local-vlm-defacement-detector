# Website Defacement Detection — Local VLM Demo

A standalone, open-source demo of the idea behind the **Layer 1 Visual Analysis** redesign I
worked on: read a webpage screenshot's *meaning* with a locally-hosted vision-language model
instead of comparing pixels or DOM structure, so legitimate content changes (a new banner, an
updated notice) don't get flagged as attacks the way brittle pixel-diffing does.

**Runs entirely on your machine.** No cloud API. No page content ever leaves your laptop — the
model runs locally via [Ollama](https://ollama.com), which is free and open source.

## What it does

- Two comparison modes, shown side by side on the same image pair:
  1. **Classical pixel / perceptual-hash diff** — the brittle baseline approach. Pure OpenCV,
     no ML.
  2. **Local VLM semantic comparison** — extracts a structured description of each page
     (headline, content summary, suspicious elements) via a local vision-language model, then
     asks the same model to classify the relationship as `MATCH`, `LEGITIMATE_CHANGE`, or
     `POSSIBLE_DEFACEMENT`.
- Three built-in sample scenarios so it works instantly with no setup:
  - **Identical re-capture** — both approaches should say match.
  - **Legitimate change** — a large, colorful promo banner replaces a notice box. Big pixel
    delta, but still completely benign. This is the case classical diff usually gets wrong
    (false positive) and the VLM should get right.
  - **Defacement** — the page is replaced with a hacked/hijacked look.
- Or upload your own two screenshots to compare.

## What this demo does *not* include

It does not use the real Cyber-ShieldPro model, prompts, or the Layer 2 (malware-signature) or
Layer 3 (content-hash) checks from the production platform — those aren't open source, and I
worked on Layer 1 specifically, not the whole engine. This is a clean-room rebuild of the same
*idea* against an open model, for demonstration purposes.

## Setup

### 1. Install Ollama (free, open source, local LLM runtime)

Download from [ollama.com](https://ollama.com) (Windows/Mac/Linux). Then pull a small
vision-language model that fits comfortably on a 6GB laptop GPU:

```bash
ollama pull qwen2.5vl:3b      # ~3.2GB — default, good balance of quality and speed
# or, for an even lighter footprint:
ollama pull moondream          # ~1.7GB — faster, slightly less detailed descriptions
```

If you use a different model, edit `DEFAULT_MODEL` at the top of `vlm_client.py`.

Ollama needs to be running (`ollama serve`, or it auto-starts as a background service on
Windows/Mac) before you launch the app — the app checks for it automatically and tells you if
it isn't reachable.

### 2. Install Python dependencies and run

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Opens at `http://localhost:8501`. The app works even without Ollama running — the classical
diff column and sample scenarios still function, and it'll just tell you the VLM side is
unavailable until Ollama is up.

**Performance note:** on an RTX 3050 (6GB VRAM), `qwen2.5vl:3b` typically responds in a few
seconds per image on GPU. If Ollama falls back to CPU (e.g. VRAM is busy with something else),
expect it to take longer — still workable for a demo, just less snappy.

## Deploying a hosted version

Because this needs a local Ollama server, it **can't run on Streamlit Community Cloud** in
VLM mode (there's no GPU or Ollama there) — which is, fittingly, the same sovereignty
constraint that motivated running the real Layer 1 model on-premise in the first place. Two
options if you want something to point people at:

- Push the repo to GitHub and let people run it locally (the natural option here).
- Deploy just the classical-diff half to Streamlit Cloud as a lighter "concept preview," with
  the VLM panel showing the "Ollama not available" state — still demonstrates the UI and the
  false-positive problem with classical diffing.

## Files

| File | Purpose |
|---|---|
| `vlm_client.py` | Thin REST client for a local Ollama server (state extraction + comparison prompts) |
| `classical_diff.py` | Pixel-diff + perceptual-hash baseline, for contrast |
| `make_samples.py` | Generates the three built-in demo scenarios (no real site data used) |
| `app.py` | Streamlit UI |
| `requirements.txt` | Pinned, all open source |
