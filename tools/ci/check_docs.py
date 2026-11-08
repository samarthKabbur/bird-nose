#!/usr/bin/env python3
"""
Check that the repository's documentation still matches its code.

Run from anywhere inside the repository:

    python3 tools/ci/check_docs.py

Each check prints the problems it finds. The script exits with status 1 if
any check failed, so CI fails the pull request. It uses only the Python
standard library and Git, so it runs on the host or in any container.

Checks:
  links       Relative Markdown links point at files that exist, and
              #anchors match a heading in the target file.
  map         Every module folder appears in the README's repository map.
  readmes     Every module folder (except docs/ and .github/) has a README
              with the required sections.
  launch      Every launch argument has a description= and is named in its
              package README.
  params      Every ROS parameter is declared with a ParameterDescriptor and
              is named in its package README.
  services    Every Compose service is listed in the README's Services table.
"""
import ast
from pathlib import Path
import re
import subprocess
import sys

REQUIRED_SECTIONS = ('Purpose', 'Contents', 'See also')
# Folders documented elsewhere instead of by their own README.md.
README_EXEMPT = {'docs', '.github'}

LINK_RE = re.compile(r'(?<!!)\[[^\]]*\]\(([^)\s]+)\)')
HEADING_RE = re.compile(r'^(#{1,6})\s+(.*?)\s*#*\s*$')
FENCE_RE = re.compile(r'^\s*(```|~~~)')


def repo_root():
    """Return the repository root, found through Git."""
    out = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                         capture_output=True, text=True, check=True)
    return Path(out.stdout.strip())


def tracked_files(root):
    """Return tracked file paths relative to the root."""
    out = subprocess.run(['git', 'ls-files'], cwd=root,
                         capture_output=True, text=True, check=True)
    return [Path(line) for line in out.stdout.splitlines() if line]


def prose_lines(text):
    """Yield (line number, line) for lines outside fenced code blocks."""
    in_fence = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if not in_fence:
            yield number, line


def github_anchors(text):
    """Return the anchors GitHub generates for a Markdown file's headings."""
    anchors, seen = set(), {}
    for _, line in prose_lines(text):
        match = HEADING_RE.match(line)
        if not match:
            continue
        title = re.sub(r'`|\*\*|__', '', match.group(2))
        title = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', title)
        slug = re.sub(r'[^\w\- ]', '', title.lower()).replace(' ', '-')
        count = seen.get(slug, 0)
        seen[slug] = count + 1
        anchors.add(slug if count == 0 else f'{slug}-{count}')
    return anchors


def check_links(root, files):
    """Relative links resolve to tracked files and existing anchors."""
    problems = []
    tracked = {str(f) for f in files}
    tracked_dirs = {str(p) for f in files for p in f.parents}
    for md in (f for f in files if f.suffix == '.md'):
        text = (root / md).read_text(encoding='utf-8')
        for number, line in prose_lines(text):
            line = re.sub(r'`[^`]*`', '', line)  # links inside code spans are not links
            for target in LINK_RE.findall(line):
                if re.match(r'^[a-z][a-z0-9+.-]*:', target):
                    continue  # http:, https:, mailto:, and so on
                path_part, _, anchor = target.partition('#')
                where = f'{md}:{number}: {target}'
                if path_part:
                    resolved = (root / md.parent / path_part).resolve()
                    try:
                        rel = str(resolved.relative_to(root))
                    except ValueError:
                        problems.append(f'{where} points outside the repository')
                        continue
                    if rel not in tracked and rel not in tracked_dirs:
                        problems.append(f'{where} points at a file that is not in Git')
                        continue
                    target_file = Path(rel)
                else:
                    target_file = md
                if anchor and target_file.suffix == '.md' and str(target_file) in tracked:
                    anchors = github_anchors((root / target_file).read_text(encoding='utf-8'))
                    if anchor not in anchors:
                        problems.append(f'{where} has no heading for #{anchor}')
    return problems


def module_dirs(files):
    """Return the folders that count as modules, as POSIX paths."""
    dirs = {f.parts[0] for f in files if len(f.parts) > 1}
    modules = set(dirs) - {'src'}
    for parent in ('config', 'tools'):
        modules |= {f'{parent}/{f.parts[1]}' for f in files
                    if len(f.parts) > 2 and f.parts[0] == parent}
    modules |= {f'src/{f.parts[1]}' for f in files
                if len(f.parts) == 3 and f.parts[0] == 'src' and f.name == 'package.xml'}
    return sorted(modules)


