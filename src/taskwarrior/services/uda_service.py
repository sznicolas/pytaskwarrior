from src.taskwarrior import UdaRegistry
from ..adapters.taskwarrior_adapter import TaskWarriorAdapter
from ..dto.uda_dto import UdaDTO, UdaType

# TODO: manage orphaned `task udas`
class UdaService:
    def __init__(self, adapter: TaskWarriorAdapter):
        self.adapter = adapter
        self.registry = UdaRegistry()  # No adapter needed here

    def load_udas_from_taskrc(self) -> None:
        self.registry.load_from_taskrc(self.adapter.taskrc_file)

    def define_uda(self, uda: UdaDTO) -> None:
        """Define a new UDA using the adapter."""
        self.registry.define_update_uda(uda, self.adapter)

    def update_uda(self, uda: UdaDTO) -> None:
        """Update an existing UDA using the adapter."""
        self.registry.define_update_uda(uda, self.adapter)

    def delete_uda(self, uda: UdaDTO) -> None:
        """Delete a UDA using the adapter."""
        self.registry.delete_uda(uda, self.adapter)
