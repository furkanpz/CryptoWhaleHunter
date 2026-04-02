from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable, List

from crypto_whale_hunter.models import CoinState


CREATE_COINS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS coins (
    coinname TEXT,
    lastwar INTEGER,
    lastvol REAL,
    signalcount INTEGER,
    signaltype TEXT,
    firstsignaltime INTEGER
)
"""


class SQLiteSignalRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def initialize(self, coin_names: Iterable[str]) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        normalized = list(dict.fromkeys(name.strip().upper() for name in coin_names if name.strip()))
        with closing(self._connect()) as connection:
            connection.execute(CREATE_COINS_TABLE_SQL)
            existing = {
                row["coinname"]
                for row in connection.execute("SELECT coinname FROM coins").fetchall()
            }
            missing = [
                (coinname, 0, 0.0, 0, "long", 0)
                for coinname in normalized
                if coinname not in existing
            ]
            if missing:
                connection.executemany(
                    """
                    INSERT INTO coins (coinname, lastwar, lastvol, signalcount, signaltype, firstsignaltime)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    missing,
                )
            connection.commit()

    def get_coin_state(self, coin_name: str) -> CoinState:
        with closing(self._connect()) as connection:
            row = connection.execute(
                """
                SELECT coinname, lastwar, lastvol, signalcount, signaltype, firstsignaltime
                FROM coins
                WHERE coinname = ?
                ORDER BY rowid ASC
                LIMIT 1
                """,
                (coin_name,),
            ).fetchone()
            if row is None:
                connection.execute(
                    """
                    INSERT INTO coins (coinname, lastwar, lastvol, signalcount, signaltype, firstsignaltime)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (coin_name, 0, 0.0, 0, "long", 0),
                )
                connection.commit()
                return CoinState(coinname=coin_name)
            return self._row_to_state(row)

    def upsert_state(self, state: CoinState) -> None:
        with closing(self._connect()) as connection:
            existing = connection.execute(
                "SELECT rowid FROM coins WHERE coinname = ? ORDER BY rowid ASC LIMIT 1",
                (state.coinname,),
            ).fetchone()
            if existing is None:
                connection.execute(
                    """
                    INSERT INTO coins (coinname, lastwar, lastvol, signalcount, signaltype, firstsignaltime)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        state.coinname,
                        state.last_signal_time,
                        state.last_total_volume_usdt,
                        state.signal_count,
                        state.signal_type,
                        state.first_signal_time,
                    ),
                )
            else:
                connection.execute(
                    """
                    UPDATE coins
                    SET lastwar = ?, lastvol = ?, signalcount = ?, signaltype = ?, firstsignaltime = ?
                    WHERE rowid = ?
                    """,
                    (
                        state.last_signal_time,
                        state.last_total_volume_usdt,
                        state.signal_count,
                        state.signal_type,
                        state.first_signal_time,
                        existing["rowid"],
                    ),
                )
            connection.commit()

    def list_states(self) -> List[CoinState]:
        with closing(self._connect()) as connection:
            rows = connection.execute(
                """
                SELECT coinname, lastwar, lastvol, signalcount, signaltype, firstsignaltime
                FROM coins
                ORDER BY coinname ASC
                """
            ).fetchall()
        return [self._row_to_state(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _row_to_state(row: sqlite3.Row) -> CoinState:
        return CoinState(
            coinname=str(row["coinname"]),
            last_signal_time=int(row["lastwar"] or 0),
            last_total_volume_usdt=float(row["lastvol"] or 0.0),
            signal_count=int(row["signalcount"] or 0),
            signal_type=str(row["signaltype"] or "long"),
            first_signal_time=int(row["firstsignaltime"] or 0),
        )
