"""Unit tests for the 264x176 1-bpp E-Ink framebuffer renderer."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import types

from PIL import Image

# Load const.py and render.py directly without requiring homeassistant installed
_COMP_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "displio_rebirth"
_pkg = types.ModuleType("custom_components.displio_rebirth")
_pkg.__path__ = [str(_COMP_DIR)]
sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
sys.modules["custom_components.displio_rebirth"] = _pkg

_spec_const = importlib.util.spec_from_file_location(
    "custom_components.displio_rebirth.const", _COMP_DIR / "const.py"
)
_mod_const = importlib.util.module_from_spec(_spec_const)
sys.modules["custom_components.displio_rebirth.const"] = _mod_const
_spec_const.loader.exec_module(_mod_const)

_spec_render = importlib.util.spec_from_file_location(
    "custom_components.displio_rebirth.render", _COMP_DIR / "render.py"
)
render = importlib.util.module_from_spec(_spec_render)
sys.modules["custom_components.displio_rebirth.render"] = render
_spec_render.loader.exec_module(render)


def test_white_image_is_all_zeros() -> None:
    """White background must encode to 0x00 bytes (0 = white on Displio EPD)."""
    img = Image.new("L", (264, 176), 255)
    fb = render.image_to_epd_bytes(img, dither=False)
    assert len(fb) == 5808
    assert fb == bytes([0x00] * 5808)


def test_black_image_is_all_ones() -> None:
    """Black ink must encode to 0xFF bytes (1 = black on Displio EPD)."""
    img = Image.new("L", (264, 176), 0)
    fb = render.image_to_epd_bytes(img, dither=False)
    assert len(fb) == 5808
    assert fb == bytes([0xFF] * 5808)


def test_msb_first_top_left_pixel() -> None:
    """Top-left black pixel (0, 0) must set bit 7 (0x80) of byte 0."""
    img = Image.new("L", (264, 176), 255)
    img.putpixel((0, 0), 0)
    fb = render.image_to_epd_bytes(img, dither=False)
    assert fb[0] == 0x80
    assert fb[1:] == bytes([0x00] * 5807)


def test_render_text_card_produces_non_empty_ink() -> None:
    """Text card must produce exactly 5,808 bytes with visible black pixels."""
    fb = render.render_text_card(
        title="Living Room",
        body="22.4 °C",
        footer="Humidity 48%",
    )
    assert len(fb) == 5808
    ink_bits = sum(bin(b).count("1") for b in fb)
    assert 200 < ink_bits < (264 * 176) // 2


def test_render_text_card_invert() -> None:
    """Inverted card should have a predominantly black background."""
    fb = render.render_text_card(title="ALERT", body="Door open", invert=True)
    assert len(fb) == 5808
    ink_bits = sum(bin(b).count("1") for b in fb)
    assert ink_bits > (264 * 176) // 2
