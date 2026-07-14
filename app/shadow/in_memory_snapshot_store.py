"""In-memory implementation of ISnapshotStore for tests."""

from typing import Any

from app.shadow.interfaces import ISnapshotStore
from app.shadow.schemas import ShadowSnapshot
from app.shadow.snapshot_store import (
    SnapshotNotFoundError,
    SnapshotStoreError,
)


class InMemorySnapshotStore(ISnapshotStore):
    """Dictionary-backed snapshot store used as a test double."""

    def __init__(self):
        self._snapshots: dict[str, ShadowSnapshot] = {}

    def save_snapshot(self, snapshot_id: str, data: Any) -> None:
        if isinstance(data, ShadowSnapshot):
            snapshot = data
        elif isinstance(data, dict):
            try:
                snapshot = ShadowSnapshot(**data)
            except Exception as e:
                raise SnapshotStoreError(f"Invalid snapshot dict structure: {e}")
        else:
            raise SnapshotStoreError("Unsupported data type; expected ShadowSnapshot or dict")

        self._snapshots[snapshot_id] = snapshot

    def get_snapshot(self, snapshot_id: str) -> ShadowSnapshot:
        if snapshot_id not in self._snapshots:
            raise SnapshotNotFoundError(f"Snapshot '{snapshot_id}' does not exist.")

        return self._snapshots[snapshot_id]
