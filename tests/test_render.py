"""Unit tests for the 264x176 1-bpp E-Ink framebuffer renderer and vector icons."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

from PIL import Image, ImageDraw

# Load const.py, icons.py, and render.py directly without requiring homeassistant installed
_COMP_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "displio_rebirth"
_pkg = types.ModuleType("custom_components.displio_rebirth")
_pkg.__path__ = [str(_COMP_DIR)]
sys.modules.setdefault("custom_components", types.ModuleType("custom_components"))
sys.modules["custom_components.displio_rebirth"] = _pkg


def _load_submodule(name: str):
    spec = importlib.util.spec_from_file_location(
        f"custom_components.displio_rebirth.{name}", _COMP_DIR / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules[f"custom_components.displio_rebirth.{name}"] = mod
    spec.loader.exec_module(mod)
    return mod


_load_submodule("const")
icons = _load_submodule("icons")
render = _load_submodule("render")


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
    """Classic text card with icon must produce exactly 5,808 bytes with visible black pixels."""
    fb = render.render_text_card(
        title="Living Room",
        body="22.4 °C",
        footer="Humidity 48%",
        icon="thermometer",
    )
    assert len(fb) == 5808
    ink_bits = sum((b).bit_count() for b in fb)
    assert 200 < ink_bits < (264 * 176) // 2


def test_render_text_card_invert() -> None:
    """Inverted card should have a predominantly black background."""
    fb = render.render_text_card(title="ALERT", body="Door open", invert=True)
    assert len(fb) == 5808
    ink_bits = sum((b).bit_count() for b in fb)
    assert ink_bits > (264 * 176) // 2


def test_render_split_card_landscape_and_portrait() -> None:
    """Split hero card renders cleanly in both landscape and portrait orientations."""
    for orient in ("landscape", "portrait"):
        fb = render.render_text_card(
            title="PARIS",
            subtitle="Cloudy",
            body="21.5°C",
            icon="mdi:weather-partly-cloudy",
            layout="split",
            orientation=orient,
            details=[
                {"icon": "droplet", "text": "48%"},
                {"icon": "wind", "text": "12 km/h"},
            ],
        )
        assert len(fb) == 5808
        ink_bits = sum((b).bit_count() for b in fb)
        assert 5000 < ink_bits < 38000


def test_render_list_card_portrait() -> None:
    """List/agenda card renders cleanly in portrait orientation."""
    fb = render.render_text_card(
        title="Friday 13",
        subtitle="August",
        body="Dinner at mom's\nCall John\nPick up keys",
        icon="calendar",
        layout="list",
        orientation="portrait",
    )
    assert len(fb) == 5808
    ink_bits = sum((b).bit_count() for b in fb)
    assert 500 < ink_bits < (264 * 176) // 2


def test_render_grid_card_2x2() -> None:
    """2x2 dashboard grid renders 4 tiles with crisp dividers."""
    fb = render.render_grid_card(
        tiles=[
            {"title": "TEMP", "icon": "thermometer", "value": "21.5°C", "subtitle": "48% RH"},
            {"title": "WEATHER", "icon": "sun", "value": "22°C", "subtitle": "Sunny"},
            {"title": "MAIL", "icon": "mail", "value": "3", "subtitle": "Unread"},
            {"title": "ALERT", "icon": "bell", "value": "OK", "invert": True},
        ],
        orientation="landscape",
    )
    assert len(fb) == 5808
    ink_bits = sum((b).bit_count() for b in fb)
    assert 5000 < ink_bits < 35000


def test_all_vector_icons_draw_cleanly() -> None:
    """Every documented vector icon and mdi alias draws pixels without error."""
    sample = [
        "sun", "cloud", "partly_cloudy", "rain", "snow", "storm", "wind", "moon",
        "fog", "thermometer", "droplet", "mail", "calendar", "clock", "home",
        "light", "bolt", "power", "battery", "wifi", "lock", "unlock", "door",
        "window", "bell", "warning", "check", "cross", "list", "trash",
        "arrow_up", "arrow_down", "mdi:weather-sunny", "mdi:email",
    ]
    for name in sample:
        img = Image.new("L", (48, 48), 255)
        draw = ImageDraw.Draw(img)
        assert icons.draw_icon(draw, name, 4, 4, 40, fg=0, bg=255) is True
        assert any(px == 0 for px in img.getdata()), f"Icon {name} drew no pixels"
