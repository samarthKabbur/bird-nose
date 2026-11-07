# data

## Purpose

Local storage for run outputs: recordings, logs, and reports. The folder structure is in Git so every checkout has it; the contents are not. Recordings are large and belong in separate storage, not in the repository.

## Contents

| Folder | Holds |
| --- | --- |
| `bags/` | ROS 2 recordings in MCAP format (`.mcap`) |
| `logs/` | Run logs worth keeping briefly |
| `reports/` | Scenario and regression reports (Phase 4) |

Each folder contains only a `.gitkeep` placeholder in Git. `.gitignore` excludes everything else in `data/`, plus any `.mcap`, `.db3`, or `.bag` file anywhere in the repository.

## Usage

Record a run from the dev container (the repository is mounted, so files appear here on the host too):

```bash
ros2 bag record -s mcap -o data/bags/$(date +%F_%H%M)_<what-you-tested> <topics...>
```

Every important run should note: Git commit or tag, image digest, robot configuration, scenario and seed, Nav2 parameter revision, start time and operator notes, and pass or fail.

## Limitations

Long-term storage and retention for large recordings is still an open decision in the living doc.

## See also

- [bird_nose_telemetry](../src/bird_nose_telemetry/README.md): MCAP support and Foxglove for reviewing recordings
