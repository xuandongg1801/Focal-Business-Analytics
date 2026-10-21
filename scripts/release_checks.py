"""Release inventory, portable paths, semantic narrative and dependency gates."""
from __future__ import annotations
import ast
import hashlib
import importlib.metadata
import os
from pathlib import Path
import platform
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
RUNTIME_DIRS = frozenset({'.cache', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache'})
EXCLUDED_DIRS = RUNTIME_DIRS | {'.venv', '.git', 'node_modules', '.idea', '.vscode', 'dist'}
TEXT_EXTENSIONS = {'.py', '.md', '.json', '.yaml', '.yml', '.toml', '.txt', '.log', '.csv', '.in', '.css', '.ps1'}
INTEGRATION = re.compile('|'.join(['power'+'bi', 'power'+' bi', 'pbi'+'p', 'pbi'+'r', 'pbi'+'sm', 'tm'+'dl', 'model'+'.bim']) + r'|\b'+'da'+'x'+r'\b', re.I)
DEVELOPER_PATH = re.compile(r'(?i)\b[a-z]:[\\/]|/(?:Users|home)/[^/\s]+|\b(?:Downloads|Desktop|OneDrive)[\\/]')
PROJECT_NARRATIVE = re.compile(
    r'(?i)(?:previous|prior)[_\s]+(?:project|experiments?|release|versions?)'
    r'|old[_\s]+version|version[_\s]+before|before[_\s]+audit|fixed[_\s]+from'
    r'|\blegacy\b|\bmigrated\b|' + 'trước ' + 'đây|' + 'phiên bản ' + 'cũ|' + 'sau khi ' + 'sửa')

RETIRED_SEMANTICS = re.compile(r'(?i)\b' + 'pro'+'xy' + r'\b|approval '+r'probability|'
    + 'nhãn đại'+' diện|' + 'hoàn thiện'+' đơn|' + '(?:không|chưa) phải '+r'Win[/ ]Lost')
REMOVED_FEATURE = re.compile(r'(?i)\b' + 're'+'port' + r'(?:[/\\]|_dir\b|_path\b)')
REMOVED_DIRECTORY = 're'+'port'


def release_files(root=ROOT):
    for directory, folders, files in os.walk(root):
        folders[:] = sorted(d for d in folders if d not in EXCLUDED_DIRS)
        for name in sorted(files):
            path = Path(directory)/name
            if path.suffix in {'.pyc', '.pyo', '.log', '.zip'} or name.startswith('.coverage'):
                continue
            yield path


def fingerprint(root=ROOT, *, source_only=False):
    files = release_files(root)
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files
            if (not source_only or p.suffix in {'.py', '.md', '.in', '.toml', '.txt', '.ps1'} or p.name == '.python-version')
            and p.relative_to(root).parts[:2] != ('outputs', 'release')
            and p.relative_to(root).parts[:2] != ('outputs', 'logs')}


def check_text(relative, text):
    if INTEGRATION.search(relative) or INTEGRATION.search(text):
        raise AssertionError(f'Obsolete integration: {relative}')
    if DEVELOPER_PATH.search(text):
        raise AssertionError(f'Developer-specific absolute path: {relative}')
    if RETIRED_SEMANTICS.search(text):
        raise AssertionError(f'Retired target semantic: {relative}')
    if REMOVED_FEATURE.search(text):
        raise AssertionError(f'Removed feature reference: {relative}')
    if PROJECT_NARRATIVE.search(text):
        raise AssertionError(f'Project-version narrative: {relative}')
    # API import is a scientific/library namespace, not release history.
    for line in text.splitlines():
        if re.search(r'(?i)\bv[12]\b', line) and 'streamlit.testing.' not in line:
            raise AssertionError(f'Version narrative requires classification: {relative}')


def check_source(root=ROOT, check_links=True):
    if (root/REMOVED_DIRECTORY).exists():
        raise AssertionError('Removed feature directory is still present')
    syntax = scanned = 0
    for path in release_files(root):
        relative = path.relative_to(root).as_posix()
        if INTEGRATION.search(relative):
            raise AssertionError(f'Obsolete integration path: {relative}')
        if path.suffix == '.py':
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=relative)
            syntax += 1
        if path.suffix in TEXT_EXTENSIONS:
            text = path.read_text(encoding='utf-8-sig')
            check_text(relative, text)
            if check_links and path.suffix == '.md':
                for target in re.findall(r'\]\(([^)]+)\)', text):
                    if '://' not in target and not target.startswith('#'):
                        target = unquote(target.split('#')[0].strip('<>'))
                        if target and not (path.parent/target).exists():
                            raise AssertionError(f'Broken document link in {relative}: {target}')
            scanned += 1
    return dict(syntax_files=syntax, source_files_scanned=scanned, stale_references='PASS',
                developer_paths='PASS', project_narrative='PASS', target_semantics='PASS', removed_feature='PASS')


def check_clean_tree(root=ROOT):
    bad = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {'.venv', '.git', 'node_modules', 'dist'}]
        bad.extend((Path(folder)/d).relative_to(root).as_posix() for d in dirs if d in RUNTIME_DIRS)
        bad.extend((Path(folder)/n).relative_to(root).as_posix() for n in files
                   if n.endswith(('.pyc','.pyo','.log')) or n.startswith('.coverage'))
    if bad:
        raise AssertionError(f'Runtime junk in release: {bad[:10]}')
    return {'status':'PASS', 'runtime_junk':0}


def environment(root=ROOT):
    expected_python = (root/'.python-version').read_text().strip()
    actual_python = platform.python_version()
    if actual_python != expected_python:
        raise AssertionError(f'Python {actual_python}; required {expected_python}')
    expected = {}
    for line in (root/'requirements.txt').read_text().splitlines():
        if line.strip() and not line.startswith('#'):
            name, version = line.split('==')
            expected[name] = version
    actual = {name: importlib.metadata.version(name) for name in expected}
    if actual != expected:
        raise AssertionError(f'Runtime differs from requirements: {actual}')
    return {'python':actual_python, 'packages':actual, 'exact_pins':'PASS'}


def sanitize_log(text, root=ROOT):
    # Diagnostics are not delivered; portable substitutions also aid local review.
    return text.replace(str(root), '<project>').replace(root.as_posix(), '<project>')


def clean_runtime(root=ROOT):
    """Remove only verified runtime paths within this checkout; never follow links."""
    import shutil
    root = root.resolve()
    targets = []
    for folder, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in {'.venv', '.git', 'node_modules', 'dist'}]
        for name in list(dirs):
            if name in RUNTIME_DIRS:
                targets.append(Path(folder)/name)
                dirs.remove(name)
        targets.extend(Path(folder)/n for n in files
                       if n.endswith(('.pyc','.pyo','.log')) or n.startswith('.coverage'))
    removed = []
    for path in targets:
        target = path.resolve()
        if path.is_symlink() or root not in target.parents or target == root:
            raise ValueError('Refusing runtime cleanup outside the checked project root')
        if target.is_dir():
            if any(p.is_symlink() for p in target.rglob('*')):
                raise ValueError('Runtime directory contains a link')
            shutil.rmtree(target)
        else:
            target.unlink()
        removed.append(target.relative_to(root).as_posix())
    return removed
