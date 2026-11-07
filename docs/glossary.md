# Glossary

Terms used across the Bird Nose repository, in alphabetical order.

| Term | Meaning |
| --- | --- |
| **`base_link`** | The frame fixed to the robot's body. Sensor positions in `robot.yaml` are given relative to it (REP 105). |
| **`br131`** | A software bridge on Nuvo that joins its robot-network Ethernet ports into one network, `192.168.131.0/24`, like a small switch. It only works while Nuvo is running. |
| **CI (continuous integration)** | Checks GitHub runs automatically on every pull request and on `main`: docs, scripts, Compose files, build, and tests. See [ci.md](ci.md). |
| **Clearpath API** | The standard topic and service names Clearpath robots publish under their namespace, such as `platform/cmd_vel` and `platform/odom/filtered`. Simulation and hardware use the same names. |
| **colcon** | ROS 2's build tool. `colcon build` builds every package in `src/`; `colcon test` runs their tests. Output goes to `build/`, `install/`, and `log/`, which Git ignores. |
| **Compose overlay** | An extra Compose file layered on top of `compose.yaml` with a second `-f`, such as `compose.nvidia.yaml`. Not the same as a workspace overlay. |
| **Compose profile** | A label that switches on a group of services, such as `--profile sim`. Services without a profile (`dev`) always start. |
| **Container** | A running instance of an image, isolated from the host but sharing its kernel. Changes made only inside a container are lost when it is removed. |
| **Dependabot** | A GitHub service that opens pull requests to update dependencies. Here it updates the GitHub Actions the workflows use, once a month. |
| **Dev container** | VS Code's feature for working inside a container. Ours uses the `dev` service. |
| **Digest** | A content hash (`sha256:…`) that names exactly one image. A tag like `jazzy` can be moved to a new image; a digest cannot, so pinning to a digest makes builds reproducible. |
| **Discovery range** | How far ROS 2 looks for other nodes: `LOCALHOST` (this computer only) or `SUBNET` (the local network). Set by `ROS_AUTOMATIC_DISCOVERY_RANGE`. |
| **Domain ID** | A number (`ROS_DOMAIN_ID`) that splits ROS 2 traffic into separate channels. Nodes on different domains never see each other: Bird Nose uses 0 for the robot and 42 for simulation. |
| **Fast DDS** | The middleware implementation (`rmw_fastrtps_cpp`) Bird Nose uses everywhere. Every computer that should talk must use the same one. |
| **Frame** | A named coordinate system, such as `map`, `odom`, or `base_link`. TF tracks how frames relate over time. |
| **Generators (Clearpath)** | Clearpath tools that read `robot.yaml` and write the robot model, launch files, and parameters into the setup folder next to it. |
| **Image** | A packaged file system with everything needed to run software. Built from a Dockerfile; started as a container. |
| **Launch file** | A Python file that starts nodes with their parameters. `ros2 launch <package> <file> --show-args` lists its arguments. |
| **MCAP** | The recording format for ROS 2 bags. Viewable in Foxglove. |
| **Namespace** | A prefix on every topic, service, and node name. The robot's is `/Nuvo_7100VTC_Series`, set in `robot.yaml`. |
| **Nav2** | The ROS 2 navigation stack: localization, path planning, control, and obstacle avoidance. |
| **Node** | One ROS 2 program (a process or part of one) that publishes, subscribes, or offers services. |
| **Parameter descriptor** | Metadata declared with a parameter: description, range, and read-only flag. `ros2 param describe` shows it. |
| **QoS** | Quality of Service: settings such as reliability and history depth that publishers and subscribers must agree on. Sensor data usually uses "best effort". |
| **REP** | ROS Enhancement Proposal, a ROS convention document. REP 103 sets units (metres, seconds, radians) and axis directions; REP 105 names standard frames. |
| **`robot.yaml`** | Clearpath's single description of a robot: platform, attachments, sensors, namespace, middleware. Ours is in `config/robots/husky-a200/`. |
| **Self-hosted runner** | A GitHub program installed on a team computer that runs workflow jobs there instead of on GitHub's machines. Bird Nose uses one only for the manually started simulation test. |
| **Setup path** | The folder holding `robot.yaml` that Clearpath's generators write into: `/etc/clearpath/` on the robot, `~/.bird_nose/sim_setup/` in simulation. |
| **Sim time** | Using Gazebo's `/clock` topic instead of the wall clock, so nodes stay in step with the simulation when it runs slower or faster than real time (`use_sim_time:=true`). |
| **SLAM** | Simultaneous localization and mapping: building a map while working out where the robot is in it. |
| **TF** | ROS's transform system, which publishes how frames relate (topics `tf` and `tf_static`). |
| **udev rule** | A host rule that gives a device a stable name, such as `/dev/microstrain_rtk`. Rules run on the host, never in containers. |
| **Volume** | Storage Docker keeps outside a container so it survives restarts, such as `bird-nose-sim-setup`. |
| **Workflow (GitHub Actions)** | A YAML file in `.github/workflows/` that tells GitHub which jobs to run and when, such as on every pull request. |
| **Workspace overlay** | Sourcing `install/setup.bash` on top of `/opt/ros/jazzy`, so our packages are found alongside the system's. Not the same as a Compose overlay. |
| **WSL2 / WSLg** | Windows Subsystem for Linux: runs a real Ubuntu inside Windows. WSLg is its built-in display support, which shows Linux GUI windows such as Gazebo and RViz on the Windows desktop. A supported development host for Bird Nose. |
