"""Generates three pairs of mock 'webpage screenshots' so the demo works
instantly with no upload and no external site needed:

  1. identical        -> baseline vs. an unchanged re-capture
  2. legitimate_change -> baseline vs. a rotated banner / updated date
     (the exact case classical pixel-diff gets wrong: it's a big pixel
     change but a human -- and a VLM -- would call it business as usual)
  3. defacement        -> baseline vs. a hacked/replaced page

These are drawn procedurally with OpenCV text/shapes. They are not scraped
from any real site.
"""
import numpy as np
import cv2


def _base_canvas(w=640, h=420):
    img = np.full((h, w, 3), 250, dtype=np.uint8)
    cv2.rectangle(img, (0, 0), (w, 70), (30, 40, 60), -1)  # navy header bar
    cv2.putText(img, "Ministry of Public Records", (24, 45), cv2.FONT_HERSHEY_DUPLEX, 0.9, (255, 255, 255), 1)
    return img


def make_baseline():
    img = _base_canvas()
    cv2.putText(img, "Welcome to the Official Portal", (30, 130), cv2.FONT_HERSHEY_DUPLEX, 0.8, (20, 20, 20), 1)
    cv2.putText(img, "Notice: Office hours 9:00 - 17:00, Mon-Fri", (30, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (60, 60, 60), 1)
    cv2.rectangle(img, (30, 210), (610, 260), (225, 235, 245), -1)
    cv2.putText(img, "Latest update: Form 27B now available online", (45, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 60, 90), 1)
    cv2.putText(img, "Contact: helpdesk@example.gov  |  Last updated: 12 Feb 2026", (30, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)
    return img


def make_legitimate_change():
    """Same site, same ownership, but a big seasonal promo banner replaces the
    notice area -- a large pixel delta that is still completely legitimate.
    This is deliberately drastic: it is the case that trips up classical
    pixel-diff (large % changed -> false "flagged") but that a VLM reading
    for *meaning* should still call ordinary site activity."""
    img = _base_canvas()
    cv2.putText(img, "Welcome to the Official Portal", (30, 130), cv2.FONT_HERSHEY_DUPLEX, 0.8, (20, 20, 20), 1)
    cv2.putText(img, "Notice: Office hours 9:00 - 17:00, Mon-Fri", (30, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (60, 60, 60), 1)
    # large, colorful seasonal promo banner replacing the whole notice block -- big pixel delta, still benign
    cv2.rectangle(img, (30, 205), (610, 320), (40, 160, 210), -1)
    cv2.putText(img, "Annual Public Holiday Notice", (55, 245), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)
    cv2.putText(img, "Offices closed 25-27 March for national holiday", (55, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1)
    cv2.putText(img, "Contact: helpdesk@example.gov  |  Last updated: 03 Mar 2026", (30, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (100, 100, 100), 1)
    return img


def make_defacement():
    """Same layout skeleton, hijacked content -- what an attacker's page might look like."""
    img = np.full((420, 640, 3), 10, dtype=np.uint8)
    cv2.rectangle(img, (0, 0), (640, 70), (10, 10, 10), -1)
    cv2.putText(img, "Ministry of Public Records", (24, 45), cv2.FONT_HERSHEY_DUPLEX, 0.9, (80, 80, 80), 1)
    cv2.putText(img, "HACKED BY G0STLY", (60, 190), cv2.FONT_HERSHEY_DUPLEX, 1.1, (0, 0, 255), 2)
    cv2.putText(img, "your security means nothing", (60, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 1)
    cv2.putText(img, "Contact: helpdesk@example.gov  |  Last updated: 12 Feb 2026", (30, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (90, 90, 90), 1)
    return img


def all_samples():
    return {
        "baseline": make_baseline(),
        "legitimate_change": make_legitimate_change(),
        "defacement": make_defacement(),
    }


if __name__ == "__main__":
    for name, img in all_samples().items():
        cv2.imwrite(f"sample_{name}.png", cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        print("wrote", f"sample_{name}.png")
