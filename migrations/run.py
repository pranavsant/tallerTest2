"""
Migration runner — applies SQL migrations in order.

Usage:
    python -m migrations.run
"""
from __future__ import annotations

import asyncio
import os
import re
from pathlib import Path

import asyncpg


async def run_migrations() -> None:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:password@localhost:5432/overseer_ai",
    )
    # asyncpg uses postgresql:// not postgresql+asyncpg://
    url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(url)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id         SERIAL PRIMARY KEY,
            name       TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
    """)

    migration_dir = Path(__file__).parent
    migration_files = sorted(
        f for f in migration_dir.glob("*.sql") if re.match(r"^\d{3}_", f.name)
    )

    for mf in migration_files:
        already_applied = await conn.fetchval(
            "SELECT 1 FROM _migrations WHERE name = $1", mf.name
        )
        if already_applied:
            print(f"[skip]  {mf.name}")
            continue

        sql = mf.read_text()
        await conn.execute(sql)
        await conn.execute(
            "INSERT INTO _migrations (name) VALUES ($1)", mf.name
        )
        print(f"[apply] {mf.name}")

    await conn.close()
    print("Migrations complete.")


if __name__ == "__main__":
    asyncio.run(run_migrations())
