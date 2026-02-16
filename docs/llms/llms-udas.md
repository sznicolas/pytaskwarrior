# UDA Implementation

User Defined Attributes (UDAs) extend TaskWarrior with custom fields to meet specific project needs.

## UDA Definition Examples

### String UDA with Allowed Values

```python
from taskwarrior import TaskWarrior
from taskwarrior.dto.uda_dto import UdaConfig, UdaType

tw = TaskWarrior()

# Define a severity UDA
severity = UdaConfig(
    name="severity",
    type=UdaType.STRING,
    label="Severity",
    values=["low", "medium", "high", "critical"],
    default="medium",
)
tw.uda_service.define_uda(severity)
```

### Numeric UDA for Time Estimates

```python
# Define an estimate UDA
estimate = UdaConfig(
    name="estimate",
    type=UdaType.NUMERIC,
    label="Hours",
    coefficient=1.0,  # Affects urgency
)
tw.uda_service.define_uda(estimate)
```

### Date UDA for Milestones

```python
# Define a milestone UDA
milestone = UdaConfig(
    name="milestone",
    type=UdaType.DATE,
    label="Milestone Date",
)
tw.uda_service.define_uda(milestone)
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
    print(config.type)    # UdaType.STRING
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
        type=UdaType.STRING,
        label="Severity",
        values=["low", "medium", "high", "critical"],
        default="medium",
    )
    
    # Estimate UDA
    estimate = UdaConfig(
        name="estimate",
        type=UdaType.NUMERIC,
        label="Hours",
        coefficient=1.0,
    )
    
    tw.uda_service.define_uda(severity)
    tw.uda_service.define_uda(estimate)
```

### Use Descriptive Names

```python
# Good descriptive names
tw.uda_service.define_uda(UdaConfig(name="priority", type=UdaType.STRING, label="Priority"))
tw.uda_service.define_uda(UdaConfig(name="risk", type=UdaType.STRING, label="Risk Level"))

# Less descriptive names
tw.uda_service.define_uda(UdaConfig(name="p", type=UdaType.STRING, label="Priority"))
tw.uda_service.define_uda(UdaConfig(name="r", type=UdaType.STRING, label="Risk"))
```

### Set Appropriate Defaults

```python
# Set sensible defaults for your UDAs
severity = UdaConfig(
    name="severity",
    type=UdaType.STRING,
    label="Severity",
    values=["low", "medium", "high", "critical"],
    default="medium",  # Good default
)

estimate = UdaConfig(
    name="estimate",
    type=UdaType.NUMERIC,
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
    type=UdaType.STRING,
    label="Status",
    values=["planning", "in-progress", "review", "completed"],
    default="planning",
)
tw.uda_service.define_uda(status_tracking)

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
    type=UdaType.STRING,
    label="Resource",
    values=["developer", "designer", "manager", "qa"],
    default="developer",
)
tw.uda_service.define_uda(resource)

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
    type=UdaType.NUMERIC,
    label="Budget (USD)",
    coefficient=1.0,
)
tw.uda_service.define_uda(budget)

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
