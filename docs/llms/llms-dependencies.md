# Task Dependencies

Task dependencies in pytaskwarrior allow you to create complex workflows where tasks must be completed in a specific order.

## Task Dependency Creation

### Basic Dependency Setup

```python
from taskwarrior import TaskWarrior, TaskInputDTO

tw = TaskWarrior()

# Create tasks
task1 = tw.add_task(TaskInputDTO(description="Design API"))
task2 = tw.add_task(TaskInputDTO(description="Implement API"))
task3 = tw.add_task(TaskInputDTO(description="Write tests"))

# Create dependent task
dependent = TaskInputDTO(
    description="Deploy to production",
    depends=[task1.uuid, task2.uuid, task3.uuid],
)
tw.add_task(dependent)
```

### Dependency with Multiple Tasks

```python
# Create a complex workflow
design = tw.add_task(TaskInputDTO(description="UI Design"))
development = tw.add_task(TaskInputDTO(description="Backend Development"))
testing = tw.add_task(TaskInputDTO(description="Quality Assurance"))
deployment = tw.add_task(TaskInputDTO(
    description="Production Deployment",
    depends=[design.uuid, development.uuid, testing.uuid]
))
```

## Dependency Visualization

### Checking Dependencies

```python
# Get a task with dependencies
task = tw.get_task(uuid)

# View direct dependencies
if task.depends:
    print("Direct dependencies:")
    for dep_uuid in task.depends:
        dep_task = tw.get_task(dep_uuid)
        print(f"  - {dep_task.description}")
```

### Dependency Chain Analysis

```python
def get_dependency_chain(tw, task_uuid):
    """Get the full dependency chain for a task"""
    task = tw.get_task(task_uuid)
    chain = [task.description]
    
    if task.depends:
        for dep_uuid in task.depends:
            chain.extend(get_dependency_chain(tw, dep_uuid))
    
    return chain

# Usage
chain = get_dependency_chain(tw, "production-deployment-uuid")
print("Dependency chain:", " -> ".join(chain))
```

## Chain Task Management

### Creating Sequential Workflows

```python
# Create a sequential workflow for a project
def create_project_workflow(tw, project_name):
    # Phase 1: Research
    research = tw.add_task(TaskInputDTO(
        description=f"{project_name} - Research Phase",
        project=project_name
    ))
    
    # Phase 2: Design
    design = tw.add_task(TaskInputDTO(
        description=f"{project_name} - Design Phase",
        project=project_name,
        depends=[research.uuid]
    ))
    
    # Phase 3: Implementation
    implementation = tw.add_task(TaskInputDTO(
        description=f"{project_name} - Implementation Phase",
        project=project_name,
        depends=[design.uuid]
    ))
    
    # Phase 4: Testing
    testing = tw.add_task(TaskInputDTO(
        description=f"{project_name} - Testing Phase",
        project=project_name,
        depends=[implementation.uuid]
    ))
    
    # Phase 5: Deployment
    deployment = tw.add_task(TaskInputDTO(
        description=f"{project_name} - Deployment",
        project=project_name,
        depends=[testing.uuid]
    ))
    
    return {
        'research': research,
        'design': design,
        'implementation': implementation,
        'testing': testing,
        'deployment': deployment
    }

# Usage
workflow = create_project_workflow(tw, "NewFeature")
```

### Managing Parallel Tasks

```python
# Create tasks that can run in parallel but must all complete before the final task
def create_parallel_workflow(tw, project_name):
    # Parallel tasks
    task1 = tw.add_task(TaskInputDTO(
        description=f"{project_name} - Task 1",
        project=project_name
    ))
    
    task2 = tw.add_task(TaskInputDTO(
        description=f"{project_name} - Task 2",
        project=project_name
    ))
    
    task3 = tw.add_task(TaskInputDTO(
        description=f"{project_name} - Task 3",
        project=project_name
    ))
    
    # Final task that depends on all three
    final = tw.add_task(TaskInputDTO(
        description=f"{project_name} - Final Task",
        project=project_name,
        depends=[task1.uuid, task2.uuid, task3.uuid]
    ))
    
    return {
        'task1': task1,
        'task2': task2,
        'task3': task3,
        'final': final
    }
```

