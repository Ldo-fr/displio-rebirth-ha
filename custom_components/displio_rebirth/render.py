"""264x176 1-bpp monochrome E-Ink framebuffer renderer using Pillow."""

from __future__ import annotations

import io
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont, ImageOps

from .const import EPD_FB_SIZE, EPD_HEIGHT, EPD_WIDTH

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


def render_text_card(
    title: str = "",
    body: str = "",
    footer: str = "",
    invert: bool = False,
) -> bytes:
    """Render a clean 264x176 monochrome card with optional title, body, and footer."""
    bg = 0 if invert else 255
    fg = 255 if invert else 0
    img = Image.new("L", (EPD_WIDTH, EPD_HEIGHT), bg)
    draw = ImageDraw.Draw(img)

    y = 8
    margin_x = 10

    if title:
        font_title = _load_font(22, bold=True)
        draw.text((margin_x, y), title[:24], fill=fg, font=font_title)
        y += 30
        draw.line([(margin_x, y), (EPD_WIDTH - margin_x, y)], fill=fg, width=2)
        y += 8

    if body:
        lines_in = body.splitlines()
        # Use larger font for short single-line values (e.g. "21.5 °C")
        if len(lines_in) == 1 and len(lines_in[0]) <= 12:
            font_body = _load_font(38, bold=True)
            wrapped = lines_in
            line_h = 44
        elif len(lines_in) <= 2 and max((len(l) for l in lines_in), default=0) <= 18:
            font_body = _load_font(24, bold=True)
            wrapped = lines_in
            line_h = 30
        else:
            font_body = _load_font(16, bold=False)
            wrapped = []
            for ln in lines_in:
                wrapped.extend(textwrap.wrap(ln, width=28) or [""])
            line_h = 20

        max_y = EPD_HEIGHT - (28 if footer else 8)
        for ln in wrapped:
            if y + line_h > max_y:
                break
            draw.text((margin_x, y), ln, fill=fg, font=font_body)
            y += line_h

    if footer:
        font_footer = _load_font(13, bold=False)
        draw.line([(margin_x, EPD_HEIGHT - 24), (EPD_WIDTH - margin_x, EPD_HEIGHT - 24)], fill=fg, width=1)
        draw.text((margin_x, EPD_HEIGHT - 20), footer[:36], fill=fg, font=font_footer)

    return image_to_epd_bytes(img, dither=False, invert=False)
