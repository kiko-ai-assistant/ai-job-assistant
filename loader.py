import os
import re
from yoyo import step
from src.config import SQL_DIR

def build_steps():
    migration_steps = []

    pattern = re.compile(r'^(\d+)_([\w-]+)\.up.sql$')

    # Get all 'up' migrations
    up_files = [f for f in os.listdir(SQL_DIR) if pattern.match(f)]

    for up_file in up_files:
        prefix, name = pattern.match(up_file).groups()
        down_file = f"{prefix}_{name}.down.sql"
        down_path = SQL_DIR / down_file

        with open(SQL_DIR / up_file, 'r', encoding='utf-8') as f:
            up_sql = f.read()

        down_sql = ""
        if down_path.exists():
            with open(down_path, 'r', encoding='utf-8') as f:
                down_sql = f.read()

        migration_steps.append(step(up_sql, down_sql))

    return migration_steps

steps = build_steps()
