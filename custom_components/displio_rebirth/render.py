"""264x176 1-bpp monochrome E-Ink framebuffer renderer using Pillow.

Supports Displio-inspired card layouts (classic, split, list, 2x2 grid)
in both landscape (264x176) and portrait (176x264) orientations, with crisp
scalable vector icons.
"""

from __future__ import annotations

import io
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .const import EPD_FB_SIZE, EPD_HEIGHT, EPD_WIDTH
from .icons import draw_icon, normalize_icon_name

_FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/ttf-dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/ttf-dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a clean TrueType font with fallback to Pillow's built-in font."""
    candidates = _FONT_CANDIDATES if bold else tuple(reversed(_FONT_CANDIDATES))
    for path in candidates:
        if Path(path).is_file():
            try:
                return ImageFont.truetype(path, size=size)
            except OSError:
                continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _text_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> tuple[int, int]:
    """Return (width, height) of a single line of text."""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_centered(
    draw: ImageDraw.ImageDraw,
    cx: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: int,
) -> None:
    tw, _ = _text_size(draw, text, font)
    draw.text((cx - tw // 2, y), text, fill=fill, font=font)


def _fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_w: int,
    start_size: int,
    min_size: int = 12,
    bold: bool = True,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Pick the largest font size that fits text inside max_w."""
    for sz in range(start_size, min_size - 1, -2):
        f = _load_font(sz, bold=bold)
        tw, _ = _text_size(draw, text, f)
        if tw <= max_w:
            return f
    return _load_font(min_size, bold=bold)


def _finalize_canvas(img: Image.Image, portrait: bool) -> bytes:
    """Rotate portrait 176x264 canvas to physical 264x176 and export EPD bytes."""
    if portrait:
        img = img.transpose(Image.Transpose.ROTATE_90)
    return image_to_epd_bytes(img, dither=False, invert=False)


def image_to_epd_bytes(
    image: Image.Image,
    dither: bool = True,
    invert: bool = False,
) -> bytes:
    """Convert any PIL Image into a 5,808-byte Displio E-Ink framebuffer.

    Format: 264x176, row-major, MSB-first, 1 = black ink, 0 = white background.
    """
    img = ImageOps.contain(image.convert("L"), (EPD_WIDTH, EPD_HEIGHT))
    canvas = Image.new("L", (EPD_WIDTH, EPD_HEIGHT), 255)
    offset_x = (EPD_WIDTH - img.width) // 2
    offset_y = (EPD_HEIGHT - img.height) // 2
    canvas.paste(img, (offset_x, offset_y))

    if invert:
        canvas = ImageOps.invert(canvas)

    dither_mode = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
    mono = canvas.convert("1", dither=dither_mode)

    # Pillow '1' mode uses 1=white, 0=black; Displio EPD uses 1=black, 0=white.
    raw = bytes(b ^ 0xFF for b in mono.tobytes())
    assert len(raw) == EPD_FB_SIZE
    return raw


def render_image_bytes(
    data: bytes,
    dither: bool = True,
    invert: bool = False,
) -> bytes:
    """Decode encoded image bytes (PNG/JPEG/BMP/etc.) into a 5,808-byte framebuffer."""
    with Image.open(io.BytesIO(data)) as img:
        return image_to_epd_bytes(img, dither=dither, invert=invert)


def _render_split_card(
    title: str,
    body: str,
    subtitle: str,
    footer: str,
    icon: str,
    details: list[dict[str, Any] | str] | None,
    invert: bool,
    portrait: bool,
) -> bytes:
    """Render the iconic Displio split card (dark hero panel + light info panel)."""
    w, h = (EPD_HEIGHT, EPD_WIDTH) if portrait else (EPD_WIDTH, EPD_HEIGHT)
    dark = 255 if invert else 0
    light = 0 if invert else 255
    img = Image.new("L", (w, h), light)
    draw = ImageDraw.Draw(img)

    has_icon = bool(normalize_icon_name(icon))

    if portrait:
        # Top dark hero panel (height ~146 px), bottom light panel (~118 px)
        split_y = 148
        draw.rectangle([0, 0, w, split_y], fill=dark)
        if title:
            ft = _fit_font(draw, title.upper(), w - 16, 18, 12, bold=True)
            _draw_centered(draw, w // 2, 10, title.upper(), ft, light)
        if has_icon:
            draw_icon(draw, icon, (w - 64) // 2, 40, 64, fg=light, bg=dark)
        if subtitle:
            fs = _fit_font(draw, subtitle, w - 16, 16, 12, bold=False)
            _draw_centered(draw, w // 2, 118, subtitle, fs, light)

        # Bottom light panel: big value + optional details/footer
        y = split_y + 10
        if body:
            lines = body.splitlines()
            if len(lines) == 1 and len(lines[0]) <= 12:
                fb = _fit_font(draw, lines[0], w - 16, 34, 18, bold=True)
                _draw_centered(draw, w // 2, y, lines[0], fb, dark)
                y += 44
            else:
                fb = _load_font(15, bold=False)
                for ln in lines:
                    for wl in textwrap.wrap(ln, width=20) or [""]:
                        if y + 18 > h - 24:
                            break
                        draw.text((10, y), wl, fill=dark, font=fb)
                        y += 18

        if details:
            draw.line([(8, h - 34), (w - 8, h - 34)], fill=dark, width=1)
            cols = min(2, len(details))
            col_w = w // cols
            fd = _load_font(13, bold=False)
            for idx, item in enumerate(details[:2]):
                d_icon = item.get("icon", "") if isinstance(item, dict) else ""
                d_text = str(item.get("text", "") if isinstance(item, dict) else item)
                dx = idx * col_w + 8
                if d_icon and draw_icon(draw, d_icon, dx, h - 26, 16, fg=dark, bg=light):
                    dx += 20
                draw.text((dx, h - 24), d_text[:10], fill=dark, font=fd)
        elif footer:
            draw.line([(8, h - 28), (w - 8, h - 28)], fill=dark, width=1)
            ff = _load_font(13, bold=False)
            _draw_centered(draw, w // 2, h - 22, footer[:22], ff, dark)
    else:
        # Landscape: Left dark hero panel (width 114 px), right light panel (150 px)
        split_x = 114
        draw.rectangle([0, 0, split_x, h], fill=dark)
        if title:
            title_lines = textwrap.wrap(title.upper(), width=10)[:2]
            ft = _load_font(14, bold=True)
            ty = 10
            for tl in title_lines:
                _draw_centered(draw, split_x // 2, ty, tl, ft, light)
                ty += 17
        if has_icon:
            draw_icon(draw, icon, (split_x - 56) // 2, 56, 56, fg=light, bg=dark)
        if subtitle:
            fs = _fit_font(draw, subtitle, split_x - 12, 15, 11, bold=False)
            _draw_centered(draw, split_x // 2, h - 30, subtitle, fs, light)

        # Right light panel
        rx = split_x + 10
        rw = w - rx - 8
        y = 14
        if body:
            lines = body.splitlines()
            if len(lines) == 1 and len(lines[0]) <= 10:
                fb = _fit_font(draw, lines[0], rw, 34, 18, bold=True)
                draw.text((rx, y), lines[0], fill=dark, font=fb)
                y += 46
            else:
                fb = _load_font(15, bold=False)
                for ln in lines:
                    for wl in textwrap.wrap(ln, width=16) or [""]:
                        if y + 19 > h - 26:
                            break
                        draw.text((rx, y), wl, fill=dark, font=fb)
                        y += 19

        if details:
            fd = _load_font(15, bold=False)
            dy = max(y + 4, 72)
            for item in details[:3]:
                if dy + 24 > h - 4:
                    break
                draw.line([(rx, dy - 4), (w - 8, dy - 4)], fill=dark, width=1)
                d_icon = item.get("icon", "") if isinstance(item, dict) else ""
                d_text = str(item.get("text", "") if isinstance(item, dict) else item)
                tx = rx
                if d_icon and draw_icon(draw, d_icon, tx, dy + 2, 18, fg=dark, bg=light):
                    tx += 24
                draw.text((tx, dy + 2), d_text[:14], fill=dark, font=fd)
                dy += 30
        elif footer:
            draw.line([(rx, h - 28), (w - 8, h - 28)], fill=dark, width=1)
            ff = _load_font(13, bold=False)
            draw.text((rx, h - 22), footer[:18], fill=dark, font=ff)

    return _finalize_canvas(img, portrait)


def _render_list_card(
    title: str,
    subtitle: str,
    body: str,
    footer: str,
    icon: str,
    invert: bool,
    portrait: bool,
) -> bytes:
    """Render an agenda / to-do list card (header with icon/title + bulleted items)."""
    w, h = (EPD_HEIGHT, EPD_WIDTH) if portrait else (EPD_WIDTH, EPD_HEIGHT)
    bg = 0 if invert else 255
    fg = 255 if invert else 0
    img = Image.new("L", (w, h), bg)
    draw = ImageDraw.Draw(img)

    # Top header
    hx = 10
    if normalize_icon_name(icon):
        draw_icon(draw, icon, hx, 8, 30, fg=fg, bg=bg)
        hx += 38
    if title:
        ft = _fit_font(draw, title, w - hx - 8, 22, 14, bold=True)
        draw.text((hx, 6), title, fill=fg, font=ft)
    if subtitle:
        fs = _load_font(13, bold=False)
        draw.text((hx, 30), subtitle[:26], fill=fg, font=fs)

    y = 48
    draw.line([(8, y), (w - 8, y)], fill=fg, width=2)
    y += 8

    # Bullet items from body lines
    fi = _load_font(15, bold=False)
    max_y = h - (24 if footer else 6)
    max_chars = 20 if portrait else 30
    for raw_line in body.splitlines():
        item = raw_line.strip().lstrip("-*• ")
        if not item:
            continue
        if y + 20 > max_y:
            break
        # Small bullet dot
        draw.ellipse([10, y + 6, 15, y + 11], fill=fg)
        draw.text((22, y), item[:max_chars], fill=fg, font=fi)
        y += 22

    if footer:
        draw.line([(8, h - 24), (w - 8, h - 24)], fill=fg, width=1)
        ff = _load_font(12, bold=False)
        draw.text((10, h - 19), footer[:34], fill=fg, font=ff)

    return _finalize_canvas(img, portrait)


def render_text_card(
    title: str = "",
    body: str = "",
    footer: str = "",
    invert: bool = False,
    *,
    icon: str = "",
    subtitle: str = "",
    layout: str = "classic",
    orientation: str = "landscape",
    details: list[dict[str, Any] | str] | None = None,
) -> bytes:
    """Render a 264x176 (or portrait 176x264) Displio card."""
    portrait = orientation == "portrait"
    layout_clean = (layout or "classic").strip().lower()

    if layout_clean == "split":
        return _render_split_card(
            title=title,
            body=body,
            subtitle=subtitle,
            footer=footer,
            icon=icon,
            details=details,
            invert=invert,
            portrait=portrait,
        )
    if layout_clean == "list":
        return _render_list_card(
            title=title,
            subtitle=subtitle,
            body=body,
            footer=footer,
            icon=icon,
            invert=invert,
            portrait=portrait,
        )

    # Classic layout (with optional dark header bar & icon)
    w, h = (EPD_HEIGHT, EPD_WIDTH) if portrait else (EPD_WIDTH, EPD_HEIGHT)
    bg = 0 if invert else 255
    fg = 255 if invert else 0
    img = Image.new("L", (w, h), bg)
    draw = ImageDraw.Draw(img)

    y = 8
    margin_x = 10

    if title:
        # Dark header strip like the Displio "Recipe of the Day" card
        draw.rectangle([0, 0, w, 34], fill=fg)
        tx = margin_x
        if normalize_icon_name(icon):
            draw_icon(draw, icon, tx, 5, 24, fg=bg, bg=fg)
            tx += 30
        ft = _fit_font(draw, title, w - tx - 8, 20, 13, bold=True)
        draw.text((tx, 6), title, fill=bg, font=ft)
        y = 42
    elif normalize_icon_name(icon):
        draw_icon(draw, icon, margin_x, y, 36, fg=fg, bg=bg)
        y += 42

    if body:
        lines_in = body.splitlines()
        if len(lines_in) == 1 and len(lines_in[0]) <= 12:
            fb = _fit_font(draw, lines_in[0], w - 2 * margin_x, 38, 18, bold=True)
            wrapped = lines_in
            line_h = 44
        elif len(lines_in) <= 2 and max((len(ln) for ln in lines_in), default=0) <= 18:
            fb = _load_font(22, bold=True)
            wrapped = lines_in
            line_h = 28
        else:
            fb = _load_font(15, bold=False)
            wrap_w = 19 if portrait else 29
            wrapped = []
            for ln in lines_in:
                wrapped.extend(textwrap.wrap(ln, width=wrap_w) or [""])
            line_h = 19

        max_y = h - (28 if footer else 8)
        for ln in wrapped:
            if y + line_h > max_y:
                break
            draw.text((margin_x, y), ln, fill=fg, font=fb)
            y += line_h

    if footer:
        draw.rectangle([0, h - 24, w, h], fill=fg)
        ff = _load_font(13, bold=False)
        _draw_centered(draw, w // 2, h - 20, footer[:36], ff, bg)

    return _finalize_canvas(img, portrait)


def render_grid_card(
    tiles: list[dict[str, Any]],
    orientation: str = "landscape",
) -> bytes:
    """Render the iconic Displio 2x2 dashboard grid (up to 4 tiles)."""
    portrait = orientation == "portrait"
    w, h = (EPD_HEIGHT, EPD_WIDTH) if portrait else (EPD_WIDTH, EPD_HEIGHT)
    img = Image.new("L", (w, h), 255)
    draw = ImageDraw.Draw(img)

    half_w = w // 2
    half_h = h // 2

    for idx, tile in enumerate(tiles[:4]):
        col = idx % 2
        row = idx // 2
        x0 = col * half_w
        y0 = row * half_h
        x1 = w if col == 1 else half_w
        y1 = h if row == 1 else half_h
        tw = x1 - x0
        th = y1 - y0

        inv = bool(tile.get("invert", False))
        t_bg = 0 if inv else 255
        t_fg = 255 if inv else 0
        draw.rectangle([x0, y0, x1, y1], fill=t_bg)

        title = str(tile.get("title", "")).upper()
        value = str(tile.get("value", ""))
        subtitle = str(tile.get("subtitle", ""))
        icon = str(tile.get("icon", ""))
        has_icon = bool(normalize_icon_name(icon))

        # Top title
        if title:
            ft = _fit_font(draw, title, tw - 10, 12, 10, bold=True)
            _draw_centered(draw, x0 + tw // 2, y0 + 5, title, ft, t_fg)

        # Middle: icon + big value
        mid_y = y0 + (24 if title else 12)
        if has_icon and value:
            draw_icon(draw, icon, x0 + 6, mid_y + 2, 26, fg=t_fg, bg=t_bg)
            fv = _fit_font(draw, value, tw - 40, 26, 13, bold=True)
            draw.text((x0 + 36, mid_y + 4), value, fill=t_fg, font=fv)
        elif has_icon:
            draw_icon(draw, icon, x0 + (tw - 36) // 2, mid_y, 36, fg=t_fg, bg=t_bg)
        elif value:
            fv = _fit_font(draw, value, tw - 12, 28, 14, bold=True)
            _draw_centered(draw, x0 + tw // 2, mid_y + 4, value, fv, t_fg)

        # Bottom subtitle
        if subtitle:
            fs = _fit_font(draw, subtitle, tw - 10, 13, 10, bold=False)
            _draw_centered(draw, x0 + tw // 2, y0 + th - 19, subtitle, fs, t_fg)

    # Crisp 2px cross dividers
    draw.line([(half_w, 0), (half_w, h)], fill=0, width=2)
    draw.line([(0, half_h), (w, half_h)], fill=0, width=2)

    return _finalize_canvas(img, portrait)
