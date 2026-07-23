"""
Classical pixel-difference and perceptual-hash comparison — the brittle
baseline approach (Section 4.1 of the report) that the VLM-based Layer 1
redesign was built to replace. Included here deliberately, so the demo can
show *why* semantic comparison wins: this classical method flags ordinary
visual churn (a moved banner, a timestamp) as loudly as it flags a real
defacement, because it has no idea what either image *means*.

Pure OpenCV + NumPy, no ML, no dependencies beyond the fingerprint demo
already uses.
"""

import numpy as np
import cv2


def _to_gray_array(image_rgb, size=(256, 256)):
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    return cv2.resize(gray, size, interpolation=cv2.INTER_AREA)


def pixel_diff_percent(baseline_rgb, current_rgb, threshold=25) -> tuple[float, np.ndarray]:
    """Percentage of pixels that changed by more than `threshold` intensity
    levels, plus a visual diff heatmap."""
    a = _to_gray_array(baseline_rgb)
    b = _to_gray_array(current_rgb)
    diff = cv2.absdiff(a, b)
    changed_mask = (diff > threshold).astype(np.uint8)
    pct = 100.0 * changed_mask.sum() / changed_mask.size
    heatmap = cv2.applyColorMap(diff, cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    return pct, heatmap_rgb


def average_hash(image_rgb, hash_size=8) -> np.ndarray:
    """Simple average-hash perceptual fingerprint: shrink, grayscale,
    threshold against the mean. Returns a flat boolean array."""
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    small = cv2.resize(gray, (hash_size, hash_size), interpolation=cv2.INTER_AREA)
    return (small > small.mean()).flatten()


def hamming_distance(hash_a: np.ndarray, hash_b: np.ndarray) -> int:
    return int(np.count_nonzero(hash_a != hash_b))


def classical_verdict(baseline_rgb, current_rgb):
    """Returns (verdict, pixel_change_pct, hamming_dist, heatmap) using pure
    pixel/perceptual-hash comparison — no understanding of meaning at all."""
    pct, heatmap = pixel_diff_percent(baseline_rgb, current_rgb)
    ha, hb = average_hash(baseline_rgb), average_hash(current_rgb)
    dist = hamming_distance(ha, hb)

    if pct < 2 and dist <= 4:
        verdict = "MATCH"
    elif pct < 15 and dist <= 12:
        verdict = "FLAGGED (visual change detected)"
    else:
        verdict = "FLAGGED (large visual change)"
    return verdict, pct, dist, heatmap
