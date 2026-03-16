from typing import Any, Optional

# Provide a module-level placeholder so tests can patch `Replica` on the module
Replica: Any = None

from .sync_protocol import SyncProtocol


class SyncLocal(SyncProtocol):
    def __init__(self, sync_dir: str) -> None:
        self.sync_dir = sync_dir
        # Lazily created replica to avoid side-effects at import/instantiation time
        self._replica: Optional[Any] = None

    def _ensure_replica(self) -> None:
        if self._replica is None:
            # Prefer a patched module-level Replica (tests can set this), otherwise import lazily
            Replica_cls = globals().get("Replica")
            if Replica_cls is None:
                from taskchampion import Replica as Replica_cls

            self._replica = Replica_cls.new_on_disk(self.sync_dir, True)

    def synchronize(self) -> None:
        # Ensure the Replica exists, then perform local sync
        self._ensure_replica()
        assert self._replica is not None
        self._replica.sync_to_local(self.sync_dir, avoid_snapshots=False)
