from typing import Optional
from ..protocols.sync import SyncProtocol

from taskchampion import Replica
import os

class SyncLocal(SyncProtocol):
    def __init__(self, sync_dir: str):
        self.sync_dir = sync_dir
        self._replica = Replica.new_on_disk(self.sync_dir, True)

    def synchronize(self) -> None:
        # Use the Replica object for local sync
        self._replica.sync_to_local(self.sync_dir, avoid_snapshots=False)
