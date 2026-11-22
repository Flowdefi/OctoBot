#  Drakkar-Software OctoBot-Tentacles
#  Copyright (c) Drakkar-Software, All rights reserved.

import json
from pathlib import Path


_PROFILE = Path(__file__).resolve().parents[1]
_TENTACLES = _PROFILE.parents[1]


def test_featured_cex_profile_lists_target_venues():
    profile = json.loads((_PROFILE / "profile.json").read_text())
    exchanges = profile["config"]["exchanges"]
    assert set(exchanges) == {"mexc", "bingx", "blofin", "bitunix", "bydfi"}
    assert all(exchanges[name]["enabled"] for name in exchanges)
    assert profile["config"]["trader-simulator"]["enabled"] is True
    assert profile["config"]["trader"]["enabled"] is False
    assert profile["config"]["services"]["marketing-assets"]["enabled"] is True


def test_featured_cex_activates_exchange_and_marketing_tentacles():
    tentacles_config = json.loads((_PROFILE / "tentacles_config.json").read_text())
    trading = tentacles_config["tentacle_activation"]["Trading"]
    services = tentacles_config["tentacle_activation"]["Services"]
    assert trading["MEXC"] is True
    assert trading["Bingx"] is True
    assert trading["Blofin"] is True
    assert trading["Bitunix"] is True
    assert trading["Bydfi"] is True
    assert services["MarketingAssetsService"] is True


def test_featured_exchange_tentacles_exist():
    exchange_root = _TENTACLES / "Trading" / "Exchange"
    for name in ("mexc", "bingx", "blofin", "bitunix", "bydfi"):
        assert (exchange_root / name / "metadata.json").is_file()
    assert (exchange_root / "blofin_websocket_feed" / "metadata.json").is_file()
    assert (exchange_root / "bydfi_websocket_feed" / "metadata.json").is_file()
    assert (
        _TENTACLES / "Services" / "Services_bases" / "marketing_assets_service" / "renderer.py"
    ).is_file()