def section(text, heading):
    """Return the body of a '## heading' section, up to the next heading of that level."""
    match = re.search(rf'^##+ {re.escape(heading)}\s*$(.*?)(?=^## |\Z)', text, re.M | re.S)
    return match.group(1) if match else ''


def check_map(root, files):
    """Every module folder is listed in the README's repository map."""
    table = section((root / 'README.md').read_text(encoding='utf-8'), 'Repository map')
    if not table:
        return ['README.md has no "Repository map" section']
    listed = {cell.rstrip('/') for cell in re.findall(r'^\| `([^`]+)`', table, re.M)}
    return [f'README.md repository map is missing `{m}/`'
            for m in module_dirs(files) if m not in listed]


def check_readmes(root, files):
    """Every module folder has a README with the required sections."""
    problems = []
    for module in module_dirs(files):
        if module in README_EXEMPT:
            continue
        readme = root / module / 'README.md'
        if not readme.is_file():
            problems.append(f'{module}/ has no README.md')
            continue
        headings = re.findall(r'^## (.+?)\s*$', readme.read_text(encoding='utf-8'), re.M)
        for required in REQUIRED_SECTIONS:
            if required not in headings:
                problems.append(f'{module}/README.md has no "## {required}" section')
    return problems


def call_name(node):
    """Return the called function's name for Name and Attribute calls."""
    func = node.func
    return func.id if isinstance(func, ast.Name) else getattr(func, 'attr', None)


def package_readme(root, path):
    """Return the text of the README of the package that holds path."""
    parts = path.parts
    readme = root / parts[0] / parts[1] / 'README.md'
    return readme.read_text(encoding='utf-8') if readme.is_file() else ''


def check_launch(root, files):
    """Launch arguments have a description and appear in the package README."""
    problems = []
    for path in files:
        if path.parts[0] != 'src' or 'launch' not in path.parts or path.suffix != '.py':
            continue
        readme = package_readme(root, path)
        tree = ast.parse((root / path).read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and call_name(node) == 'DeclareLaunchArgument'):
                continue
            if not (node.args and isinstance(node.args[0], ast.Constant)):
                continue
            name = node.args[0].value
            where = f'{path}:{node.lineno}: launch argument {name!r}'
            if not any(k.arg == 'description' for k in node.keywords):
                problems.append(f'{where} has no description=')
            if f'`{name}`' not in readme:
                problems.append(f'{where} is not in the package README')
    return problems


def check_params(root, files):
    """ROS parameters are declared with a descriptor and appear in the package README."""
    problems = []
    for path in files:
        if path.parts[0] != 'src' or path.suffix != '.py' or 'test' in path.parts:
            continue
        readme = package_readme(root, path)
        tree = ast.parse((root / path).read_text(encoding='utf-8'), filename=str(path))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and call_name(node) == 'declare_parameter'):
                continue
            if not (node.args and isinstance(node.args[0], ast.Constant)):
                continue
            name = node.args[0].value
            where = f'{path}:{node.lineno}: parameter {name!r}'
            if len(node.args) < 3 and not any(k.arg == 'descriptor' for k in node.keywords):
                problems.append(f'{where} has no ParameterDescriptor')
            if f'`{name}`' not in readme:
                problems.append(f'{where} is not in the package README')
    return problems


def compose_services(text):
    """Return the service names under the top-level services: key."""
    match = re.search(r'^services:\s*$(.*?)(?=^\S|\Z)', text, re.M | re.S)
    return re.findall(r'^  ([A-Za-z0-9_.-]+):\s*$', match.group(1), re.M) if match else []


def check_services(root, files):
    """Every Compose service is listed in the README's Services table."""
    services = compose_services((root / 'containers/compose.yaml').read_text(encoding='utf-8'))
    if not services:
        return ['containers/compose.yaml: no services found']
    table = section((root / 'README.md').read_text(encoding='utf-8'), 'Services')
    listed = set(re.findall(r'^\| `([^`]+)`', table, re.M))
    return [f'README.md Services table is missing `{s}`' for s in services if s not in listed]


CHECKS = (
    ('links', check_links),
    ('map', check_map),
    ('readmes', check_readmes),
    ('launch', check_launch),
    ('params', check_params),
    ('services', check_services),
)


def main():
    """Run every check and report the results."""
    root = repo_root()
    files = [f for f in tracked_files(root) if (root / f).is_file()]
    failed = False
    for name, check in CHECKS:
        problems = check(root, files)
        print(f'{"FAIL" if problems else "ok  "} {name}')
        for problem in problems:
            print(f'     {problem}')
        failed = failed or bool(problems)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
