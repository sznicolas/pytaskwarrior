# Error Handling

Effective error handling is crucial for robust task management applications using pytaskwarrior.

## Exception Handling Patterns

### Basic Exception Handling

```python
from taskwarrior.exceptions import (
    TaskWarriorError,
    TaskNotFound,
    TaskValidationError
)

try:
    task = tw.get_task("nonexistent-uuid")
except TaskNotFound:
    print("Task not found")
except TaskValidationError as e:
    print(f"Invalid data: {e}")
except TaskWarriorError as e:
    print(f"TaskWarrior error: {e}")
```

### Comprehensive Error Handling

```python
import logging
from taskwarrior.exceptions import (
    TaskWarriorError,
    TaskNotFound,
    TaskValidationError
)

logger = logging.getLogger(__name__)

def safe_task_operation(tw, operation_func, *args, **kwargs):
    """Wrapper for safe task operations with comprehensive error handling"""
    try:
        return operation_func(*args, **kwargs)
    except TaskNotFound as e:
        logger.warning(f"Task not found: {e}")
        return None
    except TaskValidationError as e:
        logger.error(f"Task validation error: {e}")
        raise
    except TaskWarriorError as e:
        logger.error(f"TaskWarrior error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

# Usage
task = safe_task_operation(tw, tw.get_task, "nonexistent-uuid")
```

## Validation Error Recovery

### Handling Invalid Task Data

```python
from taskwarrior import TaskInputDTO
from taskwarrior.exceptions import TaskValidationError

def create_task_safely(tw, task_data):
    """Create a task with validation error recovery"""
    try:
        task = TaskInputDTO(**task_data)
        return tw.add_task(task)
    except TaskValidationError as e:
        # Log the validation error
        print(f"Validation failed: {e}")
        
        # Try to fix common issues
        if 'description' not in task_data:
            task_data['description'] = "Unnamed Task"
        
        # Retry with fixed data
        try:
            task = TaskInputDTO(**task_data)
            return tw.add_task(task)
        except TaskValidationError as e2:
            print(f"Still failed after fix: {e2}")
            raise

# Usage
task_data = {
    "priority": "H",
    # Missing description - will be auto-fixed
}
task = create_task_safely(tw, task_data)
```

### Data Sanitization

```python
def sanitize_task_data(task_data):
    """Sanitize task data before creating tasks"""
    sanitized = task_data.copy()
    
    # Ensure description exists
    if not sanitized.get('description'):
        sanitized['description'] = "Unnamed Task"
    
    # Validate priority
    valid_priorities = ['H', 'M', 'L', None]
    if sanitized.get('priority') not in valid_priorities:
        sanitized['priority'] = None
    
    # Validate tags
    if 'tags' in sanitized and not isinstance(sanitized['tags'], list):
        sanitized['tags'] = []
    
    return sanitized

# Usage
raw_data = {"priority": "H", "project": "work"}
sanitized_data = sanitize_task_data(raw_data)
task = TaskInputDTO(**sanitized_data)
```

## Task Not Found Scenarios

### Graceful Handling of Missing Tasks

```python
def get_or_create_task(tw, task_uuid, fallback_description):
    """Get a task or create it if it doesn't exist"""
    try:
        return tw.get_task(task_uuid)
    except TaskNotFound:
        print(f"Task {task_uuid} not found, creating new one")
        task = TaskInputDTO(description=fallback_description)
        return tw.add_task(task)

# Usage
task = get_or_create_task(tw, "some-uuid", "Fallback task")
```

### Task Existence Checking

```python
def task_exists(tw, task_uuid):
    """Check if a task exists without raising exceptions"""
    try:
        tw.get_task(task_uuid)
        return True
    except TaskNotFound:
        return False

# Usage
if task_exists(tw, "some-uuid"):
    print("Task exists")
else:
    print("Task does not exist")
```

## Error Logging Strategies

### Structured Error Logging

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def log_task_error(operation, error, task_uuid=None):
    """Log task-related errors with structured information"""
    error_info = {
        'timestamp': datetime.now().isoformat(),
        'operation': operation,
        'error_type': type(error).__name__,
        'error_message': str(error),
        'task_uuid': task_uuid
    }
    
    if isinstance(error, TaskValidationError):
        logger.error(f"Task validation error: {error_info}")
    elif isinstance(error, TaskNotFound):
        logger.warning(f"Task not found: {error_info}")
    else:
        logger.error(f"TaskWarrior error: {error_info}")

# Usage
try:
    tw.get_task("nonexistent-uuid")
except TaskWarriorError as e:
    log_task_error("get_task", e, "nonexistent-uuid")
```

### Error Recovery with Retry Logic

```python
import time
from taskwarrior.exceptions import TaskWarriorError

def retry_operation(operation, max_retries=3, delay=1):
    """Retry an operation with exponential backoff"""
    for attempt in range(max_retries):
        try:
            return operation()
        except TaskWarriorError as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff

# Usage
def get_task_with_retry(tw, uuid):
    return retry_operation(lambda: tw.get_task(uuid))

try:
    task = get_task_with_retry(tw, "some-uuid")
except TaskWarriorError as e:
    print(f"Failed after retries: {e}")
```

## Graceful Degradation

### Fallback Behavior

```python
def get_tasks_with_fallback(tw, filter_string=None):
    """Get tasks with fallback behavior"""
    try:
        return tw.get_tasks(filter_string)
    except TaskWarriorError as e:
        logger.error(f"Failed to get tasks: {e}")
        # Fallback to all tasks
        try:
            return tw.get_tasks()
        except TaskWarriorError:
            # Even fallback failed, return empty list
            logger.error("Even fallback failed")
            return []

# Usage
tasks = get_tasks_with_fallback(tw, "project:work")
```

### Partial Success Handling

```python
def batch_process_tasks(tw, task_list):
    """Process a list of tasks with partial success handling"""
    successful = []
    failed = []
    
    for task_data in task_list:
        try:
            task = TaskInputDTO(**task_data)
            tw.add_task(task)
            successful.append(task_data)
        except Exception as e:
            logger.error(f"Failed to create task {task_data}: {e}")
            failed.append((task_data, str(e)))
    
    return successful, failed

# Usage
tasks_to_create = [
    {"description": "Task 1"},
    {"description": "Task 2"},
    # ... more tasks
]
successful, failed = batch_process_tasks(tw, tasks_to_create)
print(f"Created {len(successful)} tasks, failed {len(failed)}")
```
