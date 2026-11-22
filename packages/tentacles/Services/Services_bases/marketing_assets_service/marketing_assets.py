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
from pathlib import Path

import octobot_commons.constants as commons_constants
import octobot_commons.logging as bot_logging
import octobot_services.constants as services_constants
import octobot_services.services as services

try:
    from tentacles.Services.Services_bases.marketing_assets_service import renderer
except ImportError:
    import renderer  # type: ignore[no-redef]


class MarketingAssetsService(services.AbstractService):
    BACKTESTING_ENABLED = True

    def __init__(self):
        super().__init__()
        self.output_dir = Path("user") / "marketing_assets"

    @staticmethod
    def is_setup_correctly(config):
        return True

    @staticmethod
    def get_is_enabled(config):
        try:
            return config[services_constants.CONFIG_CATEGORY_SERVICES][
                services_constants.CONFIG_MARKETING_ASSETS
            ][commons_constants.CONFIG_ENABLED_OPTION]
        except KeyError:
            return False

    @staticmethod
    def get_should_warn():
        return False

    def has_required_configuration(self):
        return self.get_is_enabled(self.config)

    def get_endpoint(self):
        return str(self.output_dir)

    def get_type(self):
        return services_constants.CONFIG_MARKETING_ASSETS

    async def prepare(self):
        service_config = self.config.get(services_constants.CONFIG_CATEGORY_SERVICES, {}).get(
            services_constants.CONFIG_MARKETING_ASSETS, {}
        )
        configured_dir = service_config.get(services_constants.CONFIG_MARKETING_ASSETS_OUTPUT_DIR)
        if configured_dir:
            self.output_dir = Path(configured_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self.logger or bot_logging.get_logger(self.get_name())

    def get_fields_description(self):
        return {
            services_constants.CONFIG_MARKETING_ASSETS_OUTPUT_DIR: (
                "Directory for generated PNG cards (dark, typographic, one metric)."
            ),
        }

    def get_default_value(self):
        return {
            services_constants.CONFIG_MARKETING_ASSETS_OUTPUT_DIR: str(self.output_dir),
        }

    def get_required_config(self):
        return []

    def get_successful_startup_message(self):
        return f"Marketing assets will be written to {self.output_dir}", True

    def create_price_card(
        self,
        symbol: str,
        price: str,
        change_pct: float,
        exchange: str = "",
        fmt: str = "square",
        filename: str | None = None,
    ) -> Path:
        image = renderer.render_price_card(
            renderer.PriceCard(symbol=symbol, price=price, change_pct=change_pct, exchange=exchange),
            fmt=fmt,
        )
        destination = self.output_dir / (filename or f"{_slug(exchange or 'market')}_{_slug(symbol)}_{fmt}.png")
        return renderer.save_image(image, destination)

    def create_exchange_card(
        self,
        exchange: str,
        tagline: str,
        pairs: tuple[str, ...] = (),
        fmt: str = "landscape",
        filename: str | None = None,
    ) -> Path:
        image = renderer.render_exchange_card(
            renderer.ExchangeCard(exchange=exchange, tagline=tagline, pairs=pairs),
            fmt=fmt,
        )
        destination = self.output_dir / (filename or f"{_slug(exchange)}_intro_{fmt}.png")
        return renderer.save_image(image, destination)

    def create_strategy_card(
        self,
        title: str,
        subtitle: str,
        fmt: str = "story",
        filename: str | None = None,
    ) -> Path:
        image = renderer.render_strategy_card(
            renderer.StrategyCard(title=title, subtitle=subtitle),
            fmt=fmt,
        )
        destination = self.output_dir / (filename or f"{_slug(title)}_{fmt}.png")
        return renderer.save_image(image, destination)


def _slug(value: str) -> str:
    return "".join(char.lower() if char.isalnum() else "-" for char in value).strip("-")
