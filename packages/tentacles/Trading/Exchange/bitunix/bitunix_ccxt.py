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
"""
Local CCXT adapter for Bitunix.

Bitunix is not in upstream CCXT yet. This class covers public market data and
signed private requests so OctoBot can paper-trade and attach API keys when
the official CCXT client is unavailable.
"""
import hashlib
import json
import time
import uuid

import ccxt.async_support as ccxt


class bitunix(ccxt.Exchange):
    def describe(self):
        return self.deep_extend(super().describe(), {
            "id": "bitunix",
            "name": "Bitunix",
            "countries": ["SC"],
            "rateLimit": 100,
            "pro": False,
            "certified": False,
            "version": "v1",
            "has": {
                "CORS": None,
                "spot": True,
                "margin": False,
                "swap": True,
                "future": True,
                "option": False,
                "fetchMarkets": True,
                "fetchTicker": True,
                "fetchTickers": True,
                "fetchOHLCV": True,
                "fetchOrderBook": True,
                "fetchTrades": True,
                "fetchBalance": True,
                "createOrder": True,
                "cancelOrder": True,
                "fetchOpenOrders": True,
            },
            "timeframes": {
                "1m": "1m",
                "3m": "3m",
                "5m": "5m",
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "2h": "2h",
                "4h": "4h",
                "6h": "6h",
                "8h": "8h",
                "12h": "12h",
                "1d": "1d",
                "3d": "3d",
                "1w": "1w",
                "1M": "1M",
            },
            "urls": {
                "logo": "https://www.bitunix.com/favicon.ico",
                "api": {
                    "spot": "https://openapi.bitunix.com",
                    "future": "https://fapi.bitunix.com",
                },
                "www": "https://www.bitunix.com",
                "doc": [
                    "https://openapidoc.bitunix.com/",
                    "https://www.bitunix.com/api-docs/futures/common/introduction.html",
                ],
            },
            "api": {
                "spot": {
                    "public": {
                        "get": {
                            "api/v1/spot/market/tickers": 1,
                            "api/v1/spot/market/depth": 1,
                            "api/v1/spot/market/klines": 1,
                            "api/v1/spot/market/fills": 1,
                            "api/spot/v1/common/coin_pairs": 1,
                        },
                    },
                    "private": {
                        "get": {
                            "api/v1/spot/account/balance": 1,
                            "api/v1/spot/orders/pending": 1,
                        },
                        "post": {
                            "api/v1/spot/order/place": 1,
                            "api/v1/spot/order/cancel": 1,
                        },
                    },
                },
                "future": {
                    "public": {
                        "get": {
                            "api/v1/futures/market/trading_pairs": 1,
                            "api/v1/futures/market/tickers": 1,
                            "api/v1/futures/market/kline": 1,
                            "api/v1/futures/market/depth": 1,
                            "api/v1/futures/market/trades": 1,
                        },
                    },
                    "private": {
                        "get": {
                            "api/v1/futures/account": 1,
                            "api/v1/futures/order/pending": 1,
                        },
                        "post": {
                            "api/v1/futures/order/place": 1,
                            "api/v1/futures/order/cancel": 1,
                        },
                    },
                },
            },
            "precisionMode": ccxt.TICK_SIZE,
            "exceptions": {},
        })

    def sign(self, path, api="public", method="GET", params=None, headers=None, body=None):
        params = params or {}
        section, access = api if isinstance(api, (list, tuple)) else self._split_api(api)
        base = self.urls["api"][section]
        query = self.omit(params, self.extract_params(path))
        url = f"{base}/{path}"
        query_string = ""
        body_string = ""
        if method == "GET":
            if query:
                query_string = self.urlencode(self.keysort(query))
                url = f"{url}?{query_string}"
        elif query:
            body_string = json.dumps(query, separators=(",", ":"), ensure_ascii=False)
            body = body_string
        headers = headers or {}
        headers["Content-Type"] = "application/json"
        if access == "private":
            self.check_required_credentials()
            nonce = uuid.uuid4().hex
            timestamp = str(int(time.time() * 1000))
            digest_source = f"{nonce}{timestamp}{self.apiKey}{query_string}{body_string}"
            digest = hashlib.sha256(digest_source.encode("utf-8")).hexdigest()
            sign = hashlib.sha256(f"{digest}{self.secret}".encode("utf-8")).hexdigest()
            headers.update({
                "api-key": self.apiKey,
                "nonce": nonce,
                "timestamp": timestamp,
                "sign": sign,
            })
        return {"url": url, "method": method, "body": body, "headers": headers}

    def _split_api(self, api):
        if api in ("spot", "future"):
            return api, "public"
        if api in ("public", "private"):
            default_type = self.safe_string(self.options, "defaultType", "spot")
            return default_type if default_type in ("spot", "future") else "spot", api
        return "spot", "public"

    def _unwrap(self, response):
        if isinstance(response, dict) and "data" in response:
            return response["data"]
        return response

    async def fetch_markets(self, params=None):
        params = params or {}
        markets = []
        default_type = self.safe_string(self.options, "defaultType", "spot")
        if default_type != "future":
            try:
                raw = self._unwrap(await self.spotPublicGetApiSpotV1CommonCoinPairs(params))
                markets.extend(self._parse_spot_markets(raw))
            except Exception:
                raw = self._unwrap(await self.spotPublicGetApiV1SpotMarketTickers(params))
                markets.extend(self._parse_spot_markets_from_tickers(raw))
        if default_type in ("future", "swap"):
            raw = self._unwrap(await self.futurePublicGetApiV1FuturesMarketTradingPairs(params))
            markets.extend(self._parse_future_markets(raw))
        return markets

    def _as_list(self, raw):
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict):
            for key in ("list", "pairs", "symbols", "tickers"):
                if isinstance(raw.get(key), list):
                    return raw[key]
        return []

    def _parse_spot_markets(self, raw):
        result = []
        for market in self._as_list(raw):
            base = self.safe_string_2(market, "base", "baseCoin")
            quote = self.safe_string_2(market, "quote", "quoteCoin")
            symbol = self.safe_string(market, "symbol") or (f"{base}/{quote}" if base and quote else None)
            if not base or not quote:
                continue
            result.append({
                "id": symbol.replace("/", "") if symbol else f"{base}{quote}",
                "symbol": f"{base}/{quote}",
                "base": base,
                "quote": quote,
                "settle": None,
                "baseId": base,
                "quoteId": quote,
                "settleId": None,
                "type": "spot",
                "spot": True,
                "margin": False,
                "swap": False,
                "future": False,
                "option": False,
                "active": True,
                "contract": False,
                "precision": {
                    "amount": self.safe_number_2(market, "basePrecision", "amountPrecision", 1e-8),
                    "price": self.safe_number_2(market, "quotePrecision", "pricePrecision", 1e-8),
                },
                "limits": {
                    "amount": {"min": self.safe_number(market, "minAmount"), "max": None},
                    "price": {"min": None, "max": None},
                    "cost": {"min": self.safe_number(market, "minCost"), "max": None},
                },
                "info": market,
            })
        return result

    def _parse_spot_markets_from_tickers(self, raw):
        result = []
        for ticker in self._as_list(raw):
            market_id = self.safe_string(ticker, "symbol")
            if not market_id:
                continue
            base, quote = self._split_symbol(market_id)
            result.append({
                "id": market_id,
                "symbol": f"{base}/{quote}",
                "base": base,
                "quote": quote,
                "type": "spot",
                "spot": True,
                "swap": False,
                "future": False,
                "active": True,
                "contract": False,
                "precision": {"amount": 1e-8, "price": 1e-8},
                "limits": {"amount": {"min": None, "max": None}, "price": {"min": None, "max": None}, "cost": {"min": None, "max": None}},
                "info": ticker,
            })
        return result

    def _parse_future_markets(self, raw):
        result = []
        for market in self._as_list(raw):
            market_id = self.safe_string(market, "symbol")
            base = self.safe_string_2(market, "base", "baseCoin")
            quote = self.safe_string_2(market, "quote", "quoteCoin", "USDT")
            if not market_id and base:
                market_id = f"{base}{quote}"
            if not market_id:
                continue
            if not base:
                base, quote = self._split_symbol(market_id)
            result.append({
                "id": market_id,
                "symbol": f"{base}/{quote}:{quote}",
                "base": base,
                "quote": quote,
                "settle": quote,
                "baseId": base,
                "quoteId": quote,
                "settleId": quote,
                "type": "swap",
                "spot": False,
                "swap": True,
                "future": True,
                "contract": True,
                "linear": True,
                "inverse": False,
                "active": True,
                "precision": {"amount": 1e-8, "price": 1e-8},
                "limits": {"amount": {"min": None, "max": None}, "price": {"min": None, "max": None}, "cost": {"min": None, "max": None}},
                "info": market,
            })
        return result

    def _split_symbol(self, market_id: str) -> tuple[str, str]:
        if "/" in market_id:
            base, quote = market_id.split("/", 1)
            return base, quote.split(":")[0]
        for quote in ("USDT", "USDC", "BTC", "ETH", "USD"):
            if market_id.endswith(quote) and len(market_id) > len(quote):
                return market_id[:-len(quote)], quote
        return market_id, "USDT"

    def _to_exchange_symbol(self, symbol: str) -> str:
        return symbol.replace("/", "").split(":")[0]

    async def fetch_ticker(self, symbol, params=None):
        await self.load_markets()
        market = self.market(symbol)
        request = {"symbol": market["id"]}
        if market["spot"]:
            raw = self._unwrap(await self.spotPublicGetApiV1SpotMarketTickers(self.extend(request, params or {})))
        else:
            raw = self._unwrap(await self.futurePublicGetApiV1FuturesMarketTickers(self.extend(request, params or {})))
        ticker = self._as_list(raw)[0] if self._as_list(raw) else raw
        return self._parse_ticker(ticker, market)

    async def fetch_tickers(self, symbols=None, params=None):
        await self.load_markets()
        default_type = self.safe_string(self.options, "defaultType", "spot")
        if default_type in ("future", "swap"):
            raw = self._unwrap(await self.futurePublicGetApiV1FuturesMarketTickers(params or {}))
        else:
            raw = self._unwrap(await self.spotPublicGetApiV1SpotMarketTickers(params or {}))
        result = {}
        for ticker in self._as_list(raw):
            market_id = self.safe_string(ticker, "symbol")
            market = self.safe_market(market_id)
            parsed = self._parse_ticker(ticker, market)
            result[parsed["symbol"]] = parsed
        return self.filter_by_array_tickers(result, "symbol", symbols)

    def _parse_ticker(self, ticker, market=None):
        last = self.safe_number_2(ticker, "last", "close")
        return self.safe_ticker({
            "symbol": market["symbol"] if market else self.safe_string(ticker, "symbol"),
            "timestamp": self.safe_integer(ticker, "ts"),
            "datetime": None,
            "high": self.safe_number_2(ticker, "high", "high24h"),
            "low": self.safe_number_2(ticker, "low", "low24h"),
            "bid": self.safe_number(ticker, "bid"),
            "ask": self.safe_number(ticker, "ask"),
            "last": last,
            "close": last,
            "baseVolume": self.safe_number_2(ticker, "baseVolume", "vol"),
            "quoteVolume": self.safe_number_2(ticker, "quoteVolume", "quoteVol"),
            "info": ticker,
        }, market)

    async def fetch_ohlcv(self, symbol, timeframe="1m", since=None, limit=None, params=None):
        await self.load_markets()
        market = self.market(symbol)
        request = {
            "symbol": market["id"],
            "interval": self.safe_string(self.timeframes, timeframe, timeframe),
        }
        if limit is not None:
            request["limit"] = limit
        if since is not None:
            request["startTime"] = since
        if market["spot"]:
            raw = self._unwrap(await self.spotPublicGetApiV1SpotMarketKlines(self.extend(request, params or {})))
        else:
            raw = self._unwrap(await self.futurePublicGetApiV1FuturesMarketKline(self.extend(request, params or {})))
        candles = self._as_list(raw)
        return [
            [
                self.safe_integer_2(candle, 0, "openTime") if isinstance(candle, dict) else self.safe_integer(candle, 0),
                self.safe_number_2(candle, "open", 1) if isinstance(candle, dict) else self.safe_number(candle, 1),
                self.safe_number_2(candle, "high", 2) if isinstance(candle, dict) else self.safe_number(candle, 2),
                self.safe_number_2(candle, "low", 3) if isinstance(candle, dict) else self.safe_number(candle, 3),
                self.safe_number_2(candle, "close", 4) if isinstance(candle, dict) else self.safe_number(candle, 4),
                self.safe_number_2(candle, "volume", 5) if isinstance(candle, dict) else self.safe_number(candle, 5),
            ]
            for candle in candles
        ]

    async def fetch_order_book(self, symbol, limit=None, params=None):
        await self.load_markets()
        market = self.market(symbol)
        request = {"symbol": market["id"]}
        if limit is not None:
            request["limit"] = limit
        if market["spot"]:
            raw = self._unwrap(await self.spotPublicGetApiV1SpotMarketDepth(self.extend(request, params or {})))
        else:
            raw = self._unwrap(await self.futurePublicGetApiV1FuturesMarketDepth(self.extend(request, params or {})))
        return self.parse_order_book(raw, market["symbol"], None, "bids", "asks")

    async def fetch_trades(self, symbol, since=None, limit=None, params=None):
        await self.load_markets()
        market = self.market(symbol)
        request = {"symbol": market["id"]}
        if limit is not None:
            request["limit"] = limit
        if market["spot"]:
            raw = self._unwrap(await self.spotPublicGetApiV1SpotMarketFills(self.extend(request, params or {})))
        else:
            raw = self._unwrap(await self.futurePublicGetApiV1FuturesMarketTrades(self.extend(request, params or {})))
        return self.parse_trades(self._as_list(raw), market, since, limit)
