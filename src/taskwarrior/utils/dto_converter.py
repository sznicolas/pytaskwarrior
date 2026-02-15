"""DTO conversion utilities.

This module provides functions for converting between different
task data transfer objects.
"""

from ..dto.task_dto import TaskInputDTO, TaskOutputDTO


def task_output_to_input(task_output: TaskOutputDTO) -> TaskInputDTO:
    """Convert a TaskOutputDTO to a TaskInputDTO for modification.

    This is useful when you want to modify an existing task: retrieve it
    as TaskOutputDTO, convert to TaskInputDTO, make changes, then save.

    The conversion excludes read-only fields that are set by TaskWarrior
    (uuid, entry, start, end, modified, index, status, urgency, imask, rtype).

    Args:
        task_output: The task output to convert.

    Returns:
        A TaskInputDTO with the editable fields from the output.

    Example:
        >>> task = tw.get_task(uuid)
        >>> input_dto = task_output_to_input(task)
        >>> input_dto.priority = Priority.HIGH
        >>> tw.modify_task(input_dto, uuid)
    """
    data = task_output.model_dump(
        exclude={"uuid", "entry", "start", "end", "modified", "index", "status", "urgency", "imask", "rtype"}
    )
    # Convert datetime fields to strings as required by TaskInputDTO
    datetime_fields = ["due", "scheduled", "wait", "until"]
    for field in datetime_fields:
        if field in data and data[field] is not None:
            data[field] = data[field].isoformat()
    return TaskInputDTO(**data)
