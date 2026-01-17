from ..dto.task_dto import TaskInputDTO, TaskOutputDTO


def task_output_to_input(task_output: TaskOutputDTO) -> TaskInputDTO:
    """Convert TaskOutputDTO to TaskInputDTO for modification."""
    data = task_output.model_dump(
        exclude={"uuid", "entry", "start", "end", "modified", "index", "status", "urgency", "imask", "rtype"}
    )
    # Convert datetime fields to strings as required by TaskInputDTO
    datetime_fields = ["due", "scheduled", "wait", "until"]
    for field in datetime_fields:
        if field in data and data[field] is not None:
            data[field] = data[field].isoformat()
    return TaskInputDTO(**data)
