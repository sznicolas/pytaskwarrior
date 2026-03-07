# Tips and Tricks

## Change a root project name

```bash
❯ task proj:old_project

ID Projet            Duration Description                   
12 old_project.init      PT1H review the error logs         
13 old_project.debug     PT1H try to isolate the failure    
14 old_project.fix       PT1H review the global architecture
15 old_project.fix       PT1H implement a fix               

4 tasks
```

```python
from taskwarrior import TaskWarrior, TaskInputDTO

tw = TaskWarrior()

for task in tw.get_tasks('project:old_project'):
    new_project_name = task.project.replace('old_project', 'legacy_management')
    updated_task = TaskInputDTO(project=new_project_name)
    tw.modify_task(updated_task, task.uuid)
```

```bash
❯ task proj:legacy_management

ID Projet                  Duration Description                   
12 legacy_management.init      PT1H review the error logs         
13 legacy_management.debug     PT1H try to isolate the failure    
14 legacy_management.fix       PT1H review the global architecture
15 legacy_management.fix       PT1H implement a fix

4 tasks
```
