from typing import Protocol

class SyncProtocol(Protocol):
    def synchronize(self) -> None:
        """Perform the synchronization process."""
        ...
    # Future extension: add more sync-related methods as needed
