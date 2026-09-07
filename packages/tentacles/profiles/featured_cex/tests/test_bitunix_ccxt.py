from __future__ import annotations

import importlib.util
from pathlib import Path

_ADAPTER = (
    Path(__file__).resolve().parents[3]
    / "Trading"
    / "Exchange"
    / "bitunix"
    / "bitunix_ccxt.py"
)


def _load_adapter():
    spec = importlib.util.spec_from_file_location("bitunix_ccxt_standalone", _ADAPTER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_bitunix_adapter_file_exists():
    assert _ADAPTER.is_file()


def test_bitunix_describe_has_spot_and_swap_urls():
    module = _load_adapter()
    described = module.bitunix().describe()
    assert described["id"] == "bitunix"
    assert described["has"]["spot"] is True
    assert described["has"]["swap"] is True
    assert described["urls"]["api"]["spot"] == "https://openapi.bitunix.com"
    assert described["urls"]["api"]["future"] == "https://fapi.bitunix.com"


def test_bitunix_split_symbol_defaults_to_usdt():
    module = _load_adapter()
    exchange = module.bitunix()
    assert exchange._split_symbol("BTC/USDT") == ("BTC", "USDT")
    assert exchange._split_symbol("BTCUSDT") == ("BTC", "USDT")
    assert exchange._split_symbol("ETH") == ("ETH", "USDT")


def test_bitunix_sign_uses_nonce_and_sha256_chain():
    module = _load_adapter()
    exchange = module.bitunix(
        {
            "apiKey": "test-key",
            "secret": "test-secret",
        }
    )
    signed = exchange.sign(
        "api/v1/spot/account",
        api="private",
        method="GET",
        params={"walletType": "SPOT"},
        headers=None,
        body=None,
    )
    assert signed["url"].startswith("https://openapi.bitunix.com/api/v1/spot/account")
    assert "walletType=SPOT" in signed["url"]
    assert signed["headers"]["api-key"] == "test-key"
    assert "nonce" in signed["headers"]
    assert "timestamp" in signed["headers"]
    assert "sign" in signed["headers"]
    assert len(signed["headers"]["sign"]) == 64
