# pytaskwarrior
Python module wrapping Taskwarrior.

## Getting started
As this is a wrapper, you must have a `task` command installed. So [install it](https://taskwarrior.org/download/) or build it since the debian available package is an old one (2.6.2).

### Build taskwarrior 3.4.1

Get the [Dockerfile](taskwarrior.bin)

```
cd taskwarrior.bin ; docker build -t taskwarrior_bin .
id=$(docker create taskwarrior_bin)
docker cp $id:/root/code/taskwarrior/build/src/task task
docker rm -v $id
```
### Build for Docker
Clone this repository, then build the docker image:
```
docker build -t pytaskwarrior .
```

Note: The task command should be in taskwarrior.bin, so if it not the case you can either adapt the Dockerfile to install it, or build the `task` command as explained above.

### Run in Docker
```
docker run -it  --rm pytaskwarrior bash
```
Note: For persistency we can mount a volume. The data resides in `./.task`
```
docker run -it  -v $PWD:/tw --rm pytaskwarrior bash
```

### Test it
For now:

- `python test_exec.py`
- `cd .. && pytest`
- `cd - && python # import taskwarrior and play`

## Use `taskwarrior` module
You MUST have a `taskrc` file that is configured to allow `task` command **without confirmation**. By default [this one](src/pytaskrc) is used. You can set TASKRC and TASKDATA in your environment. It's a good practice to use another taskrc than your .taskrc you're using in your CLI.
```
from taskwarrior import TaskWarrior, Task

tw = TaskWarrior()
task = Task(description='First task')
tw.add_task(task)
print(tw.get_tasks())
```
