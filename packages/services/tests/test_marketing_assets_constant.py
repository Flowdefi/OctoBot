#  Drakkar-Software OctoBot-Services
#  Copyright (c) Drakkar-Software, All rights reserved.

import octobot_services.constants as constants


def test_marketing_assets_service_key():
    assert constants.CONFIG_MARKETING_ASSETS == "marketing-assets"
    assert constants.CONFIG_MARKETING_ASSETS_OUTPUT_DIR == "output-dir"
