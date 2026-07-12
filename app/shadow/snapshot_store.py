"""Persistent storage layer for Shadow Runtime snapshots."""

import json
from pathlib import Path
from typing import Any

import structlog

from app.shadow.interfaces import ISnapshotStore
from app.shadow.schemas import ShadowSnapshot
from app.shadow.workspace import ShadowWorkspace

logger = structlog.get_logger(__name__)


class SnapshotStoreError(Exception):
    """Base exception for SnapshotStore errors."""

    pass


class SnapshotNotFoundError(SnapshotStoreError):
    """Raised when a snapshot is not found on disk."""

    pass


class SnapshotCorruptionError(SnapshotStoreError):
    """Raised when a snapshot file is corrupted or invalid."""

    pass


class SnapshotStore(ISnapshotStore):
    """Persistent storage layer for Shadow Runtime snapshots.

    Serializes and deserializes ShadowSnapshot objects to/from JSON files
    inside a workspace's snapshots directory.
    """

    def __init__(self, workspace: ShadowWorkspace):
        self.workspace = workspace
        # Ensure snapshots directory exists
        self.workspace.snapshots_dir.mkdir(parents=True, exist_ok=True)

    def _get_snapshot_path(self, snapshot_id: str) -> Path:
        """Returns the absolute file path for a given snapshot ID."""
        # Clean snapshot_id to prevent directory traversal
        safe_id = Path(snapshot_id).name
        return self.workspace.snapshots_dir / f"{safe_id}.json"

    def save_snapshot(self, snapshot_id: str, data: Any) -> None:
        """Persists a ShadowSnapshot object (or dict) to a JSON file on disk."""
        path = self._get_snapshot_path(snapshot_id)

        # If it's a ShadowSnapshot object, convert to dict/JSON
        if isinstance(data, ShadowSnapshot):
            snapshot_dict = data.model_dump()
        elif isinstance(data, dict):
            # Try to validate/parse to ensure correctness before saving
            try:
                ShadowSnapshot(**data)
            except Exception as e:
                raise SnapshotStoreError(f"Invalid snapshot dict structure: {e}")
            snapshot_dict = data
        else:
            raise SnapshotStoreError("Unsupported data type; expected ShadowSnapshot or dict")

        try:
            # Deterministic serialization: sort keys, indent for readability
            serialized = json.dumps(snapshot_dict, sort_keys=True, indent=2)
            path.write_text(serialized, encoding="utf-8")
            logger.info("snapshot_saved", snapshot_id=snapshot_id, path=str(path))
        except Exception as e:
            raise SnapshotStoreError(f"Failed to write snapshot to disk: {e}")

    def get_snapshot(self, snapshot_id: str) -> ShadowSnapshot:
        """Loads and deserializes a ShadowSnapshot from disk."""
        path = self._get_snapshot_path(snapshot_id)

        if not path.exists():
            logger.warning("snapshot_not_found", snapshot_id=snapshot_id, path=str(path))
            raise SnapshotNotFoundError(f"Snapshot '{snapshot_id}' does not exist at {path}")

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            raise SnapshotStoreError(f"Failed to read snapshot file: {e}")

        try:
            snapshot_dict = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(
                "snapshot_file_corrupted", snapshot_id=snapshot_id, path=str(path), error=str(e)
            )
            raise SnapshotCorruptionError(f"Snapshot file is not valid JSON: {e}")

        try:
            return ShadowSnapshot(**snapshot_dict)
        except Exception as e:
            logger.error(
                "snapshot_data_invalid", snapshot_id=snapshot_id, path=str(path), error=str(e)
            )
            raise SnapshotCorruptionError(
                f"Snapshot data does not conform to ShadowSnapshot schema: {e}"
            )
