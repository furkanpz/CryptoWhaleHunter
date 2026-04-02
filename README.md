# Crypto Whale Hunter

Crypto Whale Hunter is a Binance USD-M futures signal scanner that watches RSI and short-term volume spikes, then delivers matching whale-style alerts to Telegram.

The repository has been refactored into a production-oriented Python service without changing the core trading logic:

- Binance futures OHLCV data
- `1m` timeframe and `1440` candles
- `RSI(7)` thresholds
- `rsi >= 70` produces `long`
- `rsi <= 30` produces `short`
- `600` second cooldown per symbol unless direction flips
- last `10` minute USDT volume must be at least `200000`

## Architecture

The codebase is organized as a Python package:

- `crypto_whale_hunter/config.py`: environment-driven settings and validation
- `crypto_whale_hunter/market_data.py`: Binance OHLCV access
- `crypto_whale_hunter/signals.py`: pure signal decision logic
- `crypto_whale_hunter/repository.py`: SQLite bootstrap and state persistence
- `crypto_whale_hunter/notifier.py`: Telegram signal and status publishing
- `crypto_whale_hunter/service.py`: main scan loop
- `crypto_whale_hunter/status.py`: market status summary generation

Legacy entrypoints are still available:

- `python3 main.py`
- `python3 status_update/status.py`

The recommended interface is:

```bash
python3 -m crypto_whale_hunter run
python3 -m crypto_whale_hunter status
```

## Requirements

- Python `3.9+`
- Telegram bot token(s) and target chat id
- Binance access from your runtime environment

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Optional development tooling:

```bash
pip install -r requirements-dev.txt
```

## Configuration

All runtime configuration is read from environment variables and optional `.env`.

| Variable | Required | Default | Description |
| --- | --- | --- | --- |
| `COINLIST_PATH` | No | `coinlist.csv` | Symbol list file. Empty lines and duplicates are ignored. |
| `DB_PATH` | No | `db/database.db` | SQLite database path. |
| `BINANCE_TIMEFRAME` | No | `1m` | OHLCV timeframe. |
| `BINANCE_LIMIT` | No | `1440` | Number of candles fetched per symbol. |
| `RSI_PERIOD` | No | `7` | RSI period. |
| `RSI_OVERBOUGHT` | No | `70` | Long threshold. |
| `RSI_OVERSOLD` | No | `30` | Short threshold. |
| `RECENT_VOLUME_WINDOW` | No | `10` | Number of recent candles used for short-term volume. |
| `MIN_RECENT_VOLUME_USDT` | No | `200000` | Minimum recent USDT volume required for a signal. |
| `SIGNAL_COOLDOWN_SECONDS` | No | `600` | Cooldown before repeating same-direction signal. |
| `POLL_INTERVAL_SECONDS` | No | `30` | Delay between scan rounds. |
| `TELEGRAM_BOT_TOKENS` | Yes for `run` | - | Comma-separated bot tokens used for signal sending. |
| `TELEGRAM_CHAT_ID` | Yes for `run` | - | Telegram destination for signal alerts. |
| `PLUS_TELEGRAM_BOT_TOKEN` | No | empty | Optional bot token for high-priority relay channel. |
| `PLUS_TELEGRAM_CHAT_ID` | No | empty | Optional chat id for relay channel. |
| `STATUS_TELEGRAM_BOT_TOKEN` | No | first main bot token | Optional dedicated bot for status message editing. |
| `STATUS_TELEGRAM_CHAT_ID` | No | main chat id | Optional dedicated chat id for status message editing. |
| `STATUS_MESSAGE_ID` | No | `5` | Telegram message id edited by the status command. |
| `LOG_LEVEL` | No | `INFO` | Logging level. |

## Usage

Run the signal service continuously:

```bash
python3 -m crypto_whale_hunter run
```

Run a single scan round:

```bash
python3 -m crypto_whale_hunter run --once
```

Update the status message on Telegram:

```bash
python3 -m crypto_whale_hunter status
```

Render the status message without sending it:

```bash
python3 -m crypto_whale_hunter status --dry-run
```

## Database Behavior

The application bootstraps the SQLite database automatically:

- creates the `coins` table when it does not exist
- inserts missing symbols from `coinlist.csv`
- preserves existing state for known coins

The schema remains backward-compatible with the original project.

## Quality Commands

```bash
make test
make check
make lint
make format
```

## Troubleshooting

- If the service exits immediately, check missing Telegram environment variables.
- If symbols are skipped, inspect logs for Binance fetch or insufficient candle warnings.
- If status updates fail, confirm `STATUS_MESSAGE_ID`, chat id, and bot permissions.
- If Telegram sends fail intermittently, verify all configured bot tokens are valid.

## Limitations

- Signal generation still depends on public exchange data latency and rate limits.
- SQLite is suitable for a single local worker; it is not a distributed coordination layer.
- The bot logic intentionally preserves the original signal thresholds and cooldown behavior.
