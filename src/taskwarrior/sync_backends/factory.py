from typing import Any

from .sync_protocol import SyncProtocol
from .sync_local import SyncLocal

def create_sync_backend(config: dict[str, Any]) -> SyncProtocol | None:
    """
    Factory function to create a sync backend instance based on config.
    Supports 'sync.local.server_dir' key. Returns SyncLocal when configured or None.
    """
    server_dir = config.get("sync.local.server_dir")
    if server_dir:
        # Ensure server_dir is a non-empty string
        server_dir_str = str(server_dir)
        if server_dir_str.strip() == "":
            return None
        return SyncLocal(server_dir_str)
    return None
