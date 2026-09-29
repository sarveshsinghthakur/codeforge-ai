"""Generate Postgres migration SQL from the local SQLite database (Supabase target).

Outputs to scripts/sqlout/:
  00_schema.sql      - DROP + CREATE TABLE (FKs stripped) + ALTER TABLE ADD FOREIGN KEY
  10_data_<t>_<n>.sql- batched INSERTs preserving exact SQLite values
  99_sequences.sql   - setval() so future inserts don't collide with migrated IDs

Usage: python scripts/sqlite_to_supabase.py
"""
import json
import os
import re
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
SQLITE_DB = BACKEND / "codeforge.db"
OUT_DIR = Path(__file__).resolve().parent / "sqlout"
MAX_FILE_BYTES = 400_000

sys.path.insert(0, str(BACKEND))

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

import app.models  # noqa: F401  registers all tables on Base.metadata
from app.core.database import Base


def compile_ddl() -> tuple[str, list]:
    """CREATE TABLE in FK-dependency order (SQLAlchemy sorts topologically)."""
    dialect = postgresql.dialect()
    creates, idx_stmts, serial_pk = [], [], []
    for table in Base.metadata.sorted_tables:
        stmt = str(CreateTable(table).compile(dialect=dialect)).strip()
        if not stmt.endswith(";"):
            stmt += ";"
        creates.append(f"DROP TABLE IF EXISTS {table.name} CASCADE;\n{stmt}")

        for idx in table.indexes:
            try:
                idx_stmts.append(str(CreateIndex(idx).compile(dialect=dialect)).rstrip(";") + ";")
            except Exception:
                pass

        pk_cols = list(table.primary_key.columns)
        if len(pk_cols) == 1 and pk_cols[0].autoincrement:
            col = pk_cols[0]
            ctype = "BIGSERIAL" if "BIGINT" in str(col.type).upper() else "SERIAL"
            serial_pk.append((table.name, col.name, ctype))

    ddl = "-- schema\nSET client_min_messages = WARNING;\n\n" + "\n\n".join(creates) + "\n"

    # ensure autoincrement PKs are SERIAL (PG dialect may emit plain INTEGER)
    for tname, cname, ctype in serial_pk:
        ddl = re.sub(
            rf'("{cname}") INTEGER NOT NULL',
            rf"\g<1> {ctype} NOT NULL",
            ddl,
        )

    if idx_stmts:
        ddl += "\n-- indexes\n" + "\n".join(idx_stmts) + "\n"
    return ddl, list(Base.metadata.sorted_tables)


def sql_literal(value) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return "'" + value.isoformat(sep=" ") + "'"
    if isinstance(value, date):
        return "'" + value.isoformat() + "'"
    if isinstance(value, (bytes, bytearray)):
        return "'" + bytes(value).hex() + "'::bytea"
    s = str(value)
    return "'" + s.replace("'", "''") + "'"


def batch_inserts(table, columns: list[str], rows: list[tuple], out_files: list[tuple[str, str]], idx: int):
    col_sql = ", ".join(f'"{c}"' for c in columns)
    bool_idx = {i for i, c in enumerate(columns) if str(table.columns[c].type).upper() == "BOOLEAN"}
    buf, size, file_no = [], 0, 0

    def flush():
        nonlocal buf, size, file_no
        if not buf:
            return
        name = f"10_data_{idx:03d}_{table.name}_{file_no:04d}.sql"
        out_files.append((name, "\n".join(buf) + "\n"))
        buf, size = [], 0
        file_no += 1

    for row in rows:
        parts = []
        for i, v in enumerate(row):
            if i in bool_idx and v is not None:
                parts.append("TRUE" if int(v) else "FALSE")
            else:
                parts.append(sql_literal(v))
        stmt = f'INSERT INTO "{table.name}" ({col_sql}) VALUES ({", ".join(parts)}) ON CONFLICT DO NOTHING;'
        buf.append(stmt)
        size += len(stmt) + 1
        if size >= MAX_FILE_BYTES:
            flush()
    flush()


def main():
    if not SQLITE_DB.exists():
        sys.exit(f"SQLite DB not found: {SQLITE_DB}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in OUT_DIR.glob("*.sql"):
        old.unlink()

    ddl, tables = compile_ddl()
    (OUT_DIR / "000_schema.sql").write_text(ddl, encoding="utf-8")
    print(f"schema: {len(ddl):,} bytes")

    con = sqlite3.connect(str(SQLITE_DB))
    con.row_factory = sqlite3.Row
    out_files: list[tuple[str, str]] = []
    total_rows = 0

    for idx, table in enumerate(tables, start=1):
        name = table.name
        try:
            columns = [r["name"] for r in con.execute(f'PRAGMA table_info("{name}")')]
        except sqlite3.Error:
            print(f"  skip {name} (not in sqlite)")
            continue
        rows = con.execute(f'SELECT * FROM "{name}"').fetchall()
        if not rows:
            continue
        tuples = [tuple(r[c] for c in columns) for r in rows]
        batch_inserts(table, columns, tuples, out_files, idx)
        total_rows += len(tuples)
        print(f"  {name}: {len(tuples)} rows")

    con.close()

    # sequence resets for serial PKs
    seq_lines = ["-- reset sequences\n"]
    for table in Base.metadata.sorted_tables:
        pk = list(table.primary_key.columns)
        if len(pk) == 1 and pk[0].autoincrement:
            seq_lines.append(
                f"SELECT setval(pg_get_serial_sequence('{table.name}', '{pk[0].name}'), "
                f'COALESCE((SELECT MAX("{pk[0].name}") FROM {table.name}), 1), true);'
            )
    (OUT_DIR / "99_sequences.sql").write_text("\n".join(seq_lines) + "\n", encoding="utf-8")

    # order: schema, data by name, sequences last (rename to force tail)
    out_files.sort(key=lambda x: x[0])
    for i, (name, content) in enumerate(out_files, start=1):
        (OUT_DIR / f"{i:03d}_{name}").write_text(content, encoding="utf-8")

    size = sum(f.stat().st_size for f in OUT_DIR.glob("*.sql"))
    print(f"\n{len(list(OUT_DIR.glob('*.sql')))} files, {size:,} bytes, {total_rows} data rows")


if __name__ == "__main__":
    main()
