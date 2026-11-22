#  Drakkar-Software OctoBot-Tentacles
#  Copyright (c) Drakkar-Software, All rights reserved.
"""Generate a small set of modern/minimal crypto marketing cards."""
from __future__ import annotations

import argparse
from pathlib import Path

try:
    from tentacles.Services.Services_bases.marketing_assets_service import renderer
except ImportError:
    import renderer  # type: ignore[no-redef]


FEATURED = (
    ("MEXC", "Deep spot liquidity without the noise."),
    ("BingX", "Copy-friendly markets, quiet execution."),
    ("BloFin", "Perps with a restrained interface."),
    ("Bitunix", "A compact venue for majors."),
    ("BYDFi", "Spot and perps, same visual language."),
)


def generate_sample_kit(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    written.append(renderer.save_image(
        renderer.render_price_card(renderer.PriceCard(
            symbol="BTC/USDT",
            price="64,210",
            change_pct=1.84,
            exchange="MEXC",
        )),
        output_dir / "mexc-btc-usdt-square.png",
    ))
    for exchange, tagline in FEATURED:
        slug = exchange.lower()
        written.append(renderer.save_image(
            renderer.render_exchange_card(renderer.ExchangeCard(
                exchange=exchange,
                tagline=tagline,
                pairs=("BTC/USDT", "ETH/USDT"),
            )),
            output_dir / f"{slug}-intro-landscape.png",
        ))
    written.append(renderer.save_image(
        renderer.render_strategy_card(renderer.StrategyCard(
            title="Featured CEX",
            subtitle="Five venues. One paper portfolio. No withdrawal keys.",
        )),
        output_dir / "featured-cex-story.png",
    ))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="user/marketing_assets",
        help="Directory to write PNG files into",
    )
    args = parser.parse_args(argv)
    paths = generate_sample_kit(Path(args.output))
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
