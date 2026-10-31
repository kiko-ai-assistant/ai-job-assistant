from pathlib import Path

import pytest

from src.storage.sqlite_store import SqliteStateStore


@pytest.mark.asyncio
async def test_sqlite_state_store_lifecycle(tmp_path: Path) -> None:
    db_path = tmp_path / "test_state.sqlite"
    store = SqliteStateStore(db_path)
    await store.initialize()

    initial = await store.get_checkpoint("test_chan")
    assert initial == 0

    await store.commit_checkpoint("test_chan", 42)
    saved = await store.get_checkpoint("test_chan")
    assert saved == 42

    await store.commit_checkpoint("test_chan", 100)
    updated = await store.get_checkpoint("test_chan")
    assert updated == 100

    chan2 = await store.get_checkpoint("other_chan")
    assert chan2 == 0

    await store.close()
