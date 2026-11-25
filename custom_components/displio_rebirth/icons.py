"""Crisp, scalable 1-bpp vector icons drawn with Pillow for Displio E-Ink cards.

Designed to stay razor-sharp at both small (16-24 px) and hero (44-64 px) sizes
without external font files or network calls.
"""

from __future__ import annotations

import math

from PIL import ImageDraw

# Friendly aliases (including common Home Assistant mdi:* names)
ICON_ALIASES: dict[str, str] = {
    "sunny": "sun",
    "weather-sunny": "sun",
    "clear-day": "sun",
    "clear_day": "sun",
    "cloudy": "cloud",
    "weather-cloudy": "cloud",
    "partlycloudy": "partly_cloudy",
    "partly-cloudy": "partly_cloudy",
    "weather-partly-cloudy": "partly_cloudy",
    "rainy": "rain",
    "pouring": "rain",
    "weather-rainy": "rain",
    "weather-pouring": "rain",
    "snowy": "snow",
    "weather-snowy": "snow",
    "lightning": "storm",
    "lightning-rainy": "storm",
    "weather-lightning": "storm",
    "weather-lightning-rainy": "storm",
    "windy": "wind",
    "weather-windy": "wind",
    "clear-night": "moon",
    "clear_night": "moon",
    "weather-night": "moon",
    "foggy": "fog",
    "weather-fog": "fog",
    "temp": "thermometer",
    "temperature": "thermometer",
    "humidity": "droplet",
    "water": "droplet",
    "water-percent": "droplet",
    "email": "mail",
    "email-outline": "mail",
    "envelope": "mail",
    "date": "calendar",
    "calendar-today": "calendar",
    "time": "clock",
    "clock-outline": "clock",
    "energy": "bolt",
    "flash": "bolt",
    "lightning-bolt": "bolt",
    "plug": "power",
    "power-plug": "power",
    "lamp": "light",
    "lightbulb": "light",
    "alert": "bell",
    "bell-ring": "bell",
    "alert-triangle": "warning",
    "door-open": "door",
    "lock-open": "unlock",
    "house": "home",
    "todo": "list",
    "format-list-bulleted": "list",
    "ok": "check",
    "error": "cross",
    "close": "cross",
    "trash-can": "trash",
    "delete": "trash",
}


def normalize_icon_name(name: str | None) -> str:
    """Normalize an icon name (stripping optional 'mdi:' prefix and resolving aliases)."""
    if not name:
        return ""
    clean = name.strip().lower()
    clean = clean.removeprefix("mdi:")
    return ICON_ALIASES.get(clean, clean)


def _draw_cloud_shape(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    s: int,
    fg: int,
    bg: int,
    w: int,
) -> None:
    """Draw a clean rounded cloud silhouette."""
    draw.ellipse([x + int(s * 0.10), y + int(s * 0.42), x + int(s * 0.48), y + int(s * 0.80)], fill=fg)
    draw.ellipse([x + int(s * 0.28), y + int(s * 0.22), x + int(s * 0.72), y + int(s * 0.68)], fill=fg)
    draw.ellipse([x + int(s * 0.54), y + int(s * 0.38), x + int(s * 0.92), y + int(s * 0.80)], fill=fg)
    draw.rectangle([x + int(s * 0.28), y + int(s * 0.54), x + int(s * 0.74), y + int(s * 0.80)], fill=fg)


