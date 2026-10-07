"""Render the app's logo (frontend/src/components/app/LogoMark.tsx) into the Android launcher icons and splash screens.

Usage (from the repo root, with any Python that has Pillow, e.g. the backend venv):
    backend/.venv/Scripts/python scripts/android_icons.py      # Windows
    backend/.venv/bin/python scripts/android_icons.py          # macOS/Linux
"""

import math
import re
from pathlib import Path

from PIL import Image, ImageDraw

RES = Path(__file__).resolve().parent.parent / "frontend/android/app/src/main/res"
BLUE = (44, 107, 237, 255)  # --primary in frontend/src/styles/tokens.css
WHITE = (255, 255, 255, 255)
# Same path, stroke and dash pattern as LogoMark.tsx (viewBox 0 0 64 64).
BUBBLE = "M32 15c-9.9 0-18 7.2-18 16.1 0 4.7 2.3 9 6 11.9l-1.6 6.4 7.1-3.5c2 .6 4.2.9 6.5.9 9.9 0 18-7.2 18-16.1S41.9 15 32 15Z"
STROKE, DASH, GAP = 3.2, 5.0, 3.2
SS = 4  # supersampling for smooth edges


def _cubic(p0, p1, p2, p3, steps=24):
    for i in range(1, steps + 1):
        t = i / steps
        yield tuple(
            (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * b + 3 * (1 - t) * t**2 * c + t**3 * d
            for a, b, c, d in zip(p0, p1, p2, p3)
        )


def flatten(path: str) -> list[tuple[float, float]]:
    """Polyline for the subset of SVG path syntax used by the logo: M, c, s/S, l, Z."""
    tokens = re.findall(r"[MmCcSsLlZz]|-?\d*\.?\d+", path)
    pts, cur, start, last_ctrl, cmd, i = [], (0.0, 0.0), (0.0, 0.0), None, None, 0

    def num():
        nonlocal i
        i += 1
        return float(tokens[i - 1])

    while i < len(tokens):
        if tokens[i].isalpha():
            cmd = tokens[i]
            i += 1
            if cmd in "Zz":
                pts.append(start)
                cur = start
                continue
        rel = cmd.islower()
        ox, oy = cur if rel else (0.0, 0.0)
        if cmd in "Mm":
            cur = start = (ox + num(), oy + num())
            pts.append(cur)
            cmd = "l" if rel else "L"
        elif cmd in "Ll":
            cur = (ox + num(), oy + num())
            pts.append(cur)
            last_ctrl = None
        elif cmd in "Cc":
            c1 = (ox + num(), oy + num())
            c2 = (ox + num(), oy + num())
            end = (ox + num(), oy + num())
            pts.extend(_cubic(cur, c1, c2, end))
            cur, last_ctrl = end, c2
        elif cmd in "Ss":
            c1 = (2 * cur[0] - last_ctrl[0], 2 * cur[1] - last_ctrl[1]) if last_ctrl else cur
            c2 = (ox + num(), oy + num())
            end = (ox + num(), oy + num())
            pts.extend(_cubic(cur, c1, c2, end))
            cur, last_ctrl = end, c2
    return pts


def dashes(pts, on, off):
    """Split a polyline into dash segments (lists of points) following an on/off pattern."""
    out, current, drawing, left = [], [pts[0]], True, on
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        pos = 0.0
        while seg - pos > 1e-9:
            step = min(left, seg - pos)
            pos += step
            t = pos / seg
            p = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
            if drawing:
                current.append(p)
            left -= step
            if left <= 1e-9:
                if drawing:
                    out.append(current)
                drawing = not drawing
                left = on if drawing else off
                current = [p]
    if drawing and len(current) > 1:
        out.append(current)
    return out


def draw_bubble(draw: ImageDraw.ImageDraw, scale: float, ox: float, oy: float):
    width = STROKE * scale
    for dash in dashes(flatten(BUBBLE), DASH, GAP):
        xy = [(ox + x * scale, oy + y * scale) for x, y in dash]
        draw.line(xy, fill=WHITE, width=max(1, round(width)))
        r = width / 2  # round caps and joins
        for x, y in xy:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=WHITE)


def logo(size: int, *, circle: bool, bubble_fraction: float = 1.0, background=None) -> Image.Image:
    """circle=True: blue disc + bubble (legacy icon). circle=False: bubble only, scaled into the middle."""
    big = size * SS
    img = Image.new("RGBA", (big, big), background or (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    if circle:
        draw.ellipse([0, 0, big - 1, big - 1], fill=BLUE)
    scale = big / 64 * bubble_fraction
    offset = (big - 64 * scale) / 2
    draw_bubble(draw, scale, offset, offset)
    return img.resize((size, size), Image.LANCZOS)


def main():
    densities = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}
    for name, d in densities.items():
        folder = RES / f"mipmap-{name}"
        icon = logo(round(48 * d), circle=True)
        icon.save(folder / "ic_launcher.png")
        icon.save(folder / "ic_launcher_round.png")
        # Adaptive icon: 108dp canvas, only the middle ~66dp is guaranteed visible.
        logo(round(108 * d), circle=False, bubble_fraction=0.62).save(folder / "ic_launcher_foreground.png")
    (RES / "values/ic_launcher_background.xml").write_text(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '    <color name="ic_launcher_background">#2C6BED</color>\n</resources>\n',
        encoding="utf-8",
    )
    for splash in RES.glob("drawable*/splash.png"):
        w, h = Image.open(splash).size
        img = Image.new("RGBA", (w, h), BLUE)
        mark = logo(round(min(w, h) * 0.32), circle=False, bubble_fraction=1.0)
        img.alpha_composite(mark, ((w - mark.width) // 2, (h - mark.height) // 2))
        img.convert("RGB").save(splash)
    print(f"Icons and splash screens written under {RES}")


if __name__ == "__main__":
    main()