## Dependency Validation

### Checking Task Status Before Completion

```python
def can_complete_task(tw, task_uuid):
    """Check if all dependencies are completed"""
    task = tw.get_task(task_uuid)
    
    if not task.depends:
        return True
    
    for dep_uuid in task.depends:
        dep_task = tw.get_task(dep_uuid)
        if dep_task.status != 'completed':
            return False
    
    return True

# Usage
if can_complete_task(tw, "dependent-task-uuid"):
    tw.done_task("dependent-task-uuid")
else:
    print("Cannot complete task - dependencies not met")
```

### Dependency Chain Validation

```python
def validate_dependency_chain(tw, task_uuid):
    """Validate that a task's dependency chain is valid"""
    try:
        task = tw.get_task(task_uuid)
        
        # Check if dependencies exist
        for dep_uuid in task.depends or []:
            try:
                tw.get_task(dep_uuid)
            except Exception:
                return False, f"Dependency {dep_uuid} not found"
        
        # Check for circular dependencies (simplified)
        visited = set()
        def check_circular(uuid):
            if uuid in visited:
                return True
            visited.add(uuid)
            
            task = tw.get_task(uuid)
            if task.depends:
                for dep_uuid in task.depends:
                    if check_circular(dep_uuid):
                        return True
            return False
        
        if check_circular(task_uuid):
            return False, "Circular dependency detected"
        
        return True, "Valid dependency chain"
    
    except Exception as e:
        return False, f"Validation error: {str(e)}"

# Usage
is_valid, message = validate_dependency_chain(tw, "task-uuid")
print(f"Validation: {message}")
```

## Complex Workflow Patterns

### Multi-Level Dependencies

```python
# Create a multi-level dependency structure
def create_complex_workflow(tw):
    # Level 1: Research and Planning
    research = tw.add_task(TaskInputDTO(description="Research"))
    planning = tw.add_task(TaskInputDTO(description="Planning"))
    
    # Level 2: Design and Development
    design = tw.add_task(TaskInputDTO(
        description="Design",
        depends=[research.uuid]
    ))
    
    development = tw.add_task(TaskInputDTO(
        description="Development",
        depends=[planning.uuid]
    ))
    
    # Level 3: Testing and Deployment
    testing = tw.add_task(TaskInputDTO(
        description="Testing",
        depends=[design.uuid, development.uuid]
    ))
    
    deployment = tw.add_task(TaskInputDTO(
        description="Deployment",
        depends=[testing.uuid]
    ))
    
    return {
        'research': research,
        'planning': planning,
        'design': design,
        'development': development,
        'testing': testing,
        'deployment': deployment
    }
```

### Conditional Dependencies

```python
# Create a workflow where some dependencies are conditional
def create_conditional_workflow(tw):
    # Base tasks
    base_task = tw.add_task(TaskInputDTO(description="Base Task"))
    
    # Conditional tasks
    conditional_task1 = tw.add_task(TaskInputDTO(
        description="Conditional Task 1",
        depends=[base_task.uuid]
    ))
    
    conditional_task2 = tw.add_task(TaskInputDTO(
        description="Conditional Task 2",
        depends=[base_task.uuid]
    ))
    
    # Final task that depends on both conditional tasks
    final = tw.add_task(TaskInputDTO(
        description="Final Task",
        depends=[conditional_task1.uuid, conditional_task2.uuid]
    ))
    
    return {
        'base': base_task,
        'conditional1': conditional_task1,
        'conditional2': conditional_task2,
        'final': final
    }
```

## Related Documentation

- [Task Management Patterns](llms-task-patterns.md) - Common patterns for task management
- [Context Workflows](llms-contexts.md) - Advanced context usage
- [Recurring Tasks Strategy](llms-recurring.md) - Managing recurring workflows
