#  Drakkar-Software OctoBot-Tentacles
#  Copyright (c) Drakkar-Software, All rights reserved.

from pathlib import Path

try:
    from tentacles.Services.Services_bases.marketing_assets_service import renderer
except ImportError:
    import renderer  # type: ignore[no-redef]


def test_price_card_dimensions_and_png(tmp_path: Path):
    image = renderer.render_price_card(
        renderer.PriceCard(symbol="BTC/USDT", price="64,210", change_pct=1.84, exchange="MEXC"),
        fmt="square",
    )
    assert image.size == renderer.FORMATS["square"]
    path = renderer.save_image(image, tmp_path / "btc.png")
    assert path.is_file()
    assert path.stat().st_size > 1000


def test_negative_change_and_unknown_format():
    image = renderer.render_price_card(
        renderer.PriceCard(symbol="ETH/USDT", price="2,410", change_pct=-0.72, exchange="BingX"),
        fmt="landscape",
    )
    assert image.size == renderer.FORMATS["landscape"]
    try:
        renderer.canvas("billboard")
        raise AssertionError("expected UnknownFormatError")
    except renderer.UnknownFormatError:
        pass


def test_exchange_and_strategy_cards():
    exchange = renderer.render_exchange_card(
        renderer.ExchangeCard(
            exchange="BloFin",
            tagline="Perps with a quiet interface.",
            pairs=("BTC/USDT", "ETH/USDT"),
        )
    )
    strategy = renderer.render_strategy_card(
        renderer.StrategyCard(title="Grid", subtitle="Extract value from range, not from prediction.")
    )
    assert exchange.size == renderer.FORMATS["landscape"]
    assert strategy.size == renderer.FORMATS["story"]
