import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crypto_whale_hunter.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["status", *sys.argv[1:]]))
