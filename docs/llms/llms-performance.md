# Performance Tips

Optimizing pytaskwarrior usage can significantly improve application responsiveness and efficiency.

## Batch Operation Optimization

### Efficient Task Creation

```python
from taskwarrior import TaskWarrior, TaskInputDTO

tw = TaskWarrior()

# Instead of creating tasks one by one
tasks_to_create = [
    TaskInputDTO(description="Task 1", project="work"),
    TaskInputDTO(description="Task 2", project="work"),
    TaskInputDTO(description="Task 3", project="work")
]

# Create all tasks in a batch
for task in tasks_to_create:
    tw.add_task(task)

# Or use bulk operations if available
# (This would depend on the underlying TaskWarrior implementation)
```

### Batch Task Updates

```python
from taskwarrior import task_output_to_input

def batch_update_tasks(tw, tasks_data):
    """Update multiple tasks efficiently"""
    for task_data in tasks_data:
        try:
            # Get the current task
            task = tw.get_task(task_data['uuid'])
            
            # Convert to input DTO
            input_dto = task_output_to_input(task)
            
            # Apply changes
            if 'priority' in task_data:
                input_dto.priority = task_data['priority']
            if 'tags' in task_data:
                input_dto.tags = task_data['tags']
            
            # Save changes
            tw.modify_task(input_dto, task_data['uuid'])
        except Exception as e:
            print(f"Failed to update task {task_data['uuid']}: {e}")

# Usage
tasks_to_update = [
    {'uuid': 'task-1', 'priority': 'H'},
    {'uuid': 'task-2', 'tags': ['urgent', 'review']},
]
batch_update_tasks(tw, tasks_to_update)
```

## Filter Performance Tips

### Efficient Filtering Strategies

```python
# Good - use specific filters that leverage indexes
tasks = tw.get_tasks("project:work and status:pending")

# Avoid - complex filters that may be slow
tasks = tw.get_tasks("project:work and (priority:H or priority:M) and not +done")

# Better - break complex filters into steps
work_tasks = tw.get_tasks("project:work")
filtered_tasks = [t for t in work_tasks if t.priority in ['H', 'M']]
```

### Pre-filtering for Complex Queries

```python
def get_complex_filtered_tasks(tw, project=None, priority=None):
    """Optimize complex filtering by pre-filtering"""
    
    # Start with a broad filter
    base_filter = "status:pending"
    
    if project:
        base_filter += f" and project:{project}"
    
    # Get all matching tasks
    all_tasks = tw.get_tasks(base_filter)
    
    # Apply additional filtering in memory if needed
    filtered_tasks = all_tasks
    
    if priority:
        filtered_tasks = [t for t in filtered_tasks if t.priority == priority]
    
    return filtered_tasks

# Usage
tasks = get_complex_filtered_tasks(tw, project="work", priority="H")
```

## Caching Strategies

### Task Result Caching

```python
import time
from functools import lru_cache

class CachedTaskWarrior:
    def __init__(self, tw):
        self.tw = tw
        self._task_cache = {}
        self._cache_timeout = 300  # 5 minutes
    
    @lru_cache(maxsize=128)
    def get_tasks_cached(self, filter_string=""):
        """Cached version of get_tasks"""
        return self.tw.get_tasks(filter_string)
    
    def get_task_cached(self, uuid):
        """Cached version of get_task"""
        # Simple in-memory cache
        if uuid in self._task_cache:
            cached, timestamp = self._task_cache[uuid]
            if time.time() - timestamp < self._cache_timeout:
                return cached
        
        # Fetch from TaskWarrior
        task = self.tw.get_task(uuid)
        self._task_cache[uuid] = (task, time.time())
        return task

# Usage
cached_tw = CachedTaskWarrior(tw)
tasks = cached_tw.get_tasks_cached("project:work")
```

### Context Caching

