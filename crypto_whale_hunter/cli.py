from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Sequence

from crypto_whale_hunter.config import Settings
from crypto_whale_hunter.logging_utils import configure_logging
from crypto_whale_hunter.market_data import BinanceFuturesMarketData
from crypto_whale_hunter.notifier import TelegramNotifier, TelegramStatusPublisher
from crypto_whale_hunter.repository import SQLiteSignalRepository
from crypto_whale_hunter.service import SignalScannerService
from crypto_whale_hunter.status import StatusService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crypto Whale Hunter command line interface.")
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Optional environment file. Values from the shell override values in the file.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run the signal scanner.")
    run_parser.add_argument("--once", action="store_true", help="Execute one scan cycle and exit.")

    status_parser = subparsers.add_parser("status", help="Update the status Telegram message.")
    status_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Render the status message to stdout instead of sending it.",
    )

    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    settings = Settings.from_env(env_file=Path(args.env_file))
    configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)

    repository = SQLiteSignalRepository(settings.db_path)

    if args.command == "run":
        settings.validate_runtime()
        market_data = BinanceFuturesMarketData(settings)
        notifier = TelegramNotifier(
            bot_tokens=settings.telegram_bot_tokens,
            chat_id=settings.telegram_chat_id,
            plus_bot_token=settings.plus_telegram_bot_token,
            plus_chat_id=settings.plus_telegram_chat_id,
        )
        service = SignalScannerService(
            settings=settings,
            repository=repository,
            market_data=market_data,
            notifier=notifier,
        )
        if args.once:
            summary = service.run_once()
            logger.info("Single scan completed: %s", summary)
            return 0
        service.run_forever()
        return 0

    settings.validate_status()
    publisher = TelegramStatusPublisher(
        bot_token=settings.status_telegram_bot_token,
        chat_id=settings.status_telegram_chat_id,
        message_id=settings.status_message_id,
    )
    service = StatusService(repository=repository, publisher=publisher)
    message = service.publish(dry_run=args.dry_run)
    if args.dry_run:
        print(message)
    return 0
