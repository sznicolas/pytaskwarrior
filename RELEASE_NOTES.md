# PyTaskWarrior 2.0.0 Release Notes

## Overview

**PyTaskWarrior 2.0.0** is a major release that introduces breaking API changes: the `UdaConfig.type` field has been renamed to `UdaConfig.uda_type`, and `define_context` now accepts a `ContextDTO` instance instead of separate name/read/write parameters. These changes improve API consistency and avoid naming conflicts.

### Key Highlights

- **Breaking Change**: `UdaConfig.type` → `UdaConfig.uda_type`
- **Why**: `type` is a reserved Python keyword and built-in function, causing confusion and potential issues
- **Migration**: Simple find-and-replace: update all instances of `.type=UdaType` to `.uda_type=UdaType` and `.type` to `.uda_type`
- **All 183 tests passing**, 0 failures

---

## What's New in 2.0.0

### Breaking Changes

#### UdaConfig Field Rename

The `type` field in `UdaConfig` has been renamed to `uda_type` to avoid conflicts with Python's built-in `type` function.

**Before (1.x):**
```python
from taskwarrior import UdaConfig, UdaType

uda = UdaConfig(
    name="severity",
    type=UdaType.STRING,  # ❌ Problematic: 'type' is a Python built-in
    label="Severity Level"
)
```

**After (2.0):**
```python
from taskwarrior import UdaConfig, UdaType

uda = UdaConfig(
    name="severity",
    uda_type=UdaType.STRING,  # ✅ Clear and avoids conflicts
    label="Severity Level"
)
```

### Migration Guide

To upgrade from 1.x to 2.0.0:

1. **Update all UdaConfig instantiations:**
   - Replace `type=UdaType.*` with `uda_type=UdaType.*`
   - Example: `UdaConfig(name="x", type=UdaType.STRING)` → `UdaConfig(name="x", uda_type=UdaType.STRING)`

2. **Update all UdaConfig attribute access:**
   - Replace `config.type` with `config.uda_type`
   - Example: `if uda.type == UdaType.STRING:` → `if uda.uda_type == UdaType.STRING:`

3. **No changes needed:**
   - TaskWarrior `.taskrc` config files remain unchanged
   - `UdaType` enum is unchanged
   - All other APIs are unchanged

### Configuration Format Unchanged

The `.taskrc` configuration file format remains the same:
```taskrc
uda.severity.type=string
uda.severity.label=Severity
uda.severity.values=low,medium,high,critical
```

The parser automatically maps the `type` key to the `uda_type` field in `UdaConfig`.

---

## Installation

```bash
pip install pytaskwarrior==2.0.0
```

## Links

- **[CHANGELOG.md](CHANGELOG.md)** – Full release history
- **[README.md](README.md)** – Quick start, API reference, examples
- **[GitHub Issues](https://github.com/sznicolas/pytaskwarrior/issues)** – Bug reports

## Contributors

- Nicolas Schmeltz ([@sznicolas](https://github.com/sznicolas))
- GitHub Copilot (breaking change implementation, test updates, documentation)

---

**v2.0.0** | April 5, 2026
