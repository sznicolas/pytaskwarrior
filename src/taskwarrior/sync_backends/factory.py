from typing import Any, Dict, Type
from .sync_local import SyncLocal
from ..protocols.sync import SyncProtocol

# Mapping of backend type to class
SYNC_BACKEND_CLASSES: Dict[str, Type[SyncProtocol]] = {
    'local': SyncLocal,
    # Future: add other backends here, e.g. 'remote': SyncRemote
}

def create_sync_backend(config: Dict[str, Any]) -> SyncProtocol:
    """
    Factory function to create a sync backend instance based on config.
    Expects config to have at least a 'type' key.
    """
    backend_type = config.get('type')
    if backend_type not in SYNC_BACKEND_CLASSES:
        raise ValueError(f"Unknown sync backend type: {backend_type}")
    backend_cls = SYNC_BACKEND_CLASSES[backend_type]
    # Pass config to backend constructor (customize as needed per backend)
    if backend_type == 'local':
        sync_dir = config.get('sync_dir')
        if not sync_dir:
            raise ValueError("'sync_dir' must be specified for local backend")
        return backend_cls(sync_dir)
    # Add more backend initializations here as needed
    raise NotImplementedError(f"Backend type '{backend_type}' is not fully implemented.")
