"""Shadow Runtime entry point.
Instantiating the runtime has no side effects, and all collaborating components
are optional so a minimal runtime can be created and driven without wiring any
real components yet.
"""

import structlog

from app.shadow.context import ShadowContext
from app.shadow.interfaces import IMockInjector, IShadowRuntime, IShadowWorkspace, ISnapshotStore

logger = structlog.get_logger(__name__)

SHADOW_PLACEHOLDER_MESSAGE = (
    "Shadow Testing runtime is under development — no shadow logic runs yet."
)


class ShadowRuntime(IShadowRuntime):
    """Minimal Shadow Runtime that manages a lifecycle and a :class:`ShadowContext`.

    Collaborators are injected optionally so the runtime can be instantiated on
    its own. :meth:`initialize` creates and activates a context; :meth:`shutdown`
    deactivates and releases it. Both methods are idempotent.
    """

    def __init__(
        self,
        workspace: IShadowWorkspace | None = None,
        snapshot_store: ISnapshotStore | None = None,
        injector: IMockInjector | None = None,
    ) -> None:
        self.workspace = workspace
        self.snapshot_store = snapshot_store
        self.injector = injector
        self._context: ShadowContext | None = None

    @property
    def context(self) -> ShadowContext | None:
        """The active :class:`ShadowContext`, or ``None`` before initialization."""
        return self._context

    @property
    def is_active(self) -> bool:
        """Whether the runtime currently holds an active context."""
        return self._context is not None and self._context.is_active

    def initialize(self) -> None:
        """Create and activate the shadow context.

        Idempotent: calling it again while already active leaves the existing
        context in place. Access the context via :attr:`context`.
        """
        if self.is_active:
            logger.info("shadow_runtime_already_initialized")
            return

        self._context = ShadowContext(
            workspace=self.workspace,
            snapshot_store=self.snapshot_store,
            injector=self.injector,
        )
        self._context.activate()
        logger.info("shadow_runtime_initialized")

    def shutdown(self) -> None:
        """Deactivate and release the shadow context.

        Idempotent: a no-op if the runtime was never initialized or is already
        shut down.
        """
        if self._context is None:
            logger.info("shadow_runtime_already_shutdown")
            return

        self._context.deactivate()
        self._context = None
        logger.info("shadow_runtime_shutdown")


def run_shadow() -> str:
    """Dedicated entry point for ``e2e-healer --shadow``.

    Exercises the minimal runtime lifecycle (initialize → shutdown) to prove the
    foundation is wired, then returns a human-readable status message for the CLI
    to surface. The real Shadow Testing orchestration (mocking, trace parsing,
    DOM injection) lands in a future issue.
    """
    runtime = ShadowRuntime()
    runtime.initialize()
    runtime.shutdown()
    return SHADOW_PLACEHOLDER_MESSAGE
