import asyncio
import sys
from pathlib import Path

# Ensure src/ and apps/bot/ are on sys.path
APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent.parent

for path in (APP_DIR, PROJECT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from src.bot.run import main

if __name__ == "__main__":
    asyncio.run(main())
