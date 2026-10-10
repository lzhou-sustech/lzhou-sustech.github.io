#!/usr/bin/env python3
"""Remove public editing controls and list PDFs committed by the site owner.

Only index.html and ai-aided-papers.html are changed. No source publications,
PDFs, or other assets are deleted. Repository write access is enforced by GitHub,
not by this script. Every file committed to the public repository is public.
"""
from __future__ import annotations

import html
import json
import re
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent


def pdf_listing(folder: Path, *, ai: bool) -> str:
    cards: list[str] = []
    if folder.is_dir():
        pdfs = sorted(
            (p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() == '.pdf'),
            key=lambda p: p.name.casefold(),
        )
        for pdf in pdfs:
            if pdf.is_symlink() or not pdf.resolve().is_relative_to(folder.resolve()):
                continue
            metadata_path = pdf.with_suffix('.json')
            metadata: dict = {}
            if metadata_path.is_file() and not metadata_path.is_symlink():
                try:
                    value = json.loads(metadata_path.read_text(encoding='utf-8'))
                except (OSError, ValueError) as exc:
                    raise ValueError(f'Invalid PDF metadata: {metadata_path}') from exc
                if not isinstance(value, dict):
                    raise ValueError(f'PDF metadata must be an object: {metadata_path}')
                metadata = value
            title = metadata.get('title') or re.sub(r'[_-]+', ' ', pdf.stem)
            if not isinstance(title, str):
                raise ValueError(f'PDF title must be text: {metadata_path}')
            url = html.escape(quote(pdf.relative_to(ROOT).as_posix(), safe='/'), quote=True)
            title_html = html.escape(title)
            authors = metadata.get('authors', '')
            if isinstance(authors, list):
                authors = ', '.join(str(author) for author in authors)
            authors_html = f'<p class="preprint-authors">{html.escape(str(authors))}</p>' if authors else ''
            description = metadata.get('description', '')
            description_html = f'<p>{html.escape(str(description))}</p>' if description else ''
            size = pdf.stat().st_size
            size_label = f'{size / 1_048_576:.1f} MB' if size >= 1_048_576 else f'{max(1, round(size / 1024))} KB'
            cards.append(
                f'<li class="preprint-card"><h3><a href="{url}">{title_html}</a></h3>'
                f'{authors_html}{description_html}<p class="preprint-links">'
                f'<a href="{url}">Read PDF</a> <a href="{url}" download>Download PDF</a>'
                f' <span class="preprint-size">{size_label}</span></p></li>'
            )
    if cards:
        return '<ul class="preprint-list">\n' + '\n'.join(cards) + '\n</ul>'
    text = 'No AI-assisted PDFs are currently listed.' if ai else 'No PDFs are currently listed.'
    return f'<div class="preprint-empty"><p>{text}</p></div>'


def refresh_page(source: str, listing: str) -> str:
    # These exact containers contain editing links only, never public papers.
    source = re.sub(r'<div class="preprint-upload">.*?</div>', '', source, flags=re.S)
    source = re.sub(r'<details class="paper-manager">.*?</details>', '', source, flags=re.S)
    begin = '<!-- PUBLIC-PDFS:START -->'
    end = '<!-- PUBLIC-PDFS:END -->'
    replacement = f'{begin}\n{listing}\n{end}'
    if begin in source or end in source:
        if source.count(begin) != 1 or source.count(end) != 1:
            raise ValueError('Expected exactly one complete PUBLIC-PDFS section')
        source, count = re.subn(re.escape(begin) + r'.*?' + re.escape(end), lambda _: replacement, source, flags=re.S)
    else:
        # Migrate the original empty placeholder or original generated PDF list.
        pattern = r'<div class="preprint-empty">.*?</div>|<ul class="preprint-list">.*?</ul>'
        matches = list(re.finditer(pattern, source, flags=re.S))
        if len(matches) != 1:
            raise ValueError('Could not identify one uploaded-PDF section; no files have been saved')
        source, count = re.subn(pattern, lambda _: replacement, source, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Could not update the uploaded-PDF section')
    if 'class="preprint-upload"' in source or 'class="paper-manager"' in source:
        raise ValueError('Public editing controls remain')
    return source


def main() -> None:
    pending: list[tuple[Path, str]] = []
    for filename, folder, ai in [('index.html', 'preprints', False), ('ai-aided-papers.html', 'ai-papers', True)]:
        path = ROOT / filename
        original = path.read_text(encoding='utf-8')
        updated = refresh_page(original, pdf_listing(ROOT / folder, ai=ai))
        if updated != original:
            pending.append((path, updated))
    # Validate both pages before writing either one.
    for path, updated in pending:
        path.write_text(updated, encoding='utf-8')
        print(f'Updated {path.name}')
    if not pending:
        print('Public pages are already current')


if __name__ == '__main__':
    main()
