"""Neon ALTERs: users.avatar_url -> TEXT (base64 DP) + user_problem_progress.time_spent_seconds.

DSN from DATABASE_URL env (Neon). Idempotent.
"""
import os
import sys

import psycopg2

dsn = os.environ.get("DATABASE_URL", "").strip()
if not dsn:
    sys.exit("DATABASE_URL env var required (Neon DSN)")
if dsn.startswith("postgres://"):
    dsn = dsn.replace("postgres://", "postgresql://", 1)

STMTS = [
    "ALTER TABLE user_problem_progress ADD COLUMN IF NOT EXISTS time_spent_seconds INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE users ALTER COLUMN avatar_url TYPE TEXT",
]

conn = psycopg2.connect(dsn, connect_timeout=20)
conn.autocommit = False
try:
    for s in STMTS:
        with conn.cursor() as cur:
            cur.execute(s)
        conn.commit()
        print("OK  ", s)
    with conn.cursor() as cur:
        cur.execute(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name='users' AND column_name='avatar_url'"
        )
        print("users.avatar_url:", cur.fetchone()[0])
        cur.execute(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name='user_problem_progress' AND column_name='time_spent_seconds'"
        )
        print("user_problem_progress.time_spent_seconds:", cur.fetchone()[0])
    conn.commit()
    print("done")
finally:
    conn.close()
