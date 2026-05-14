# Troubleshooting

Common issues and solutions when using `pytaskwarrior`.

---

## `task` binary not found

Since pytaskwarrior v2.1, the `task` binary is **not required** by default.
`TaskWarrior()` uses the taskchampion backend directly.

If you explicitly pass `task_cmd="task"` and get this error:

```
FileNotFoundError: [Errno 2] No such file or directory: 'task'
```

Either remove the `task_cmd` argument to use the default backend, or install TaskWarrior:

```bash
# macOS
brew install task

# Ubuntu / Debian
sudo apt install taskwarrior

# Non-standard location
tw = TaskWarrior(task_cmd="/usr/local/bin/task")
```

---

## Wrong Python version

**Requirements:**
- Python ≥ 3.12

```bash
python --version  # must be 3.12+
```

---

## `taskchampion-py` not installed or wrong version

**Symptom:** `ModuleNotFoundError: No module named 'taskchampion'`

**Fix:**
```bash
pip install pytaskwarrior  # installs taskchampion-py automatically
# or from source:
uv sync
```

pytaskwarrior requires `taskchampion-py >= 3.0.1.1`.

---

## UDA not appearing on tasks

**Symptom:** `task.get_uda("my_field")` always returns `None`.

1. **UDA not registered** — declare the UDA before creating tasks:

    ```python
    from taskwarrior import TaskWarrior, UdaConfig, UdaType

    tw = TaskWarrior()
    cfg = UdaConfig(name="severity", uda_type=UdaType.STRING, label="Severity")
    tw.define_uda(cfg)
    ```

2. **Task created before the UDA was defined** — re-add the UDA config and verify with `tw.get_uda_config("severity")`.

3. **Wrong field name** — UDA names are case-sensitive and must match the name used in `UdaConfig`.

---

## `get_tasks()` returns an empty list

1. **Active context filtering** — if a context is active, it filters all queries:

    ```python
    tw.unset_context()        # remove the active context
    tasks = tw.get_tasks()
    ```

2. **Wrong `data_location`** — pointing to a different directory:

    ```python
    tw = TaskWarrior(data_location="~/.task")
    ```

3. **Filter too restrictive** — try without a filter first:

    ```python
    tasks = tw.get_tasks()
    ```

---

## OR / AND filters not working

pytaskwarrior's Python filter engine does not support `or`, `and`, or
parenthesised expressions. All tokens are combined with implicit AND.

For complex boolean logic, filter in Python after retrieving tasks:

```python
tasks = tw.get_tasks()
result = [t for t in tasks if "work" in (t.project or "") or "urgent" in (t.tags or [])]
```

---

## Import error: `ModuleNotFoundError: No module named 'taskwarrior'`

```bash
pip install pytaskwarrior
```

Note: the **pip package** is `pytaskwarrior`, but the **Python import** is `taskwarrior`:

```python
from taskwarrior import TaskWarrior  # correct
```

---

## Still stuck?

- Open an issue on [GitHub](https://github.com/sznicolas/pytaskwarrior/issues)
- Check the [API reference](api/taskwarrior.md) for correct method signatures
