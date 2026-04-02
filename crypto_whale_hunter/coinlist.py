from __future__ import annotations

import csv
from pathlib import Path
from typing import List


def load_coinlist(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"Coin list file not found: {path}")

    symbols = []
    seen = set()
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        for row in reader:
            if not row:
                continue
            symbol = row[0].strip().upper()
            if not symbol or symbol.startswith("#") or symbol in seen:
                continue
            seen.add(symbol)
            symbols.append(symbol)
    return symbols
