# pytaskwarrior
Python module wrapping Taskwarrior. Tested with task >=3.4

## Getting started
As this is a wrapper, you must have a `task` command installed. So [install it](https://taskwarrior.org/download/) or build it since the debian available package is an old one (2.6.2).

### Build taskwarrior latest stable

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

## Use `taskwarrior` module
```
from taskwarrior import TaskWarrior, Task

tw = TaskWarrior()
task = Task(description='First task')
tw.add_task(task)
print(tw.get_tasks())
```
