"""Unit tests for the TaskID class."""

from uuid import UUID

import pytest

from taskwarrior import TaskID
from taskwarrior.exceptions import TaskValidationError

SAMPLE_UUID = UUID("550e8400-e29b-41d4-a716-446655440000")
SAMPLE_UUID_STR = "550e8400-e29b-41d4-a716-446655440000"


class TestTaskIDConstructor:
    def test_from_positive_int(self):
        tid = TaskID(1)
        assert str(tid) == "1"

    def test_from_large_int(self):
        tid = TaskID(999)
        assert str(tid) == "999"

    def test_from_uuid_object(self):
        tid = TaskID(SAMPLE_UUID)
        assert str(tid) == SAMPLE_UUID_STR

    def test_from_uuid_string(self):
        tid = TaskID(SAMPLE_UUID_STR)
        assert str(tid) == SAMPLE_UUID_STR

    def test_from_int_string(self):
        tid = TaskID("42")
        assert str(tid) == "42"

    def test_from_uuid_prefix(self):
        """TaskWarrior accepts partial UUID prefixes."""
        tid = TaskID("550e8400")
        assert str(tid) == "550e8400"

    def test_strips_whitespace(self):
        tid = TaskID("  42  ")
        assert str(tid) == "42"

    def test_zero_int_raises(self):
        with pytest.raises(TaskValidationError, match="positive integer"):
            TaskID(0)

    def test_negative_int_raises(self):
        with pytest.raises(TaskValidationError, match="positive integer"):
            TaskID(-1)

    def test_empty_string_raises(self):
        with pytest.raises(TaskValidationError, match="empty"):
            TaskID("")

    def test_whitespace_only_string_raises(self):
        with pytest.raises(TaskValidationError, match="empty"):
            TaskID("   ")

    def test_invalid_type_raises(self):
        with pytest.raises(TaskValidationError):
            TaskID(3.14)  # type: ignore[arg-type]


class TestTaskIDEquality:
    def test_equal_from_same_int(self):
        assert TaskID(1) == TaskID(1)

    def test_equal_from_same_uuid(self):
        assert TaskID(SAMPLE_UUID) == TaskID(SAMPLE_UUID_STR)

    def test_not_equal_different_ids(self):
        assert TaskID(1) != TaskID(2)

    def test_not_equal_to_plain_int(self):
        assert TaskID(1) != 1

    def test_not_equal_to_plain_str(self):
        assert TaskID("42") != "42"


class TestTaskIDHash:
    def test_hashable(self):
        s = {TaskID(1), TaskID(2), TaskID(1)}
        assert len(s) == 2

    def test_usable_as_dict_key(self):
        d = {TaskID(1): "task one"}
        assert d[TaskID(1)] == "task one"


class TestTaskIDRepr:
    def test_repr(self):
        assert repr(TaskID(42)) == "TaskID('42')"
        assert repr(TaskID(SAMPLE_UUID_STR)) == f"TaskID({SAMPLE_UUID_STR!r})"
