#!/usr/bin/env python3
from __future__ import annotations

import asyncio
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.db import AsyncSessionLocal
from app.seed import seed_published_games
from app.storage import ObjectStorageService


async def main() -> None:
    storage = ObjectStorageService(settings)
    async with AsyncSessionLocal() as session:
        games = await seed_published_games(session, storage)
    print(f"Seeded {len(games)} published games")


if __name__ == "__main__":
    asyncio.run(main())
