"""Crop, resize and compress the site photos to WebP.

    python tools/build_photos.py <folder with the downloaded originals>

Each output size matches how large the photo is actually shown, so phones
never download desktop-sized files. Sources and credits: CREDITS.md and
core/photos.py.
"""
import sys
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

OUT = Path(__file__).resolve().parent.parent / "static" / "img" / "photos"
QUALITY = 52

# name: (source file, [(width, height), ...], focus point (x, y) for cropping[, quality, smoothing radius])
# A 4-value focus (left, top, right, bottom as fractions) crops to that box first, to zoom in.
# Busy scenes (river rocks, foliage) get lower quality plus a very light blur:
# invisible at display size, but it halves the file size.
PHOTOS = {
    # Hero: wide on desktop; a taller crop on phones.
    "hero-guiting": ("hi-c09.jpg", [(1600, 900), (1100, 619)], (0.5, 0.97)),
    "hero-guiting-m": ("hi-c09.jpg", [(720, 640)], (0.3, 0.38, 0.95, 0.98)),
    "hero-coast": ("hi-c11.jpg", [(1100, 619)], (0.5, 0.55)),
    "hero-cantingas": ("hi-c01.jpg", [(1100, 619)], (0.5, 0.5), 38, 0.7),
    # Homepage "Discover Sibuyan" gallery (4:3).
    "g-guiting": ("hi-c03.jpg", [(800, 600), (400, 300)], (0.5, 0.4), 46, 0.3),
    "g-cantingas": ("hi-c02.jpg", [(800, 600), (400, 300)], (0.5, 0.6), 42, 0.5),
    "g-coast": ("hi-c12.jpg", [(800, 600), (400, 300)], (0.45, 0.5)),
    # Tourism page headers (16:9) and small gallery photos.
    "t-guiting": ("hi-c08.jpg", [(1200, 675), (600, 338)], (0.5, 0.45), 42, 0.4),
    "t-cantingas": ("hi-c01.jpg", [(1200, 675), (600, 338)], (0.5, 0.55), 38, 0.7),
    "s-ridge": ("hi-c06.jpg", [(600, 450), (300, 225)], (0.6, 0.5)),
    "s-forest": ("hi-c04.jpg", [(600, 450), (300, 225)], (0.5, 0.5)),
    "s-nepenthes": ("hi-c10.jpg", [(360, 480)], (0.5, 0.55)),
}


def main(src_dir):
    src_dir = Path(src_dir)
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for name, (src, sizes, focus, *opts) in PHOTOS.items():
        quality, blur = (opts + [QUALITY, 0])[:2] if opts else (QUALITY, 0)
        img = Image.open(src_dir / src).convert("RGB")
        if len(focus) == 4:
            l, t, r, b = focus
            img = img.crop((int(l * img.width), int(t * img.height), int(r * img.width), int(b * img.height)))
            focus = (0.5, 0.5)
        for w, h in sizes:
            out = OUT / f"{name}-{w}.webp"
            fitted = ImageOps.fit(img, (w, h), method=Image.LANCZOS, centering=focus)
            if blur:
                fitted = fitted.filter(ImageFilter.GaussianBlur(blur))
            fitted.save(out, "WEBP", quality=quality, method=6)
            total += out.stat().st_size
            print(f"{out.name:28} {out.stat().st_size / 1024:6.1f} KB")
    print(f"total {total / 1024:.0f} KB")


if __name__ == "__main__":
    main(sys.argv[1])
