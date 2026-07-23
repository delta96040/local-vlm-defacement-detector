import streamlit as st
import numpy as np
import cv2
from PIL import Image
import io

from classical_diff import classical_verdict
from vlm_client import (
    check_ollama_available, extract_page_state, compare_states, parse_verdict,
    OllamaError, DEFAULT_MODEL,
)
from make_samples import all_samples

st.set_page_config(page_title="Local VLM Defacement Detector", layout="wide")

st.title("Website Defacement Detection — Local VLM Demo")
st.caption(
    "A from-scratch, open-source reproduction of the Layer 1 Visual Analysis idea I worked on "
    "during my internship: reading a page's *meaning* with a locally-hosted vision-language "
    "model instead of comparing pixels or DOM, so legitimate content changes don't get flagged "
    "as attacks. Runs entirely on your machine via Ollama — no cloud API, no page content ever "
    "leaves your laptop."
)

with st.expander("What this is (and isn't)", expanded=False):
    st.markdown(
        f"""
This is a **standalone, open-source rebuild** of the idea behind Layer 1, built against
[Ollama](https://ollama.com) (free, open source, runs locally) and a small open vision-language
model — by default `{DEFAULT_MODEL}` (~3.2GB, fits comfortably on a 6GB laptop GPU; drop to
`moondream` (~1.7GB) if you want more headroom). It does **not** use the production model,
proprietary prompts, Layer 2 malware-signature scanning, or Layer 3 content-hash checks from
the real Cyber-ShieldPro platform — those aren't open source and this demo doesn't claim to
reproduce them.

The demo includes a **classical pixel/perceptual-hash comparison mode** side by side with the
VLM mode, on purpose: it's the brittle baseline approach (Section 4.1 of the report) that
motivated the redesign, and seeing both side by side on the same image pair is the fastest way
to show *why* semantic comparison matters.
        """
    )

# ---------------------------------------------------------------- Ollama status
available, status_msg = check_ollama_available()
col_status, col_toggle = st.columns([3, 1])
with col_status:
    if available:
        st.success(f"✅ {status_msg}  (model: `{DEFAULT_MODEL}`)")
    else:
        st.warning(f"⚠️ {status_msg}")
        st.caption(
            "You can still explore the full UI and the classical-diff comparison below without "
            "Ollama running — the VLM columns will just stay empty until it's available."
        )

st.divider()

# ---------------------------------------------------------------- input selection
st.sidebar.header("Input")
mode = st.sidebar.radio("Choose a scenario", [
    "Sample: identical re-capture",
    "Sample: legitimate change (big visual delta, still benign)",
    "Sample: defacement",
    "Upload your own two images",
])

samples = all_samples()

if mode == "Sample: identical re-capture":
    baseline_rgb, current_rgb = samples["baseline"], samples["baseline"].copy()
elif mode == "Sample: legitimate change (big visual delta, still benign)":
    baseline_rgb, current_rgb = samples["baseline"], samples["legitimate_change"]
elif mode == "Sample: defacement":
    baseline_rgb, current_rgb = samples["baseline"], samples["defacement"]
else:
    b_file = st.sidebar.file_uploader("Baseline (trusted) screenshot", type=["png", "jpg", "jpeg"], key="b")
    c_file = st.sidebar.file_uploader("Current (new capture) screenshot", type=["png", "jpg", "jpeg"], key="c")
    if not (b_file and c_file):
        st.info("Upload both a baseline and a current screenshot in the sidebar to compare them.")
        st.stop()
    baseline_rgb = np.array(Image.open(b_file).convert("RGB"))
    current_rgb = np.array(Image.open(c_file).convert("RGB"))

col1, col2 = st.columns(2)
col1.image(baseline_rgb, caption="Baseline (trusted)")
col2.image(current_rgb, caption="Current (new capture)")

run = st.button("Run comparison", type="primary")

if run:
    st.divider()
    left, right = st.columns(2)

    # -------- classical baseline --------
    with left:
        st.subheader("Classical pixel / perceptual-hash diff")
        st.caption("The brittle approach: no understanding of meaning, just raw pixels.")
        verdict, pct, dist, heatmap = classical_verdict(baseline_rgb, current_rgb)
        badge = "🟢" if verdict == "MATCH" else "🔴"
        st.markdown(f"**{badge} {verdict}**")
        st.write(f"Changed pixels: **{pct:.1f}%**  ·  Perceptual hash distance: **{dist}** / 64")
        st.image(heatmap, caption="Pixel-difference heatmap")

    # -------- VLM --------
    with right:
        st.subheader(f"Local VLM semantic comparison ({DEFAULT_MODEL})")
        st.caption("Reads what each page says and means, then compares the meaning.")
        if not available:
            st.error("Ollama isn't available right now — see the setup instructions above / in the README.")
        else:
            with st.spinner("Extracting baseline page state..."):
                b_buf = io.BytesIO(); Image.fromarray(baseline_rgb).save(b_buf, format="PNG")
                try:
                    baseline_state = extract_page_state(b_buf.getvalue())
                except OllamaError as e:
                    st.error(str(e)); st.stop()
            with st.spinner("Extracting current page state..."):
                c_buf = io.BytesIO(); Image.fromarray(current_rgb).save(c_buf, format="PNG")
                try:
                    current_state = extract_page_state(c_buf.getvalue())
                except OllamaError as e:
                    st.error(str(e)); st.stop()
            with st.spinner("Comparing states..."):
                try:
                    comparison = compare_states(baseline_state, current_state)
                except OllamaError as e:
                    st.error(str(e)); st.stop()
            verdict, reason = parse_verdict(comparison)
            badge = {"MATCH": "🟢", "LEGITIMATE_CHANGE": "🟡", "POSSIBLE_DEFACEMENT": "🔴"}.get(verdict, "⚪")
            st.markdown(f"**{badge} {verdict}**")
            st.write(reason)
            with st.expander("Extracted page states"):
                st.text("Baseline:\n" + baseline_state)
                st.text("Current:\n" + current_state)

    st.divider()
    st.info(
        "Notice on the **legitimate change** scenario: the classical diff usually flags it "
        "(large pixel delta from the new banner), while the VLM should recognise it's still "
        "the same site with ordinary content churn. That gap is the whole point of the Layer 1 "
        "redesign this demo is modeled on."
    )

st.divider()
st.caption(
    "Built as a demo of one workstream from an AI/ML Practice School III internship at Aaizel "
    "International Technologies. Open source, local-only inference via Ollama, no external services."
)
