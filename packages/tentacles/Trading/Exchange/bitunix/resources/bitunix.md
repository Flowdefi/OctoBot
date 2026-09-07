Bitunix is a RestExchange adaptation for Bitunix using the REST API.

Bitunix is not yet in upstream CCXT. OctoBot ships a local public-market adapter so simulator and market-data flows work, and signed private requests use Bitunix's double-SHA256 scheme when API keys are configured.

## OctoBot support

| Spot trading | ✅  |
| :----------- | :-- |
| Futures      | ✅  |
| Simulation   | ✅  |
| REST         | ✅  |
| Websocket    | ❌  |
| Testnet      | ❌  |

# Bitunix account setup

## Create an account

- Fill <a href="https://www.bitunix.com/register" rel="nofollow">this Bitunix</a> registration form
- Create an API key and secret (no withdrawal permission)
- Add both values to your OctoBot exchange configuration
