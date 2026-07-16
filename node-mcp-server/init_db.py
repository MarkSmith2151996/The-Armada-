#!/usr/bin/env python3
"""Initialize the Armada node context DB."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path


def init_db(db_path: Path, schema_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema = schema_path.read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema)


def main() -> int:
    root = Path(__file__).resolve().parent
    db_path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else Path("~/armada/node.db").expanduser()
    schema_path = Path(sys.argv[2]).expanduser() if len(sys.argv) > 2 else root / "schema.sql"
    init_db(db_path, schema_path)
    print(f"initialized {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
