# UDA Implementation

User Defined Attributes (UDAs) extend TaskWarrior with custom fields.

Note: In this library the DTO uses the field name `uda_type` (to avoid using the Python reserved word `type`). In TaskWarrior configuration files the corresponding key is written as `uda.<name>.type`. Examples in this document use the public TaskWarrior facade (for example `tw.define_uda`, `tw.update_uda`, and `tw.delete_uda`).

## UDA Definition Examples

### String UDA with Allowed Values

```python
from taskwarrior import TaskWarrior, UdaConfig, UdaType

tw = TaskWarrior()

# Define a severity UDA
severity = UdaConfig(
    name="severity",
    uda_type=UdaType.STRING,
    label="Severity",
    values=["low", "medium", "high", "critical"],
    default="medium",
)
tw.define_uda(severity)
```

### Numeric UDA for Time Estimates

```python
# Define an estimate UDA
estimate = UdaConfig(
    name="estimate",
    uda_type=UdaType.NUMERIC,
    label="Hours",
    coefficient=1.0,  # Affects urgency
)
tw.define_uda(estimate)
```

### Date UDA for Milestones

```python
# Define a milestone UDA
milestone = UdaConfig(
    name="milestone",
    uda_type=UdaType.DATE,
    label="Milestone Date",
)
tw.define_uda(milestone)
```

## Using UDAs in Tasks

### Creating Tasks with UDA Values

```python
from taskwarrior import TaskInputDTO

# Create a task with UDA values
task = TaskInputDTO(
    description="Fix critical bug",
    project="backend",
    udas={"severity": "critical", "estimate": 4},
)
added = tw.add_task(task)
```

### Reading UDA Values from Tasks

```python
# Read UDA values from a task
task = tw.get_task(uuid)
severity = task.get_uda("severity")  # "critical"
estimate = task.get_uda("estimate", default=0)  # 4
milestone = task.get_uda("milestone")  # None if not set
```

### Update and Delete UDAs

```python
# Update UDA
severity_updated = UdaConfig(name="severity", uda_type=UdaType.STRING, label="Severity", default="low")
tw.update_uda(severity_updated)

# Delete UDA
tw.delete_uda(severity)
```

## Listing and Managing UDAs

### Get All Defined UDA Names

```python
# Get all defined UDA names
names = tw.get_uda_names()
print(names)  # {"severity", "estimate", "milestone"}
```

### Get Configuration for a Specific UDA

```python
# Get configuration for a specific UDA
config = tw.get_uda_config("severity")
if config:
    print(config.uda_type)    # UdaType.STRING
    print(config.values)  # ["low", "medium", "high", "critical"]
```

### Reloading UDAs

If UDAs are modified externally, reload them:

```python
tw.reload_udas()
```

## UDA Best Practices

### Define UDAs Early

```python
# Define all UDAs at the beginning of your application
def setup_udas(tw):
    # Severity UDA
    severity = UdaConfig(
        name="severity",
        uda_type=UdaType.STRING,
        label="Severity",
        values=["low", "medium", "high", "critical"],
        default="medium",
    )
    
    # Estimate UDA
    estimate = UdaConfig(
        name="estimate",
        uda_type=UdaType.NUMERIC,
        label="Hours",
        coefficient=1.0,
    )
    
    tw.define_uda(severity)
    tw.define_uda(estimate)
```

### Use Descriptive Names

```python
# Good descriptive names
tw.define_uda(UdaConfig(name="priority", uda_type=UdaType.STRING, label="Priority"))
tw.define_uda(UdaConfig(name="risk", uda_type=UdaType.STRING, label="Risk Level"))

# Less descriptive names
tw.define_uda(UdaConfig(name="p", uda_type=UdaType.STRING, label="Priority"))
tw.define_uda(UdaConfig(name="r", uda_type=UdaType.STRING, label="Risk"))
```

### Set Appropriate Defaults

```python
# Set sensible defaults for your UDAs
severity = UdaConfig(
    name="severity",
    uda_type=UdaType.STRING,
    label="Severity",
    values=["low", "medium", "high", "critical"],
    default="medium",  # Good default
)

estimate = UdaConfig(
    name="estimate",
    uda_type=UdaType.NUMERIC,
    label="Hours",
    coefficient=1.0,
    default=0,  # Good default for time estimates
)
```

## Custom Field Patterns

### Status Tracking UDA

```python
# Create a status tracking UDA for project management
status_tracking = UdaConfig(
    name="status",
    uda_type=UdaType.STRING,
    label="Status",
    values=["planning", "in-progress", "review", "completed"],
    default="planning",
)
tw.define_uda(status_tracking)

# Use in tasks
task = TaskInputDTO(
    description="Design system architecture",
    udas={"status": "in-progress"}
)
```

### Resource Allocation UDA

```python
# Create a resource allocation UDA
resource = UdaConfig(
    name="resource",
    uda_type=UdaType.STRING,
    label="Resource",
    values=["developer", "designer", "manager", "qa"],
    default="developer",
)
tw.define_uda(resource)

# Use in tasks
task = TaskInputDTO(
    description="Implement user authentication",
    udas={"resource": "developer"}
)
```

### Budget Tracking UDA

```python
# Create a budget tracking UDA
budget = UdaConfig(
    name="budget",
    uda_type=UdaType.NUMERIC,
    label="Budget (USD)",
    coefficient=1.0,
)
tw.define_uda(budget)

# Use in tasks
task = TaskInputDTO(
    description="Purchase new equipment",
    udas={"budget": 1500}
)
```

## Related Documentation

- [Task Management Patterns](llms-task-patterns.md) - Common patterns for task management
- [Context Workflows](llms-contexts.md) - Advanced context usage
- [Recurring Tasks Strategy](llms-recurring.md) - Managing recurring workflows
- [Task Dependencies](llms-dependencies.md) - Complex task relationships
