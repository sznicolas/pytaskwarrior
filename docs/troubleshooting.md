# Troubleshooting

Common issues and solutions when using `pytaskwarrior`.

---

## `task` binary not found

**Error:**
```
FileNotFoundError: [Errno 2] No such file or directory: 'task'
```

**Cause:** TaskWarrior is not installed or not on `PATH`.

**Fix:**

```bash
# macOS
brew install task

# Ubuntu / Debian
sudo apt install taskwarrior

# Verify
task --version
```

If `task` is installed in a non-standard location, pass the path explicitly:

```python
tw = TaskWarrior(task_cmd="/usr/local/bin/task")
```

---

## Wrong Python or TaskWarrior version

**Symptom:** Unexpected errors or missing features.

**Requirements:**
- Python ≥ 3.12
- TaskWarrior ≥ 3.0

```bash
python --version
task --version
```

---

## UDA not appearing on tasks

**Symptom:** `task.get_uda("my_field")` always returns `None`.

**Causes and fixes:**

1. **UDA not registered** — the UDA must be declared before creating tasks:

    ```python
    from taskwarrior import TaskWarrior, UdaConfig, UdaType

    tw = TaskWarrior()
    cfg = UdaConfig(name="severity", type=UdaType.STRING, label="Severity")
    tw.define_uda(cfg)
    ```

2. **Task created before the UDA was defined** — re-add the UDA config and verify with `tw.get_uda_config("severity")`.

3. **Wrong field name** — UDA names are case-sensitive and must match the name used in `UdaConfig`.

---

## `get_tasks()` returns an empty list

**Symptom:** No tasks returned even though `task list` shows tasks in the terminal.

**Causes and fixes:**

1. **Active context filtering** — if a context is active, it filters all queries:

    ```python
    tw.clear_context()  # remove the active context
    tasks = tw.get_tasks()
    ```

2. **Wrong `data_location`** — `TaskWarrior` was instantiated with a different data directory than your terminal:

    ```python
    tw = TaskWarrior(data_location="~/.task")  # match your actual data path
    ```

3. **Filter too restrictive** — check the filter string:

    ```python
    tasks = tw.get_tasks(filter_str="status:pending")
    ```

---

## Import error: `ModuleNotFoundError: No module named 'taskwarrior'`

**Fix:** Install the package:

```bash
pip install pytaskwarrior
```

Note: the **pip package** is named `pytaskwarrior`, but the **Python import** is `taskwarrior`:

```python
from taskwarrior import TaskWarrior  # correct
from pytaskwarrior import TaskWarrior  # wrong
```

---

## `AnnotationDTO` or `ContextDTO` not found

These types are part of the public API since v1.0.0. Import from the top-level package:

```python
from taskwarrior import AnnotationDTO, ContextDTO
```

If you get an `ImportError`, upgrade to the latest version:

```bash
pip install --upgrade pytaskwarrior
```

---

## Version shows `0.0.0` or old version

**Cause:** The package was not reinstalled after a version bump in `pyproject.toml`.

**Fix:**

```bash
pip install -e .   # editable install
# or with uv
uv pip install -e .
```

---

## Still stuck?

- Open an issue on [GitHub](https://github.com/nschmeltz/pytaskwarrior/issues)
- Check the [API reference](api/taskwarrior.md) for correct method signatures
