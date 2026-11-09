#!/usr/bin/env python3
"""
Print every parameter that differs between two ROS parameter YAML files.

    python3 tools/ci/diff_params.py BEFORE.yaml AFTER.yaml

Used to check that a generated Nav2 parameter file differs from Clearpath's
only where Bird Nose meant it to (see bird_nose_navigation).
"""
import sys

import yaml


def flatten(tree, prefix=''):
    """Return {dotted.key: value} for every leaf of a nested dictionary."""
    leaves = {}
    for key, value in (tree or {}).items():
        path = f'{prefix}{key}'
        if isinstance(value, dict):
            leaves.update(flatten(value, path + '.'))
        else:
            leaves[path] = value
    return leaves


def main(before_path, after_path):
    """Print added, removed, and changed parameters; return 0."""
    with open(before_path, encoding='utf-8') as f:
        before = flatten(yaml.safe_load(f))
    with open(after_path, encoding='utf-8') as f:
        after = flatten(yaml.safe_load(f))
    for key in sorted(set(before) | set(after)):
        if key not in after:
            print(f'removed  {key} = {before[key]!r}')
        elif key not in before:
            print(f'added    {key} = {after[key]!r}')
        elif before[key] != after[key] or type(before[key]) is not type(after[key]):
            print(f'changed  {key}: {before[key]!r} -> {after[key]!r}')
    return 0


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
