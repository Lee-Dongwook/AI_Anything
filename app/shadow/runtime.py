"""Shadow Runtime orchestrator (placeholder).
This module is a skeleton placeholder: it defines the assembly point and the
component wiring only. No runtime execution logic is implemented yet; the
orchestration methods raise :class:`NotImplementedError` until a future issue
fills them in.
"""

from typing import Any

from app.shadow.interfaces import IMockInjector, IShadowRuntime, ISnapshotStore, IShadowWorkspace


class ShadowRuntime(IShadowRuntime):
    """Placeholder orchestrator for the Shadow Runtime.

    Receives the collaborating components via dependency injection and exposes
    the orchestration surface (:meth:`setup`, :meth:`replay`, :meth:`teardown`)
    that future implementations will flesh out. Instantiating this class has no
    side effects; the methods are intentionally not yet implemented.
    """

    def __init__(
        self,
        workspace: IShadowWorkspace,
        snapshot_store: ISnapshotStore,
        injector: IMockInjector,
    ) -> None:
        self.workspace = workspace
        self.snapshot_store = snapshot_store
        self.injector = injector

    def setup(self) -> None:
        """Prepare the runtime for a replay. Not implemented yet."""
        raise NotImplementedError("ShadowRuntime.setup is not implemented yet")

    def replay(self, snapshot_id: str) -> Any:
        """Replay the given snapshot through the shadow flow. Not implemented yet."""
        raise NotImplementedError("ShadowRuntime.replay is not implemented yet")

    def teardown(self) -> None:
        """Release runtime resources after a replay. Not implemented yet."""
        raise NotImplementedError("ShadowRuntime.teardown is not implemented yet")