```python
class ContextCachedTaskWarrior:
    def __init__(self, tw):
        self.tw = tw
        self._context_cache = {}
    
    def get_contexts_cached(self):
        """Cache context list"""
        if 'contexts' not in self._context_cache:
            contexts = self.tw.get_contexts()
            self._context_cache['contexts'] = contexts
            return contexts
        return self._context_cache['contexts']
    
    def apply_context_cached(self, context_name):
        """Apply context with caching"""
        # In a real implementation, you might want to cache the current context
        return self.tw.apply_context(context_name)
```

## Large Dataset Handling

### Pagination for Large Task Lists

```python
def get_all_tasks_paginated(tw, page_size=100):
    """Get all tasks in pages to avoid memory issues"""
    all_tasks = []
    offset = 0
    
    while True:
        # Get a page of tasks
        page_tasks = tw.get_tasks(f"limit:{page_size} offset:{offset}")
        
        # Add to our collection
        all_tasks.extend(page_tasks)
        
        # If we got fewer tasks than requested, we're done
        if len(page_tasks) < page_size:
            break
            
        # Move to next page
        offset += page_size
    
    return all_tasks

# Usage
all_tasks = get_all_tasks_paginated(tw)
```

### Memory-Efficient Task Processing

```python
def process_tasks_efficiently(tw, filter_string):
    """Process tasks without loading all into memory at once"""
    
    # Get tasks in batches
    batch_size = 50
    offset = 0
    
    while True:
        batch = tw.get_tasks(f"{filter_string} limit:{batch_size} offset:{offset}")
        
        if not batch:
            break
            
        # Process this batch
        for task in batch:
            # Do your processing here
            print(f"Processing: {task.description}")
            
        offset += batch_size

# Usage
process_tasks_efficiently(tw, "status:pending")
```

## Command Execution Efficiency

### Minimize External Calls

```python
# Good - minimize calls to TaskWarrior
def get_task_summary(tw):
    """Get summary of tasks with minimal calls"""
    
    # Get all pending tasks in one call
    tasks = tw.get_tasks("status:pending")
    
    # Process in memory
    summary = {
        'total': len(tasks),
        'high_priority': len([t for t in tasks if t.priority == 'H']),
        'by_project': {}
    }
    
    for task in tasks:
        project = task.project or 'unassigned'
        summary['by_project'][project] = summary['by_project'].get(project, 0) + 1
    
    return summary

# Usage
summary = get_task_summary(tw)
print(f"Total tasks: {summary['total']}")
```

### Batch Commands

```python
def batch_complete_tasks(tw, task_uuids):
    """Complete multiple tasks efficiently"""
    
    # Instead of calling done_task for each task
    # You could potentially batch these operations
    
    completed = []
    for uuid in task_uuids:
        try:
            tw.done_task(uuid)
            completed.append(uuid)
        except Exception as e:
            print(f"Failed to complete task {uuid}: {e}")
    
    return completed

# Usage
task_uuids = ["task1", "task2", "task3"]
completed = batch_complete_tasks(tw, task_uuids)
```

### Connection Pooling (if applicable)

```python
class OptimizedTaskWarrior:
    def __init__(self):
        # Reuse TaskWarrior instance instead of creating new ones
        self.tw = TaskWarrior()
    
    def get_tasks_optimized(self, filter_string=""):
        """Optimized task retrieval"""
        return self.tw.get_tasks(filter_string)
    
    def add_task_optimized(self, task):
        """Optimized task creation"""
        return self.tw.add_task(task)
```

## Monitoring and Profiling

### Performance Monitoring

```python
import time
from functools import wraps

def monitor_performance(func):
    """Decorator to monitor function performance"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.2f} seconds")
        return result
    return wrapper

@monitor_performance
def get_work_tasks(tw):
    return tw.get_tasks("project:work")

# Usage
tasks = get_work_tasks(tw)
```

### Memory Usage Monitoring

```python
import psutil
import os

def monitor_memory_usage():
    """Monitor current memory usage"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")

# Usage
monitor_memory_usage()
```
```