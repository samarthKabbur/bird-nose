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
ros2 run bird_nose_telemetry record_run <what-you-tested> [topics...]
```

It names the folder `<date>_<time>_<name>` and writes `run_metadata.yaml` beside the recording: Git commit, image digest, robot configuration, scenario and seed, Nav2 parameter revision, times, operator notes, and pass or fail. See [bird_nose_telemetry](../src/bird_nose_telemetry/README.md).

## Limitations

Long-term storage and retention for large recordings is still an open decision in the living doc.

## See also

- [bird_nose_telemetry](../src/bird_nose_telemetry/README.md): MCAP support and Foxglove for reviewing recordings
