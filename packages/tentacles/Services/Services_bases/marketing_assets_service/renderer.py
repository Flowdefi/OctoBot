#  Drakkar-Software OctoBot-Tentacles
#  Copyright (c) Drakkar-Software, All rights reserved.
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3.0 of the License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library.
"""Modern, minimal crypto marketing cards.

The visual language is dark, sparse, and typographic: one headline, one
metric, one accent rule. No charts, no logos collage, no stock imagery.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


INK = "#F4F1EA"
MUTED = "#8A8478"
BACKGROUND = "#0B0F14"
SURFACE = "#121821"
ACCENT = "#C8F542"
NEGATIVE = "#FF6B4A"
HAIRLINE = "#2A3038"

FORMATS = {
    "square": (1080, 1080),
    "landscape": (1200, 630),
    "story": (1080, 1920),
}

_FONT_CANDIDATES = (
    "/usr/local/share/fonts/inter/Inter-Regular.ttf",
    "/usr/share/fonts/truetype/inter/Inter-Regular.ttf",
    "/usr/share/fonts/truetype/inter/InterVariable.ttf",
    "/usr/share/fonts/opentype/inter/Inter-Regular.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
)
_FONT_BOLD_CANDIDATES = (
    "/usr/local/share/fonts/inter/Inter-SemiBold.ttf",
    "/usr/local/share/fonts/inter/Inter-Bold.ttf",
    "/usr/share/fonts/truetype/inter/Inter-SemiBold.ttf",
    "/usr/share/fonts/truetype/inter/Inter-Bold.ttf",
    "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
)


class MarketingAssetError(Exception):
    pass


class UnknownFormatError(MarketingAssetError):
    pass


@dataclass(frozen=True)
class PriceCard:
    symbol: str
    price: str
    change_pct: float
    exchange: str = ""
    caption: str = "Live market"


@dataclass(frozen=True)
class ExchangeCard:
    exchange: str
    tagline: str
    pairs: tuple[str, ...] = ()


@dataclass(frozen=True)
class StrategyCard:
    title: str
    subtitle: str
    footnote: str = "Paper trading · no withdrawal keys"


def _first_existing(paths: Iterable[str]) -> str | None:
    extra = os.environ.get("OCTOBOT_MARKETING_FONT")
    extra_bold = os.environ.get("OCTOBOT_MARKETING_FONT_BOLD")
    for path in ((extra, extra_bold) if extra else ()) + tuple(paths):
        if path and Path(path).is_file():
            return path
    return None


def load_font(size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = _FONT_BOLD_CANDIDATES if bold else _FONT_CANDIDATES
    path = _first_existing(candidates)
    if path:
        return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


def _draw_hairline(draw: ImageDraw.ImageDraw, x0: int, x1: int, y: int) -> None:
    draw.line((x0, y, x1, y), fill=HAIRLINE, width=1)


def _draw_accent_rule(draw: ImageDraw.ImageDraw, x: int, y: int, width: int) -> None:
    draw.rectangle((x, y, x + width, y + 3), fill=ACCENT)


def _fit_margin(size: tuple[int, int]) -> int:
    return max(56, min(size) // 12)


def canvas(fmt: str) -> Image.Image:
    if fmt not in FORMATS:
        raise UnknownFormatError(f"Unknown format {fmt!r}. Choose from {sorted(FORMATS)}")
    return Image.new("RGB", FORMATS[fmt], BACKGROUND)


def render_price_card(card: PriceCard, fmt: str = "square") -> Image.Image:
    image = canvas(fmt)
    draw = ImageDraw.Draw(image)
    width, height = image.size
    margin = _fit_margin(image.size)
    change_color = ACCENT if card.change_pct >= 0 else NEGATIVE
    sign = "+" if card.change_pct >= 0 else ""
    change_text = f"{sign}{card.change_pct:.2f}%"

    eyebrow = (card.exchange or "OctoBot").upper()
    draw.text((margin, margin), eyebrow, font=load_font(22), fill=MUTED)
    _draw_accent_rule(draw, margin, margin + 36, 36)
    draw.text((margin, margin + 72), card.symbol, font=load_font(72 if height > 800 else 54, bold=True), fill=INK)

    price_y = height // 2 - (40 if height > 800 else 8)
    draw.text((margin, price_y), card.price, font=load_font(96 if height > 800 else 64, bold=True), fill=INK)
    draw.text((margin, price_y + (120 if height > 800 else 84)), change_text, font=load_font(36, bold=True), fill=change_color)

    _draw_hairline(draw, margin, width - margin, height - margin - 48)
    draw.text((margin, height - margin - 36), card.caption, font=load_font(20), fill=MUTED)
    return image


def render_exchange_card(card: ExchangeCard, fmt: str = "landscape") -> Image.Image:
    image = canvas(fmt)
    draw = ImageDraw.Draw(image)
    width, height = image.size
    margin = _fit_margin(image.size)

    draw.rectangle((0, 0, 8, height), fill=ACCENT)
    draw.text((margin, margin), "EXCHANGE", font=load_font(20), fill=MUTED)
    draw.text((margin, margin + 40), card.exchange, font=load_font(64 if width > 1000 else 48, bold=True), fill=INK)
    draw.text((margin, margin + 130), card.tagline, font=load_font(28), fill=MUTED)

    if card.pairs:
        y = height - margin - 36
        draw.text((margin, y), "  ·  ".join(card.pairs), font=load_font(20), fill=INK)
        _draw_hairline(draw, margin, width - margin, y - 24)
    return image


def render_strategy_card(card: StrategyCard, fmt: str = "story") -> Image.Image:
    image = canvas(fmt)
    draw = ImageDraw.Draw(image)
    width, height = image.size
    margin = _fit_margin(image.size)

    draw.text((margin, margin), "STRATEGY", font=load_font(20), fill=MUTED)
    _draw_accent_rule(draw, margin, margin + 48, 36)
    title_y = height // 3
    draw.text((margin, title_y), card.title, font=load_font(64, bold=True), fill=INK)
    draw.text((margin, title_y + 96), card.subtitle, font=load_font(28), fill=MUTED)
    _draw_hairline(draw, margin, width - margin, height - margin - 64)
    draw.text((margin, height - margin - 40), card.footnote, font=load_font(20), fill=MUTED)
    return image


def save_image(image: Image.Image, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)
    return destination
