# pytaskwarrior
## Description
Automate your TaskWarrior interactions with this wrapper.

## Installation
```bash
pip install pytaskwarrior
```

## Use `taskwarrior` module
You MUST have a `taskrc` file that is configured to allow `task` command without confirmation. By default `pytaskrc` in the current directory is created and used. You can set TASKRC and TASKDATA in your environment.
```
from taskwarrior import TaskWarrior, Task, Priority

tw = TaskWarrior()
task1 = Task(description='First task')
task1 = tw.add_task(task1) # adds task1 and updates index/uuid fields
task2 = Task(
        description="🆘 Write PyTaskwarrior API documentation",
        due='P1W',
        priority=Priority.HIGH,
        project="pytaskwarrior",
        tags=["docs", "dev"]
)
print(tw.get_tasks(['status:pending']))
tw.add_task(task2)
tw.done_task(task1.uuid)
task1 = tw.get_task(task1.uuid)
print(task1.status)
```

