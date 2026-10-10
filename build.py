#!/usr/bin/env python3
"""Generate the homepage and stage public files for GitHub Pages."""
from pathlib import Path
import runpy
import shutil

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / '_site'
runpy.run_path(str(ROOT / 'generate.py'), run_name='__main__')
if OUTPUT.is_symlink():
    raise ValueError('Build output must not be a symbolic link')
if OUTPUT.exists():
    shutil.rmtree(OUTPUT)
OUTPUT.mkdir()
for name in ('index.html', 'ai-aided-papers.html', 'styles.css', 'script.js'):
    shutil.copy2(ROOT / name, OUTPUT / name)
for directory in ('assets', 'preprints', 'ai-papers'):
    source = ROOT / directory
    if source.is_symlink() or not source.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError(f'Unsupported content directory: {directory}')
    if not source.exists():
        continue
    for path in source.rglob('*'):
        if path.is_symlink() or not path.resolve().is_relative_to(source.resolve()):
            raise ValueError(f'Unsupported linked asset: {path.relative_to(ROOT)}')
        if not path.is_file():
            continue
        if directory in ('preprints', 'ai-papers') and path.suffix.lower() != '.pdf':
            continue
        target = OUTPUT / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
print('Staged public website in _site/')
