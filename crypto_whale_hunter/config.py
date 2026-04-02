from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple


def _parse_env_line(line: str) -> Optional[Tuple[str, str]]:
    cleaned = line.strip()
    if not cleaned or cleaned.startswith("#") or "=" not in cleaned:
        return None
    key, value = cleaned.split("=", 1)
    key = key.strip()
    value = value.strip().strip("'").strip('"')
    if not key:
        return None
    return key, value


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        parsed = _parse_env_line(raw_line)
        if parsed is None:
            continue
        key, value = parsed
        os.environ.setdefault(key, value)


def _split_csv(value: str) -> List[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def _get_int(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    return default if raw_value in (None, "") else int(raw_value)


def _get_float(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    return default if raw_value in (None, "") else float(raw_value)


def _resolve_path(base_dir: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    return candidate if candidate.is_absolute() else base_dir / candidate


@dataclass(frozen=True)
class Settings:
    base_dir: Path
    db_path: Path
    coinlist_path: Path
    timeframe: str
    limit: int
    rsi_period: int
    rsi_overbought: float
    rsi_oversold: float
    recent_volume_window: int
    min_recent_volume_usdt: float
    signal_cooldown_seconds: int
    poll_interval_seconds: int
    telegram_bot_tokens: List[str]
    telegram_chat_id: str
    plus_telegram_bot_token: Optional[str]
    plus_telegram_chat_id: Optional[str]
    status_telegram_bot_token: Optional[str]
    status_telegram_chat_id: Optional[str]
    status_message_id: int
    log_level: str

    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "Settings":
        base_dir = Path(__file__).resolve().parent.parent
        load_env_file(env_file or (base_dir / ".env"))

        db_path = _resolve_path(base_dir, os.getenv("DB_PATH", "db/database.db"))
        coinlist_path = _resolve_path(base_dir, os.getenv("COINLIST_PATH", "coinlist.csv"))
        telegram_tokens = _split_csv(os.getenv("TELEGRAM_BOT_TOKENS", ""))
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
        status_bot_token = os.getenv("STATUS_TELEGRAM_BOT_TOKEN", "").strip() or None
        status_chat_id = os.getenv("STATUS_TELEGRAM_CHAT_ID", "").strip() or None

        if not status_bot_token and telegram_tokens:
            status_bot_token = telegram_tokens[0]
        if not status_chat_id and telegram_chat_id:
            status_chat_id = telegram_chat_id

        return cls(
            base_dir=base_dir,
            db_path=db_path,
            coinlist_path=coinlist_path,
            timeframe=os.getenv("BINANCE_TIMEFRAME", "1m"),
            limit=_get_int("BINANCE_LIMIT", 1440),
            rsi_period=_get_int("RSI_PERIOD", 7),
            rsi_overbought=_get_float("RSI_OVERBOUGHT", 70),
            rsi_oversold=_get_float("RSI_OVERSOLD", 30),
            recent_volume_window=_get_int("RECENT_VOLUME_WINDOW", 10),
            min_recent_volume_usdt=_get_float("MIN_RECENT_VOLUME_USDT", 200000),
            signal_cooldown_seconds=_get_int("SIGNAL_COOLDOWN_SECONDS", 600),
            poll_interval_seconds=_get_int("POLL_INTERVAL_SECONDS", 30),
            telegram_bot_tokens=telegram_tokens,
            telegram_chat_id=telegram_chat_id,
            plus_telegram_bot_token=os.getenv("PLUS_TELEGRAM_BOT_TOKEN", "").strip() or None,
            plus_telegram_chat_id=os.getenv("PLUS_TELEGRAM_CHAT_ID", "").strip() or None,
            status_telegram_bot_token=status_bot_token,
            status_telegram_chat_id=status_chat_id,
            status_message_id=_get_int("STATUS_MESSAGE_ID", 5),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )

    def validate_runtime(self) -> None:
        missing = []
        if not self.telegram_bot_tokens:
            missing.append("TELEGRAM_BOT_TOKENS")
        if not self.telegram_chat_id:
            missing.append("TELEGRAM_CHAT_ID")
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing runtime configuration: {joined}")

    def validate_status(self) -> None:
        missing = []
        if not self.status_telegram_bot_token:
            missing.append("STATUS_TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKENS")
        if not self.status_telegram_chat_id:
            missing.append("STATUS_TELEGRAM_CHAT_ID or TELEGRAM_CHAT_ID")
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"Missing status configuration: {joined}")
