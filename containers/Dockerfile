# Bird Nose development and simulation image.
#
# One image serves every non-robot service (dev, sim, nav2, algorithm,
# telemetry, rviz) so all of them share exactly the same dependencies.
# The base image is pinned by digest: a tag such as "jazzy" can move,
# a digest cannot. Update the digest deliberately, in its own pull request.
#
# Build through Compose (see containers/compose.yaml) rather than by hand,
# so the user ID and group ID match the person running it.

# ros:jazzy-ros-base-noble, digest recorded on bender on 2026-11-06.
ARG BASE_IMAGE=ros:jazzy-ros-base-noble@sha256:8eed0a4669bbf43ee331878a4c39bd8ebddea8e3312a58b4fae8edb14526b617

# ---------------------------------------------------------------------------
# base: ROS 2 Jazzy plus everything needed to run the simulated Husky,
# Nav2, visualization, and telemetry. No build tools, no user account.
# ---------------------------------------------------------------------------
FROM ${BASE_IMAGE} AS base

SHELL ["/bin/bash", "-o", "pipefail", "-c"]
ENV DEBIAN_FRONTEND=noninteractive \
    ROS_DISTRO=jazzy

# Keep images small: never pull in "recommended" extras.
RUN printf 'APT::Install-Recommends "0";\nAPT::Install-Suggests "0";\n' \
      > /etc/apt/apt.conf.d/01norecommend

# Clearpath's package server provides the Jazzy Husky simulation and
# description packages (same source Clearpath's own images use).
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl gnupg lsb-release \
 && mkdir -p /etc/apt/keyrings \
 && curl -fsSL https://packages.clearpathrobotics.com/public.key \
      | gpg --dearmor -o /etc/apt/keyrings/clearpathrobotics.gpg \
 && echo "deb [signed-by=/etc/apt/keyrings/clearpathrobotics.gpg] https://packages.clearpathrobotics.com/stable/ubuntu $(lsb_release -cs) main" \
      > /etc/apt/sources.list.d/clearpath.list \
 && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y \
      ros-jazzy-clearpath-simulator \
      ros-jazzy-clearpath-nav2-demos \
      ros-jazzy-clearpath-viz \
      ros-jazzy-navigation2 \
      ros-jazzy-nav2-bringup \
      ros-jazzy-rviz2 \
      ros-jazzy-foxglove-bridge \
      ros-jazzy-rosbag2-storage-mcap \
      ros-jazzy-rmw-fastrtps-cpp \
 && rm -rf /var/lib/apt/lists/*

COPY containers/entrypoint.sh /usr/local/bin/bird-nose-entrypoint
RUN chmod 0755 /usr/local/bin/bird-nose-entrypoint
ENTRYPOINT ["/usr/local/bin/bird-nose-entrypoint"]
CMD ["bash"]

# ---------------------------------------------------------------------------
# dev: adds build and lint tools plus a non-root user whose UID/GID match
# the host user, so files created in the mounted repository stay yours.
# ---------------------------------------------------------------------------
FROM base AS dev

RUN apt-get update && apt-get install -y \
      sudo \
      git \
      less \
      nano \
      bash-completion \
      python3-pip \
      python3-pytest \
      ros-dev-tools \
      ros-jazzy-ament-lint-auto \
      ros-jazzy-ament-lint-common \
      ros-jazzy-ament-cmake-pytest \
 && rm -rf /var/lib/apt/lists/*

ARG USERNAME=dev
ARG USER_UID=1000
ARG USER_GID=1000

# Ubuntu 24.04 images ship a default "ubuntu" user with UID 1000, which
# would collide with most host users; remove it before creating ours.
RUN (userdel -r ubuntu 2>/dev/null || true) \
 && (getent group "${USER_GID}" >/dev/null || groupadd --gid "${USER_GID}" "${USERNAME}") \
 && useradd --uid "${USER_UID}" --gid "${USER_GID}" --create-home --shell /bin/bash "${USERNAME}" \
 && echo "${USERNAME} ALL=(root) NOPASSWD:ALL" > "/etc/sudoers.d/${USERNAME}" \
 && chmod 0440 "/etc/sudoers.d/${USERNAME}" \
 && echo 'source /usr/local/bin/bird-nose-entrypoint' >> "/home/${USERNAME}/.bashrc" \
 && mkdir -p "/home/${USERNAME}/.bird_nose/sim_setup" \
 && chown -R "${USER_UID}:${USER_GID}" "/home/${USERNAME}/.bird_nose" \
 && mkdir -p /commandhistory \
 && touch /commandhistory/.bash_history \
 && chown -R "${USER_UID}:${USER_GID}" /commandhistory \
 && echo "export PROMPT_COMMAND='history -a'; export HISTFILE=/commandhistory/.bash_history" \
      >> "/home/${USERNAME}/.bashrc"

# rosdep keeps its cache per user; initialise it once for the image.
RUN rosdep init 2>/dev/null || true

USER ${USERNAME}
RUN rosdep update --rosdistro jazzy
WORKDIR /workspaces/bird-nose
ENV DEBIAN_FRONTEND=
