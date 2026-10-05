"""Apply generated sqlout/*.sql files to any Postgres DSN from env (Neon target).

DSN comes from DATABASE_URL (never hardcoded / never from files/git).

Usage:
  DATABASE_URL=postgresql://... python scripts/apply_sqlout_neon.py [--dry-run]
"""
import glob
import os
import sqlite3
import sys
import time
from pathlib import Path

import psycopg2

SQL_DIR = Path(__file__).resolve().parent / "sqlout"
SQLITE_DB = Path(__file__).resolve().parents[1] / "codeforge.db"


def order_key(path: str):
    name = Path(path).name
    if "schema" in name:
        return (0, name)
    if "sequences" in name:
        return (2, name)
    return (1, name)


def main():
    dsn = os.environ.get("DATABASE_URL", "").strip()
    if not dsn:
        sys.exit("DATABASE_URL env var required")
    if dsn.startswith("postgres://"):
        dsn = dsn.replace("postgres://", "postgresql://", 1)

    files = sorted(glob.glob(str(SQL_DIR / "*.sql")), key=order_key)
    if not files:
        sys.exit(f"no .sql files in {SQL_DIR}")
    dry = "--dry-run" in sys.argv
    print(f"{len(files)} files{' (dry run)' if dry else ''}")
    if dry:
        for f in files:
            print("  would apply:", Path(f).name)
        return

    conn = psycopg2.connect(dsn, connect_timeout=20)
    conn.autocommit = False
    started = time.time()
    for i, path in enumerate(files, 1):
        name = Path(path).name
        sql = Path(path).read_text(encoding="utf-8")
        t0 = time.time()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print(f"[{i:02d}/{len(files)}] OK   {name}  ({time.time() - t0:.1f}s)")
        except Exception as e:
            conn.rollback()
            print(f"[{i:02d}/{len(files)}] FAIL {name}: {e}")
            sys.exit(1)

    print("\nverification (sqlite vs neon):")
    scon = sqlite3.connect(str(SQLITE_DB))
    ok = True
    tables = [r[0] for r in scon.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    )]
    with conn.cursor() as cur:
        for t in sorted(tables):
            want = scon.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            try:
                cur.execute(f'SELECT COUNT(*) FROM "{t}"')
                got = cur.fetchone()[0]
            except Exception:
                got = "ERR"
            flag = "OK " if got == want else "MISMATCH"
            if got != want:
                ok = False
            print(f"  {flag} {t}: {got} (sqlite {want})")
    scon.close()
    conn.commit()
    conn.close()
    print(f"\ndone in {time.time() - started:.1f}s" + ("" if ok else " — WITH MISMATCHES"))
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
