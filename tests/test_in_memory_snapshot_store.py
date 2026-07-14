"""Tests for the in-memory ISnapshotStore implementation used as a test double."""

import pytest

from app.shadow.in_memory_snapshot_store import InMemorySnapshotStore
from app.shadow.interfaces import ISnapshotStore
from app.shadow.schemas import CapturedRequest, CapturedResponse, NetworkSnapshot, ShadowSnapshot
from app.shadow.snapshot_store import SnapshotNotFoundError, SnapshotStoreError


def test_implements_isnapshot_store_interface():
    store = InMemorySnapshotStore()
    assert isinstance(store, ISnapshotStore)


def test_save_and_get_shadow_snapshot_object():
    store = InMemorySnapshotStore()

    req = CapturedRequest(
        method="GET", url="https://api.example.com/test", headers={"Accept": "*/*"}
    )
    res = CapturedResponse(status=200, headers={"Content-Type": "text/plain"}, body="hello-world")
    net_snap = NetworkSnapshot(request=req, response=res)
    snap = ShadowSnapshot(
        snapshot_id="test_snap_1",
        metadata={"user": "tester", "env": "ci"},
        network_snapshots=[net_snap],
    )

    store.save_snapshot("test_snap_1", snap)
    loaded_snap = store.get_snapshot("test_snap_1")

    assert loaded_snap.snapshot_id == "test_snap_1"
    assert loaded_snap.metadata["user"] == "tester"
    assert len(loaded_snap.network_snapshots) == 1
    assert loaded_snap.network_snapshots[0].request.url == "https://api.example.com/test"
    assert loaded_snap.network_snapshots[0].response.body == "hello-world"


def test_save_dict_and_get_snapshot():
    store = InMemorySnapshotStore()
    dict_data = {
        "snapshot_id": "test_snap_dict",
        "metadata": {"source": "manual"},
        "network_snapshots": [
            {
                "request": {
                    "method": "POST",
                    "url": "https://api.example.com/submit",
                    "headers": {},
                },
                "response": {"status": 201, "headers": {}, "body": "created"},
            }
        ],
    }

    store.save_snapshot("test_snap_dict", dict_data)
    loaded_snap = store.get_snapshot("test_snap_dict")

    assert loaded_snap.snapshot_id == "test_snap_dict"
    assert loaded_snap.network_snapshots[0].request.method == "POST"
    assert loaded_snap.network_snapshots[0].response.status == 201


def test_save_invalid_dict_raises_snapshot_store_error():
    store = InMemorySnapshotStore()
    invalid_dict = {
        "snapshot_id": "invalid",
        "network_snapshots": [{"request": {"bad_field": True}}],  # Missing required fields
    }

    with pytest.raises(SnapshotStoreError) as exc_info:
        store.save_snapshot("invalid", invalid_dict)
    assert "Invalid snapshot dict structure" in str(exc_info.value)


def test_save_unsupported_type_raises_snapshot_store_error():
    store = InMemorySnapshotStore()

    with pytest.raises(SnapshotStoreError) as exc_info:
        store.save_snapshot("unsupported", [1, 2, 3])  # type: ignore[arg-type]
    assert "Unsupported data type" in str(exc_info.value)


def test_get_snapshot_not_found_raises_error():
    store = InMemorySnapshotStore()

    with pytest.raises(SnapshotNotFoundError) as exc_info:
        store.get_snapshot("does_not_exist")
    assert "does not exist" in str(exc_info.value)
