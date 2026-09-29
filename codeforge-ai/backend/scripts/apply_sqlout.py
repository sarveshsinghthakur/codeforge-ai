"""Apply generated sqlout/*.sql files to Supabase in order (direct Postgres).

Password comes from env SUPABASE_DB_PASSWORD (never from files/git).

Usage:
  SUPABASE_DB_PASSWORD=... python scripts/apply_sqlout.py [--dry-run]
"""
import glob
import os
import sys
import time
from pathlib import Path

import psycopg2

SQL_DIR = Path(__file__).resolve().parent / "sqlout"
DSN = {
    "host": "aws-0-ap-southeast-1.pooler.supabase.com",
    "port": 6543,
    "user": "postgres.cfknoaukergtqfpprhex",
    "dbname": "postgres",
    "sslmode": "require",
    "connect_timeout": 20,
}

EXPECTED = {
    "users": 2,
    "problems": 373,
    "test_cases": 4149,
    "submissions": 12,
    "ai_conversations": 4,
    "ai_messages": 22,
    "user_problem_progress": 3,
}


def main():
    password = os.environ.get("SUPABASE_DB_PASSWORD")
    if not password:
        sys.exit("SUPABASE_DB_PASSWORD env var required")

    def order_key(path: str):
        name = Path(path).name
        if "schema" in name:
            return (0, name)
        if "sequences" in name:
            return (2, name)
        return (1, name)

    files = sorted(glob.glob(str(SQL_DIR / "*.sql")), key=order_key)
    if not files:
        sys.exit(f"no .sql files in {SQL_DIR}")
    dry = "--dry-run" in sys.argv
    print(f"{len(files)} files{' (dry run)' if dry else ''}")
    if dry:
        for f in files:
            print("  would apply:", Path(f).name)
        return

    conn = psycopg2.connect(password=password, **DSN)
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

    with conn.cursor() as cur:
        print("\nverification:")
        ok = True
        for table, want in EXPECTED.items():
            cur.execute(f'SELECT count(*) FROM "{table}"')
            got = cur.fetchone()[0]
            flag = "OK " if got == want else "MISMATCH"
            if got != want:
                ok = False
            print(f"  {flag} {table}: {got} (expected {want})")
        cur.execute("SELECT setval(pg_get_serial_sequence('users','id'), COALESCE((SELECT MAX(id) FROM users),1), true)")
        conn.commit()
    conn.close()
    print(f"\ndone in {time.time() - started:.1f}s" + ("" if ok else " — WITH MISMATCHES"))
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
