# Building TaskWarrior 3.x from Source

!!! note "Binary not required by default"
    `TaskWarrior()` uses the **taskchampion backend** by default — no `task` binary needed.
    This guide is only necessary if you want CLI mode (`TaskWarrior(task_cmd="task")`).

If TaskWarrior 3.x is not packaged for your OS and you need CLI mode, you can build it
from source. This guide explains how to build TaskWarrior 3.x using the provided
Dockerfile, ensuring a reproducible and portable build process.

## Prerequisites

- **Docker** (recommended for a consistent build environment)
- Alternatively, for manual builds: CMake (>=3.10), gcc, make, libgnutls28-dev, uuid-dev, Rust

## Building TaskWarrior with Docker

A ready-to-use Dockerfile is provided in `taskwarrior.bin/Dockerfile`. This will build TaskWarrior 3.x and allow you to extract the binary for use on your host system.

### Steps

1. **Build the Docker image:**
   ```bash
   docker build -f taskwarrior.bin/Dockerfile -t taskwarrior-builder .
   ```
2. **Extract the TaskWarrior binary:**
   ```bash
   docker run --rm -v $(pwd):/output taskwarrior-builder cp /root/code/taskwarrior/build/src/task /output/
   ```
   This will copy the compiled `task` binary to your current directory (as `./task`).

3. **Install the binary:**
   Move the `task` binary to a directory in your `PATH`, e.g.:
   ```bash
   sudo mv ./task /usr/local/bin/
   sudo chmod +x /usr/local/bin/task
   ```

## Notes
- The Docker build process ensures all dependencies are correctly installed and the resulting binary is compatible with most modern Linux systems.
- For advanced users, you may customize the Dockerfile or build manually by following the steps inside it.
- For more information, see the official [TaskWarrior repository](https://github.com/GothenburgBitFactory/taskwarrior).
