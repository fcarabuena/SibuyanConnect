"""Draw the PWA icons (leaf-and-wave mark) with Pillow. No design tools needed.

    python tools/make_icons.py
"""
from math import cos, pi, sin
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent.parent / "static" / "icons"
GREEN, BLUE, WHITE, MINT = "#1F5E46", "#1C4E80", "#FFFFFF", "#EAF4EE"


def wave(d, s, off, y, amp, x0, x1, width, colour):
    pts = [(off + x * s, off + (y + amp * sin((x - x0) / 4 * pi)) * s) for x in [x0 + i * 0.1 for i in range(int((x1 - x0) * 10) + 1)]]
    d.line(pts, fill=colour, width=width, joint="curve")


def draw(size, maskable=False):
    scale = 4  # draw large, then downsample for smooth edges
    big = size * scale
    img = Image.new("RGB", (big, big), WHITE)
    d = ImageDraw.Draw(img)
    s = big / 32 * (0.62 if maskable else 0.78)
    off = (big - 32 * s) / 2
    # Leaf: an ellipse tilted 45 degrees, drawn on its own layer and pasted in.
    lw, lh = int(19 * s), int(8.5 * s)
    leaf = Image.new("L", (lw, lh), 0)
    ImageDraw.Draw(leaf).ellipse([0, 0, lw - 1, lh - 1], fill=255)
    leaf = leaf.rotate(42, expand=True, resample=Image.BICUBIC)
    cx, cy = off + 15.4 * s, off + 11.6 * s
    img.paste(GREEN, (int(cx - leaf.width / 2), int(cy - leaf.height / 2)), leaf)
    d.line([(off + 10.5 * s, off + 16.5 * s), (off + 20 * s, off + 7 * s)], fill=WHITE, width=max(2, int(1.3 * s)))
    wave(d, s, off, 23.2, -0.8, 4, 28, max(3, int(1.7 * s)), BLUE)
    wave(d, s, off, 27.2, -0.6, 7, 25, max(3, int(1.7 * s)), BLUE)
    img = img.resize((size, size), Image.LANCZOS)
    if not maskable:
        img = img.convert("RGBA")
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 5, fill=255)
        img.putalpha(mask)
    return img


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    draw(192).save(OUT / "icon-192.png", optimize=True)
    draw(512).save(OUT / "icon-512.png", optimize=True)
    draw(512, maskable=True).save(OUT / "icon-maskable-512.png", optimize=True)
    print("Icons written to", OUT)
