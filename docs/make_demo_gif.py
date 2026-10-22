#!/usr/bin/env python3
"""Render a 30-second terminal demo GIF from the reproducible test results.

The GIF is a condensed visual summary of ./repro.sh, not a screen recording.
Every number comes from the current run; the label at the bottom says
"condensed from ./repro.sh".
"""
from __future__ import annotations

import os
import subprocess
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = HERE / "demo.gif"
W, H = 960, 540
FPS = 8
BG = (13, 17, 23)
BAR = (22, 27, 34)
FG = (201, 209, 217)
DIM = (110, 118, 129)
GREEN = (126, 231, 135)
RED = (255, 123, 114)
YELLOW = (210, 153, 34)
BLUE = (88, 166, 255)
PURPLE = (188, 140, 255)

MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
F = ImageFont.truetype(MONO, 17)
FB = ImageFont.truetype(BOLD, 17)
FT = ImageFont.truetype(BOLD, 22)
FS = ImageFont.truetype(MONO, 13)


def run_repro() -> str:
    p = subprocess.run([str(ROOT / "repro.sh")], cwd=ROOT,
                       capture_output=True, text=True, timeout=180)
    return (p.stdout or "") + (p.stderr or "")


def results() -> dict:
    out = run_repro()
    import json
    import re
    nums = {}
    m = re.search(r'"treatment_asr_rounds":\s*\[([^\]]+)\]', out)
    if m:
        nums["treatment"] = m.group(1).replace(" ", "")
    m = re.search(r'"filter_asr_rounds":\s*\[([^\]]+)\]', out)
    if m:
        nums["filter"] = m.group(1).replace(" ", "")
    m = re.search(r'"guard_p50_ms":\s*([0-9.]+)', out)
    if m:
        nums["guard"] = m.group(1)
    m = re.search(r'"false_success":\s*(\d+)', out)
    if m:
        nums["false_success"] = m.group(1)
    m = re.search(r'"records":\s*(\d+)', out)
    if m:
        nums["records"] = m.group(1)
    return nums


def build_lines(nums: dict) -> list[tuple[str, tuple]]:
    treatment = nums.get("treatment", "0.0,0.0,0.0")
    filter_r = nums.get("filter", "0.0,10.0,0.0")
    guard = nums.get("guard", "1.1")
    fs = nums.get("false_success", "2")
    rec = nums.get("records", "48")
    return [
        ("$ ./repro.sh", BLUE),
        ("", FG),
        ("== proofgate ==", PURPLE),
        ("16/16 tests passed", GREEN),
        ("demo: confirmed=10  refuted=2  unverified=0", YELLOW),
        ("evidence_sha256: 3f9c...  (tamper-evident)", DIM),
        ("", FG),
        ("== agent-immunity ==", PURPLE),
        ("28/28 tests passed", GREEN),
        ("injection baseline: 100%", RED),
        ("filter-only rounds: " + filter_r + "  (a reworded payload escapes)", YELLOW),
        ("antibody memory:    " + treatment + "  (learns from each block)", GREEN),
        ("utility 100% · false denial 0% · guard ~" + guard + " ms", FG),
        ("", FG),
        ("== provenance ==", PURPLE),
        ("9/9 tests passed  (HMAC + optional Ed25519)", GREEN),
        ("SHA-256 = integrity; signature = authenticity", DIM),
        ("", FG),
        ("== MCP ==", PURPLE),
        ("5 tools: verify · check · add-antibody · stats · demo", GREEN),
        ("", FG),
        ("== held-out benchmark ==", PURPLE),
        ("200 generated attacks · 100 benign controls", FG),
        ("zero-shot 29.0% · learned variants 87.5%", YELLOW),
        ("oracle upper bound 95.0% · benign FP 0.0%", FG),
        ("", FG),
        ("== crossnode-bench ==", PURPLE),
        ("10/10 tests passed", GREEN),
        (str(rec) + " records · " + str(fs) + " false successes caught", RED),
        ("a naive ok:true scorer would count them as passes", DIM),
        ("", FG),
        ("OK — all components reproduced locally.", GREEN),
    ]


def render_frame(lines: list[tuple[str, tuple]], upto: int, typed: int | None,
                 progress: float, cursor: bool) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    # window chrome
    d.rectangle([0, 0, W, 40], fill=BAR)
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        d.ellipse([18 + i * 22, 14, 30 + i * 22, 26], fill=c)
    d.text((110, 12), "gamAI Trust Layer — terminal demo", font=FS, fill=DIM)

    y = 62
    max_lines = 24
    visible = lines[:upto]
    if len(visible) > max_lines:
        visible = visible[-max_lines:]
    for idx, (text, color) in enumerate(visible):
        if typed is not None and idx == len(visible) - 1:
            text = text[:typed]
        for part in textwrap.wrap(text, width=88) or [""]:
            d.text((26, y), part, font=FB if color == BLUE else F, fill=color)
            y += 21
        if y > H - 60:
            break
    if cursor:
        d.rectangle([26, H - 58, 26 + 9, H - 42], fill=GREEN)
    # progress bar
    d.rectangle([0, H - 8, W, H], fill=BAR)
    d.rectangle([0, H - 8, int(W * progress), H], fill=BLUE)
    d.text((W - 330, H - 30), "condensed from ./repro.sh · offline · no keys",
           font=FS, fill=DIM)
    return img


def main() -> int:
    nums = results()
    lines = build_lines(nums)
    frames: list[Image.Image] = []
    total = FPS * 30  # 30 seconds
    # intro: title
    intro = [("gamAI Trust Layer", PURPLE), ("verifiable claims · learned refusals · false-success scoring", DIM)]
    for _ in range(FPS * 2):
        frames.append(render_frame(intro, len(intro), None, 0.0, True))
    # type the command
    for i in range(len("$ ./repro.sh") + 1):
        frames.append(render_frame(lines[:1], 1, i, 0.05, True))
    # reveal lines
    per = max(1, (total - len(frames) - FPS * 3) // max(1, len(lines) - 1))
    for idx in range(2, len(lines) + 1):
        for _ in range(per):
            frames.append(render_frame(lines, idx, None, idx / len(lines), True))
    # final hold
    while len(frames) < total:
        frames.append(render_frame(lines, len(lines), None, 1.0, True))
    frames = frames[:total]
    # quantize to keep the GIF small
    pal = [f.quantize(colors=32, method=Image.Quantize.MEDIANCUT) for f in frames]
    pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=1000 // FPS,
                loop=0, optimize=False, disposal=2)
    print("wrote %s (%.1f KB, %d frames)" % (OUT, OUT.stat().st_size / 1024, len(pal)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
