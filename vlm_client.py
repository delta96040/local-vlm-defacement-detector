"""
Thin client for a locally-running Ollama server, used to call a small
vision-language model (VLM) for semantic page-state extraction — the same
idea as the Layer 1 Visual Analysis redesign described in the report,
just built here from scratch against an open-source local model instead
of the proprietary production stack.

Nothing in this file talks to the internet. It only ever calls
http://localhost:11434, which is Ollama's local server address. If Ollama
isn't running, every function here raises a clear, catchable error so the
Streamlit app can fall back to demo/classical mode instead of crashing.
"""

import base64
import json
import requests

OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5vl:3b"  # ~3.2GB — comfortable on a 6GB laptop GPU

STATE_EXTRACTION_PROMPT = """You are inspecting a screenshot of a webpage for a security \
monitoring tool. Describe ONLY what is objectively visible. Respond in this exact format:

HEADLINE_TEXT: <the main heading or title text visible, or "none visible">
BODY_SUMMARY: <one or two sentence summary of the main visible content/topic>
SUSPICIOUS_ELEMENTS: <any hacker messages, unexpected logos, broken/replaced content, \
political slogans, or garbled layout — or "none">
OVERALL_TOPIC: <a few words describing what this page appears to be about>
"""

COMPARISON_PROMPT = """You are comparing two extracted webpage states for a defacement \
monitoring tool. Baseline (trusted, known-good) state:
---
{baseline}
---
Current (newly captured) state:
---
{current}
---
Classify the relationship between these two states as exactly one of:
MATCH — same page, same meaning, no action needed
LEGITIMATE_CHANGE — content changed but looks like normal site activity (news update, \
rotating banner, price change, timestamp, etc.)
POSSIBLE_DEFACEMENT — the topic, ownership, or meaning of the page appears to have changed, \
or suspicious/hacker-style content has appeared

Respond in this exact format:
VERDICT: <one of the three labels above>
REASON: <one sentence explaining why, referencing what specifically changed or didn't>
"""


class OllamaError(RuntimeError):
    """Raised when Ollama is unreachable or returns an error. Catch this in the
    UI layer to fall back to classical/demo mode."""


def _encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def check_ollama_available(model: str = DEFAULT_MODEL, timeout: float = 2.0) -> tuple[bool, str]:
    """Returns (is_available, message). Cheap check used by the UI to decide
    whether to show the live-VLM path or the offline/demo path."""
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=timeout)
        resp.raise_for_status()
        tags = [m["name"] for m in resp.json().get("models", [])]
        if not any(model.split(":")[0] in t for t in tags):
            return False, (
                f"Ollama is running, but '{model}' isn't pulled yet. "
                f"Run: ollama pull {model}"
            )
        return True, "Ollama is running and the model is available."
    except requests.exceptions.RequestException:
        return False, (
            "Ollama isn't running or isn't reachable at localhost:11434. "
            "Install it from https://ollama.com and run: ollama serve"
        )


def extract_page_state(image_bytes: bytes, model: str = DEFAULT_MODEL, timeout: float = 90.0) -> str:
    """Sends one image to the local VLM and returns its raw structured-text
    description of the page state."""
    payload = {
        "model": model,
        "prompt": STATE_EXTRACTION_PROMPT,
        "images": [_encode_image(image_bytes)],
        "stream": False,
        "options": {"temperature": 0.1},
    }
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise OllamaError(f"Could not reach Ollama: {e}") from e
    data = resp.json()
    if "response" not in data:
        raise OllamaError(f"Unexpected Ollama response: {data}")
    return data["response"].strip()


def compare_states(baseline_state: str, current_state: str, model: str = DEFAULT_MODEL,
                    timeout: float = 90.0) -> str:
    """Asks the local VLM (as a text-only call) to classify the relationship
    between two previously-extracted page states."""
    prompt = COMPARISON_PROMPT.format(baseline=baseline_state, current=current_state)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }
    try:
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=timeout)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise OllamaError(f"Could not reach Ollama: {e}") from e
    data = resp.json()
    if "response" not in data:
        raise OllamaError(f"Unexpected Ollama response: {data}")
    return data["response"].strip()


def parse_verdict(comparison_text: str) -> tuple[str, str]:
    """Pulls VERDICT and REASON lines out of the model's comparison response.
    Falls back gracefully if the model didn't follow the format exactly."""
    verdict, reason = "UNKNOWN", comparison_text
    for line in comparison_text.splitlines():
        if line.strip().upper().startswith("VERDICT:"):
            verdict = line.split(":", 1)[1].strip().upper()
        elif line.strip().upper().startswith("REASON:"):
            reason = line.split(":", 1)[1].strip()
    return verdict, reason
