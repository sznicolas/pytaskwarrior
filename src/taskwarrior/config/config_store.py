import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

from ..exceptions import TaskConfigurationError

if TYPE_CHECKING:
    from ..dto.context_dto import ContextDTO

DEFAULT_OPTIONS = [
    "rc.confirmation=off",
    "rc.bulk=0",
]

class ConfigStore:
    """
    Loads and caches Taskwarrior config from taskrc. Provides access methods and refresh capability.
    """

    def __init__(self, taskrc_path: str, data_location: str | None = None) -> None:
        self._taskrc_path: Path = Path(os.path.expandvars(taskrc_path)).expanduser()
        self._data_location: Path | None = Path(os.path.expandvars(data_location)).expanduser() if data_location else None
        self._check_or_create_taskfiles()
        self._config: dict[str, str] | None = None
        self._load_config()

    def _load_config(self) -> None:
        self._config = self._extract_taskrc_config(self._taskrc_path)

    def _check_or_create_taskfiles(self) -> None:
        """Create taskrc and data directory if they don't exist."""
        if not self._taskrc_path.exists():
            default_content = f"""# Taskwarrior configuration file
# This file was automatically created by pytaskwarrior
# Default data location
rc.data.location={self._data_location or '~/.task'}
# Disable confirmation prompts
rc.confirmation=off
rc.bulk=0
"""
            self._taskrc_path.parent.mkdir(parents=True, exist_ok=True)
            self._taskrc_path.write_text(default_content)
        if self._data_location and not self._data_location.exists():
            self._data_location.mkdir(parents=True, exist_ok=True)

    def _extract_taskrc_config(self, path: Path) -> dict[str, str]:
        import configparser

        config: dict[str, str] = {}
        parser = configparser.ConfigParser()
        # Accept .taskrc files without section headers by adding a dummy section
        try:
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()
        except FileNotFoundError as e:
            raise TaskConfigurationError(f"Taskrc file not found: {path}") from e
        except PermissionError as e:
            raise TaskConfigurationError(f"Cannot read taskrc file (permission denied): {path}") from e
        except OSError as e:
            raise TaskConfigurationError(f"Failed to read taskrc file: {path}: {e}") from e
        # Only keep blank lines, comments, or lines containing '=' (key-value)
        filtered = [line for line in lines if line.strip() == "" or line.strip().startswith("#") or "=" in line]
        content = "[taskrc]\n" + "".join(filtered)
        parser.read_string(content)
        for section in parser.sections():
            for key, value in parser.items(section):
                config[key] = value
        for key in parser.defaults():
            config[key] = parser.defaults()[key]
        return config

    def refresh(self) -> None:
        """Reloads the config from disk."""
        self._load_config()

    @property
    def config(self) -> dict[str, str]:
        if self._config is None:
            self._load_config()
        assert self._config is not None
        return self._config

    @property
    def taskrc_path(self) -> Path:
        """Return the path to the taskrc file."""
        return self._taskrc_path

    @property
    def cli_options(self) -> list[str]:
        """Return CLI options for Taskwarrior commands, including defaults."""
        options = [f"rc:{self._taskrc_path}"]
        if self._data_location:
            options.append(f"rc.data.location={self._data_location}")
        options.extend(DEFAULT_OPTIONS)
        return options

    def get_sync_config(self) -> dict[str, str]:
        # Extract sync config directly from self.config
        # Accept both 'sync.' and 'taskrc.sync.' keys for compatibility
        return {k: v for k, v in self.config.items() if k.startswith("sync.")}

    def get_contexts_config(self) -> dict[str, str]:
        # Extract context config directly from self.config
        return {k: v for k, v in self.config.items() if k.startswith("context.")}

    def get_contexts(self, current_context: str | None = None) -> list["ContextDTO"]:
        """
        Returns a list of ContextDTO objects representing all defined contexts.
        """
        from ..dto.context_dto import ContextDTO

        contexts_config = self.get_contexts_config()
        names: dict[str, dict[str, str]] = {}

        for k, v in contexts_config.items():
            m = re.match(r"context\.([^\.]+)\.(read|write)", k)
            if m:
                ctx_name = m.group(1)
                kind = m.group(2)
                names.setdefault(ctx_name, {})[kind] = v
        return [
            ContextDTO(
                name=n,
                read_filter=filters.get("read", ""),
                write_filter=filters.get("write", ""),
                active=(n == current_context),
            )
            for n, filters in names.items()
        ]