def draw_icon(
    draw: ImageDraw.ImageDraw,
    name: str,
    x: int,
    y: int,
    size: int,
    fg: int,
    bg: int,
) -> bool:
    """Draw a vector icon inside the square [x, y, x+size, y+size].

    Returns True if the icon was recognized and drawn, False otherwise.
    """
    icon = normalize_icon_name(name)
    if not icon:
        return False

    s = size
    cx = x + s // 2
    cy = y + s // 2
    w = max(2, s // 14)

    if icon == "sun":
        r = int(s * 0.23)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fg)
        r1 = int(s * 0.33)
        r2 = int(s * 0.46)
        for deg in range(0, 360, 45):
            rad = math.radians(deg)
            x1 = cx + round(math.cos(rad) * r1)
            y1 = cy + round(math.sin(rad) * r1)
            x2 = cx + round(math.cos(rad) * r2)
            y2 = cy + round(math.sin(rad) * r2)
            draw.line([(x1, y1), (x2, y2)], fill=fg, width=w)
        return True

    if icon == "cloud":
        _draw_cloud_shape(draw, x, y, s, fg, bg, w)
        return True

    if icon == "partly_cloudy":
        # Small sun peeking from top-right behind cloud
        scx, scy = x + int(s * 0.66), y + int(s * 0.30)
        sr = int(s * 0.15)
        draw.ellipse([scx - sr, scy - sr, scx + sr, scy + sr], fill=fg)
        for deg in (-90, -45, 0, 45, -135):
            rad = math.radians(deg)
            x1 = scx + round(math.cos(rad) * int(s * 0.21))
            y1 = scy + round(math.sin(rad) * int(s * 0.21))
            x2 = scx + round(math.cos(rad) * int(s * 0.29))
            y2 = scy + round(math.sin(rad) * int(s * 0.29))
            draw.line([(x1, y1), (x2, y2)], fill=fg, width=max(1, w - 1))
        # Subtle gap halo then cloud
        _draw_cloud_shape(draw, x - int(s * 0.04), y + int(s * 0.08), int(s * 0.90), fg, bg, w)
        return True

    if icon == "rain":
        _draw_cloud_shape(draw, x, y - int(s * 0.12), int(s * 0.95), fg, bg, w)
        for frac in (0.28, 0.50, 0.72):
            rx = x + int(s * frac)
            draw.line([(rx, y + int(s * 0.74)), (rx - int(s * 0.07), y + int(s * 0.92))], fill=fg, width=w)
        return True

    if icon == "snow":
        _draw_cloud_shape(draw, x, y - int(s * 0.14), int(s * 0.95), fg, bg, w)
        dr = max(2, s // 18)
        for fx, fy in ((0.28, 0.78), (0.50, 0.86), (0.72, 0.78)):
            px, py = x + int(s * fx), y + int(s * fy)
            draw.ellipse([px - dr, py - dr, px + dr, py + dr], fill=fg)
        return True

    if icon == "storm":
        _draw_cloud_shape(draw, x, y - int(s * 0.14), int(s * 0.95), fg, bg, w)
        pts = [
            (x + int(s * 0.54), y + int(s * 0.62)),
            (x + int(s * 0.40), y + int(s * 0.80)),
            (x + int(s * 0.52), y + int(s * 0.80)),
            (x + int(s * 0.42), y + int(s * 0.98)),
            (x + int(s * 0.64), y + int(s * 0.74)),
            (x + int(s * 0.52), y + int(s * 0.74)),
        ]
        draw.polygon(pts, fill=fg)
        return True

    if icon == "wind":
        for fy, fx2 in ((0.30, 0.78), (0.52, 0.90), (0.74, 0.68)):
            ly = y + int(s * fy)
            draw.line([(x + int(s * 0.10), ly), (x + int(s * fx2), ly)], fill=fg, width=w)
            r = int(s * 0.09)
            draw.arc([x + int(s * fx2) - r, ly - 2 * r, x + int(s * fx2) + r, ly], 270, 90, fill=fg, width=w)
        return True

    if icon == "moon":
        r = int(s * 0.36)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fg)
        draw.ellipse(
            [cx - int(r * 0.35), cy - int(r * 1.15), cx + int(r * 1.35), cy + int(r * 0.65)],
            fill=bg,
        )
        return True

    if icon == "fog":
        for fy in (0.28, 0.46, 0.64, 0.82):
            ly = y + int(s * fy)
            draw.line([(x + int(s * 0.12), ly), (x + int(s * 0.88), ly)], fill=fg, width=w)
        return True

    if icon == "thermometer":
        bw = max(3, int(s * 0.12))
        draw.rounded_rectangle(
            [cx - bw, y + int(s * 0.10), cx + bw, y + int(s * 0.68)],
            radius=bw,
            outline=fg,
            width=w,
        )
        br = int(s * 0.19)
        draw.ellipse([cx - br, y + int(s * 0.58), cx + br, y + int(s * 0.58) + 2 * br], fill=fg)
        draw.line([(cx, y + int(s * 0.34)), (cx, y + int(s * 0.68))], fill=fg, width=max(2, bw - 1))
        return True

    if icon == "droplet":
        r = int(s * 0.27)
        by = y + int(s * 0.63)
        draw.ellipse([cx - r, by - r, cx + r, by + r], fill=fg)
        draw.polygon([(cx, y + int(s * 0.10)), (cx - r, by - int(r * 0.1)), (cx + r, by - int(r * 0.1))], fill=fg)
        return True

    if icon == "mail":
        x1, y1 = x + int(s * 0.08), y + int(s * 0.20)
        x2, y2 = x + int(s * 0.92), y + int(s * 0.80)
        draw.rectangle([x1, y1, x2, y2], outline=fg, width=w)
        draw.line([(x1, y1), (cx, y + int(s * 0.56)), (x2, y1)], fill=fg, width=w)
        return True

    if icon == "calendar":
        x1, y1 = x + int(s * 0.10), y + int(s * 0.18)
        x2, y2 = x + int(s * 0.90), y + int(s * 0.90)
        draw.rectangle([x1, y1, x2, y2], outline=fg, width=w)
        draw.rectangle([x1, y1, x2, y + int(s * 0.36)], fill=fg)
        for rx in (0.30, 0.70):
            px = x + int(s * rx)
            draw.line([(px, y + int(s * 0.08)), (px, y + int(s * 0.24))], fill=fg, width=w)
        # Small grid dots
        dr = max(1, s // 18)
        for gy in (0.50, 0.70):
            for gx in (0.30, 0.50, 0.70):
                px, py = x + int(s * gx), y + int(s * gy)
                draw.rectangle([px - dr, py - dr, px + dr, py + dr], fill=fg)
        return True

    if icon == "clock":
        r = int(s * 0.40)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=fg, width=w)
        draw.line([(cx, cy), (cx, cy - int(r * 0.60))], fill=fg, width=w)
        draw.line([(cx, cy), (cx + int(r * 0.45), cy + int(r * 0.20))], fill=fg, width=w)
        return True

    if icon == "home":
        # Roof
        draw.polygon(
            [(cx, y + int(s * 0.12)), (x + int(s * 0.10), y + int(s * 0.50)), (x + int(s * 0.90), y + int(s * 0.50))],
            fill=fg,
        )
        # Walls
        draw.rectangle([x + int(s * 0.20), y + int(s * 0.48), x + int(s * 0.80), y + int(s * 0.88)], fill=fg)
        # Door cutout
        draw.rectangle([cx - int(s * 0.10), y + int(s * 0.62), cx + int(s * 0.10), y + int(s * 0.88)], fill=bg)
        return True

    if icon == "light":
        r = int(s * 0.26)
        by = y + int(s * 0.38)
        draw.ellipse([cx - r, by - r, cx + r, by + r], outline=fg, width=w)
        draw.rectangle([cx - int(s * 0.12), y + int(s * 0.62), cx + int(s * 0.12), y + int(s * 0.78)], fill=fg)
        draw.line([(cx - int(s * 0.10), y + int(s * 0.86)), (cx + int(s * 0.10), y + int(s * 0.86))], fill=fg, width=w)
        return True

    if icon == "bolt":
        pts = [
            (x + int(s * 0.58), y + int(s * 0.08)),
            (x + int(s * 0.24), y + int(s * 0.54)),
            (x + int(s * 0.50), y + int(s * 0.54)),
            (x + int(s * 0.40), y + int(s * 0.92)),
            (x + int(s * 0.76), y + int(s * 0.44)),
            (x + int(s * 0.50), y + int(s * 0.44)),
        ]
        draw.polygon(pts, fill=fg)
        return True

    if icon == "power":
        r = int(s * 0.34)
        draw.arc([cx - r, cy - r, cx + r, cy + r], -60, 240, fill=fg, width=w)
        draw.line([(cx, y + int(s * 0.10)), (cx, cy)], fill=fg, width=w)
        return True

    if icon == "battery":
        draw.rectangle([x + int(s * 0.10), y + int(s * 0.28), x + int(s * 0.82), y + int(s * 0.72)], outline=fg, width=w)
        draw.rectangle([x + int(s * 0.82), y + int(s * 0.40), x + int(s * 0.92), y + int(s * 0.60)], fill=fg)
        draw.rectangle([x + int(s * 0.18), y + int(s * 0.36), x + int(s * 0.64), y + int(s * 0.64)], fill=fg)
        return True

    if icon == "wifi":
        dot_r = max(2, int(s * 0.08))
        by = y + int(s * 0.80)
        draw.ellipse([cx - dot_r, by - dot_r, cx + dot_r, by + dot_r], fill=fg)
        for frac in (0.24, 0.42, 0.60):
            r = int(s * frac)
            draw.arc([cx - r, by - r, cx + r, by + r], 225, 315, fill=fg, width=w)
        return True

    if icon in ("lock", "unlock"):
        draw.rounded_rectangle(
            [x + int(s * 0.18), y + int(s * 0.46), x + int(s * 0.82), y + int(s * 0.88)],
            radius=max(2, s // 14),
            fill=fg,
        )
        sr = int(s * 0.20)
        sx = cx + (int(s * 0.14) if icon == "unlock" else 0)
        draw.arc([sx - sr, y + int(s * 0.14), sx + sr, y + int(s * 0.56)], 180, 0, fill=fg, width=w)
        draw.line([(sx - sr, y + int(s * 0.35)), (sx - sr, y + int(s * 0.48))], fill=fg, width=w)
        if icon == "lock":
            draw.line([(sx + sr, y + int(s * 0.35)), (sx + sr, y + int(s * 0.48))], fill=fg, width=w)
        return True

    if icon == "door":
        draw.rectangle([x + int(s * 0.22), y + int(s * 0.12), x + int(s * 0.78), y + int(s * 0.88)], outline=fg, width=w)
        kr = max(2, s // 16)
        kx, ky = x + int(s * 0.64), cy
        draw.ellipse([kx - kr, ky - kr, kx + kr, ky + kr], fill=fg)
        return True

    if icon == "window":
        x1, y1 = x + int(s * 0.16), y + int(s * 0.16)
        x2, y2 = x + int(s * 0.84), y + int(s * 0.84)
        draw.rectangle([x1, y1, x2, y2], outline=fg, width=w)
        draw.line([(cx, y1), (cx, y2)], fill=fg, width=w)
        draw.line([(x1, cy), (x2, cy)], fill=fg, width=w)
        return True

    if icon == "bell":
        draw.pieslice([x + int(s * 0.22), y + int(s * 0.18), x + int(s * 0.78), y + int(s * 0.74)], 180, 360, fill=fg)
        draw.rectangle([x + int(s * 0.22), y + int(s * 0.46), x + int(s * 0.78), y + int(s * 0.72)], fill=fg)
        draw.rectangle([x + int(s * 0.14), y + int(s * 0.70), x + int(s * 0.86), y + int(s * 0.78)], fill=fg)
        dr = max(2, int(s * 0.08))
        draw.ellipse([cx - dr, y + int(s * 0.78), cx + dr, y + int(s * 0.78) + 2 * dr], fill=fg)
        return True

    if icon == "warning":
        pts = [(cx, y + int(s * 0.12)), (x + int(s * 0.10), y + int(s * 0.86)), (x + int(s * 0.90), y + int(s * 0.86))]
        draw.polygon(pts, outline=fg, width=w)
        draw.line([(cx, y + int(s * 0.36)), (cx, y + int(s * 0.62))], fill=fg, width=w)
        dr = max(1, w // 2 + 1)
        draw.ellipse([cx - dr, y + int(s * 0.72) - dr, cx + dr, y + int(s * 0.72) + dr], fill=fg)
        return True

    if icon == "check":
        draw.line(
            [(x + int(s * 0.16), cy), (x + int(s * 0.42), y + int(s * 0.76)), (x + int(s * 0.84), y + int(s * 0.24))],
            fill=fg,
            width=max(2, w + 1),
        )
        return True

    if icon == "cross":
        m = int(s * 0.20)
        draw.line([(x + m, y + m), (x + s - m, y + s - m)], fill=fg, width=max(2, w + 1))
        draw.line([(x + s - m, y + m), (x + m, y + s - m)], fill=fg, width=max(2, w + 1))
        return True

    if icon == "list":
        for fy in (0.26, 0.50, 0.74):
            ly = y + int(s * fy)
            dr = max(2, s // 18)
            draw.ellipse([x + int(s * 0.14) - dr, ly - dr, x + int(s * 0.14) + dr, ly + dr], fill=fg)
            draw.line([(x + int(s * 0.30), ly), (x + int(s * 0.86), ly)], fill=fg, width=w)
        return True

    if icon == "trash":
        draw.line([(x + int(s * 0.18), y + int(s * 0.24)), (x + int(s * 0.82), y + int(s * 0.24))], fill=fg, width=w)
        draw.rectangle([x + int(s * 0.38), y + int(s * 0.12), x + int(s * 0.62), y + int(s * 0.24)], outline=fg, width=w)
        draw.rectangle([x + int(s * 0.24), y + int(s * 0.24), x + int(s * 0.76), y + int(s * 0.88)], outline=fg, width=w)
        draw.line([(x + int(s * 0.42), y + int(s * 0.36)), (x + int(s * 0.42), y + int(s * 0.76))], fill=fg, width=max(1, w - 1))
        draw.line([(x + int(s * 0.58), y + int(s * 0.36)), (x + int(s * 0.58), y + int(s * 0.76))], fill=fg, width=max(1, w - 1))
        return True

    if icon == "arrow_up":
        draw.line([(cx, y + int(s * 0.18)), (cx, y + int(s * 0.84))], fill=fg, width=w)
        draw.line([(x + int(s * 0.26), y + int(s * 0.44)), (cx, y + int(s * 0.18)), (x + int(s * 0.74), y + int(s * 0.44))], fill=fg, width=w)
        return True

    if icon == "arrow_down":
        draw.line([(cx, y + int(s * 0.16)), (cx, y + int(s * 0.82))], fill=fg, width=w)
        draw.line([(x + int(s * 0.26), y + int(s * 0.56)), (cx, y + int(s * 0.82)), (x + int(s * 0.74), y + int(s * 0.56))], fill=fg, width=w)
        return True

    return False
