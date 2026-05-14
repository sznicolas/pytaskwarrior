"""Tests for ContextService using ConfigStore directly (no CLI adapter needed)."""

import os
import tempfile

import pytest

from src.taskwarrior.config.config_store import ConfigStore
from src.taskwarrior.dto.context_dto import ContextDTO
from taskwarrior.exceptions import TaskValidationError, TaskWarriorError
from taskwarrior.services.context_service import ContextService


def _make_service() -> tuple[ContextService, ConfigStore]:
    """Create a ContextService with a real ConfigStore backed by a temp taskrc."""
    tmpdir = tempfile.mkdtemp()
    taskrc = os.path.join(tmpdir, ".taskrc")
    open(taskrc, "w").close()
    cfg = ConfigStore(taskrc)
    return ContextService(cfg), cfg


def test_define_context_writes_to_taskrc():
    svc, cfg = _make_service()
    svc.define_context(
        ContextDTO(name="work", read_filter="project:work", write_filter="project:work")
    )
    cfg.refresh()
    assert cfg.config.get("context.work.read") == "project:work"
    assert cfg.config.get("context.work.write") == "project:work"


def test_define_context_invalid_name_raises():
    svc, _ = _make_service()
    with pytest.raises(TaskValidationError):
        svc.define_context(ContextDTO(name=" ", read_filter="a", write_filter="b"))


def test_apply_context_updates_active_key():
    svc, cfg = _make_service()
    svc.define_context(ContextDTO(name="work", read_filter="project:work", write_filter=""))
    svc.apply_context("work")
    cfg.refresh()
    assert cfg.config.get("context") == "work"


def test_apply_context_unknown_raises():
    svc, _ = _make_service()
    with pytest.raises(TaskWarriorError, match="not defined"):
        svc.apply_context("nonexistent")


def test_unset_context_removes_key():
    svc, cfg = _make_service()
    svc.define_context(ContextDTO(name="work", read_filter="project:work", write_filter=""))
    svc.apply_context("work")
    svc.unset_context()
    cfg.refresh()
    assert cfg.config.get("context") is None


def test_get_current_context_returns_name_or_none():
    svc, _ = _make_service()
    assert svc.get_current_context() is None

    svc.define_context(ContextDTO(name="work", read_filter="project:work", write_filter=""))
    svc.apply_context("work")
    assert svc.get_current_context() == "work"
