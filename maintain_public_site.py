#!/usr/bin/env python3
"""Maintain separate, read-only pages and the owner's public AI-paper listing.

The original single-page layout is migrated once, without rewriting its paper
citations. Later runs preserve each page's content and refresh only navigation,
the arXiv-only preprint layout, and AI-paper links. Source metadata, PDFs, images,
and all other assets are left unchanged. GitHub enforces repository write access.
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
PAGES = (
    ('home', 'index.html', 'Home / About'),
    ('research', 'research.html', 'Research'),
    ('publications', 'publications.html', 'Publications'),
    ('preprints', 'preprints.html', 'Preprints'),
    ('ai-papers', 'ai-aided-papers.html', 'AI-Aided Papers'),
    ('teaching', 'teaching.html', 'Teaching & service'),
    ('contact', 'contact.html', 'Contact'),
)
BEGIN = '<!-- PUBLIC-PDFS:START -->'
END = '<!-- PUBLIC-PDFS:END -->'
NOTICE = '<p class="ai-disclaimer">Papers here are written with the help of ChatGPT.</p>'
LEGACY = '''  <script id="legacy-section-links">
    (() => {
      const pages = {research: 'research.html', publications: 'publications.html',
        preprints: 'preprints.html', 'ai-papers': 'ai-aided-papers.html',
        teaching: 'teaching.html', contact: 'contact.html'};
      const openLegacyLink = () => {
        const destination = pages[window.location.hash.slice(1)];
        if (destination) window.location.replace(destination);
      };
      openLegacyLink();
      window.addEventListener('hashchange', openLegacyLink);
    })();
  </script>
'''


class Audit(HTMLParser):
    """Read the structural facts required to validate every generated page."""
    def __init__(self, source: str) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.sections: list[str] = []
        self.nav: list[tuple[str, str | None]] = []
        self.classes: list[str] = []
        self.h1 = 0
        self.in_nav = False
        self.feed(source)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get('id'):
            self.ids.append(values['id'])
        self.classes.extend((values.get('class') or '').split())
        if tag == 'section':
            self.sections.append(values.get('id', ''))
        if tag == 'h1':
            self.h1 += 1
        if tag == 'nav' and values.get('aria-label') == 'Main navigation':
            self.in_nav = True
        if tag == 'a' and self.in_nav:
            self.nav.append((values.get('href', ''), values.get('aria-current')))

    def handle_endtag(self, tag: str) -> None:
        if tag == 'nav':
            self.in_nav = False


def strip_controls(source: str) -> str:
    source = re.sub(r'<div class="preprint-upload">.*?</div>', '', source, flags=re.S)
    return re.sub(r'<details class="paper-manager">.*?</details>', '', source, flags=re.S)


def navigation(filename: str) -> str:
    links = []
    for _, target, label in PAGES:
        active = ' aria-current="page"' if target == filename else ''
        links.append(f'        <a href="{target}"{active}>{html.escape(label)}</a>')
    return '<nav aria-label="Main navigation">\n' + '\n'.join(links) + '\n      </nav>'


def normalize_navigation(source: str, filename: str) -> str:
    source = strip_controls(source)
    source, count = re.subn(r'<nav aria-label="Main navigation">.*?</nav>',
                            lambda _: navigation(filename), source, flags=re.S)
    if count != 1:
        raise ValueError(f'{filename}: expected one navigation menu')
    for section, target, _ in PAGES:
        for old in (f'#{section}', f'index.html#{section}'):
            source = source.replace(f'href="{old}"', f'href="{target}"')
    return source


def extract_section(source: str, section: str) -> str:
    pattern = rf'<section\b[^>]*\bid="{re.escape(section)}"[^>]*>.*?</section>'
    matches = re.findall(pattern, source, flags=re.S)
    if len(matches) != 1:
        raise ValueError(f'Expected exactly one original {section} section')
    # The original site's sections are not nested; fail rather than truncate one.
    if len(Audit(matches[0]).sections) != 1:
        raise ValueError(f'Nested sections require manual migration: {section}')
    return matches[0]


def arxiv_only(source: str) -> str:
    source = strip_controls(source)
    source = re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), '', source, flags=re.S)
    source = re.sub(r'<h3>Uploaded PDFs</h3>', '', source)
    source = re.sub(r'<div class="preprint-empty">.*?</div>', '', source, flags=re.S)
    source = re.sub(r'<ul class="preprint-list">.*?</ul>', '', source, flags=re.S)
    source = re.sub(r'<p class="secondary">AI-assisted working drafts are listed.*?</p>',
                    '', source, flags=re.S)
    return source


def render_page(template: str, section: str, filename: str, label: str) -> str:
    if filename != 'index.html':
        section = re.sub(r'<h2(\s+id="[^\"]+-title")>(.*?)</h2>',
                         r'<h1\1>\2</h1>', section, count=1, flags=re.S)
    title = 'Lin Zhou — Academic Homepage' if filename == 'index.html' else f'{label} — Lin Zhou'
    source = re.sub(r'<title>.*?</title>', lambda _: f'<title>{html.escape(title)}</title>',
                    template, count=1, flags=re.S)
    descriptions = {
        'research.html': 'Research interests of Lin Zhou at SUSTech.',
        'publications.html': 'Publications by Lin Zhou: books, monographs, journal articles, and conference papers.',
        'preprints.html': 'arXiv preprints by Lin Zhou.',
        'teaching.html': 'Teaching and professional service of Lin Zhou.',
        'contact.html': 'Contact information for Lin Zhou at SUSTech.',
    }
    if filename in descriptions:
        source = re.sub(r'<meta name="description" content="[^"]*">',
                        lambda _: '<meta name="description" content="' +
                        html.escape(descriptions[filename], quote=True) + '">', source, count=1)
    footer = ('<footer><span>© Lin Zhou</span>'
              '<a href="#main">Back to top</a></footer>')
    replacement = f'<main id="main">\n      {section}\n      {footer}\n    </main>'
    source, count = re.subn(r'<main id="main">.*?</main>', lambda _: replacement,
                            source, count=1, flags=re.S)
    if count != 1:
        raise ValueError('Could not identify the original page content')
    if filename == 'index.html' and 'id="legacy-section-links"' not in source:
        source = source.replace('</head>', LEGACY + '</head>', 1)
    return normalize_navigation(source, filename)


def pdf_listing(folder: Path) -> str:
    """Render AI-aided manuscripts as scholarly citations with direct PDF links."""
    citations: list[tuple[str, str]] = []
    if folder.is_dir() and not folder.is_symlink():
        pdfs = sorted((p for p in folder.rglob('*') if p.is_file() and p.suffix.lower() == '.pdf'),
                      key=lambda p: p.relative_to(folder).as_posix().casefold())
        remote_records = sorted(
            (p for p in folder.rglob('*.json')
             if p.is_file() and not p.with_suffix('.pdf').is_file()),
            key=lambda p: p.relative_to(folder).as_posix().casefold())
        for pdf in [*pdfs, *remote_records]:
            if pdf.is_symlink() or not pdf.resolve().is_relative_to(folder.resolve()):
                continue
            metadata_path = pdf if pdf.suffix.lower() == '.json' else pdf.with_suffix('.json')
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
            if pdf.suffix.lower() == '.json':
                remote_url = metadata.get('pdfUrl')
                if remote_url is None:
                    continue
                if (not isinstance(remote_url, str) or
                        not re.fullmatch(r'https://arxiv\.org/pdf/\d{4}\.\d{4,5}(?:v\d+)?',
                                         remote_url)):
                    raise ValueError(f'Expected an official arXiv PDF URL: {metadata_path}')
                url = html.escape(remote_url, quote=True)
            else:
                url = html.escape(quote(pdf.relative_to(ROOT).as_posix(), safe='/'), quote=True)
            authors = metadata.get('authors', [])
            if isinstance(authors, list):
                names = [html.escape(str(name)) for name in authors if str(name).strip()]
                if len(names) == 2:
                    authors_html = ' and '.join(names)
                elif len(names) > 2:
                    authors_html = ', '.join(names[:-1]) + ', and ' + names[-1]
                else:
                    authors_html = names[0] if names else ''
            else:
                authors_html = html.escape(str(authors))
            authors_html = authors_html.replace('Lin Zhou', '<strong>Lin Zhou</strong>')
            author_prefix = f'{authors_html}. ' if authors_html else ''
            year = str(metadata.get('year') or '').strip()
            year_text = ', ' + html.escape(year) if year else ''
            updated = metadata.get('updated')
            if updated is None:
                updated = f'{year}-01-01' if re.fullmatch(r'\d{4}', year) else '0001-01-01'
            if not isinstance(updated, str):
                raise ValueError(f'Paper update date must be text: {metadata_path}')
            try:
                date.fromisoformat(updated)
            except ValueError as exc:
                raise ValueError(f'Invalid paper update date: {metadata_path}') from exc
            submitted = metadata.get('submitted')
            if submitted is not None:
                if not isinstance(submitted, str):
                    raise ValueError(f'Paper submission date must be text: {metadata_path}')
                try:
                    date.fromisoformat(submitted)
                except ValueError as exc:
                    raise ValueError(f'Invalid paper submission date: {metadata_path}') from exc
            # Sort arXiv works by their original submission date, not by
            # when they were moved into this section or subsequently revised.
            # A working paper with no submission date uses its revision date.
            sort_date = submitted or updated
            if submitted:
                date_label, date_value = 'Submitted', submitted
            elif metadata.get('updated'):
                date_label, date_value = 'Updated', updated
            else:
                date_label, date_value = '', ''
            date_html = (
                f' <span class="ai-paper-dates">({date_label} '
                f'<time datetime="{date_value}">{date_value}</time>)</span>'
            ) if date_value else ''
            category = metadata.get('citationType') or 'Working paper'
            if not isinstance(category, str):
                raise ValueError(f'PDF citation type must be text: {metadata_path}')
            arxiv_url = metadata.get('arxivUrl') or ''
            if not isinstance(arxiv_url, str):
                raise ValueError(f'arXiv link must be text: {metadata_path}')
            arxiv_link = (
                ' <a class="publication-arxiv" href="' +
                html.escape(arxiv_url, quote=True) + '">[arXiv]</a>'
            ) if arxiv_url.startswith('https://arxiv.org/abs/') else ''
            citations.append((
                sort_date,
                f'{author_prefix}<span class="publication-title">“'
                f'<a href="{url}" type="application/pdf">{html.escape(title)}</a>.”</span> '
                f'<em>{html.escape(category)}</em>{year_text}. '
                f'<a class="publication-pdf" href="{url}" type="application/pdf">[PDF]</a>'
                f'{arxiv_link}{date_html}'
            ))
    if not citations:
        return '<p class="secondary">To be updated.</p>'
    # Reverse chronological by displayed date: arXiv submission first,
    # otherwise the documented update date; use a stable name tie-breaker.
    citations.sort(key=lambda item: item[0], reverse=True)
    entries = []
    count = len(citations)
    for index, (_, citation) in enumerate(citations):
        number = count - index
        entries.append(
            f'<li class="ai-paper"><span class="ai-paper-number" '
            f'aria-label="AI-aided paper {number}">[{number}]</span>'
            f' <span class="ai-paper-citation">{citation}</span></li>'
        )
    return (NOTICE + '\n<ol class="ai-paper-list" reversed start="' + str(count) +
            '" role="list" aria-label="AI-aided working papers">\n' +
            '\n'.join(entries) + '\n</ol>')


def refresh_ai(source: str) -> str:
    # Include the disclaimer only when actual papers are available to read.
    source = re.sub(r'<p class="draft-notice">.*?</p>', '', source, flags=re.S)
    if source.count(BEGIN) != 1 or source.count(END) != 1:
        raise ValueError('AI page must have exactly one complete PUBLIC-PDFS section')
    replacement = f'{BEGIN}\n{pdf_listing(ROOT / "ai-papers")}\n{END}'
    return re.sub(re.escape(BEGIN) + r'.*?' + re.escape(END), lambda _: replacement,
                  source, count=1, flags=re.S)


def validate(pages: dict[str, str]) -> None:
    expected_nav = [filename for _, filename, _ in PAGES]
    for section, filename, _ in PAGES:
        source = pages[filename]
        audit = Audit(source)
        if audit.sections != [section] or audit.h1 != 1:
            raise ValueError(f'{filename}: expected one dedicated section and one main heading')
        if len(audit.ids) != len(set(audit.ids)):
            raise ValueError(f'{filename}: duplicate element IDs')
        if [href for href, _ in audit.nav] != expected_nav:
            raise ValueError(f'{filename}: incorrect page navigation')
        if [href for href, current in audit.nav if current == 'page'] != [filename]:
            raise ValueError(f'{filename}: incorrect active navigation item')
        if any(c in audit.classes for c in ('preprint-upload', 'paper-manager', 'remove-paper')):
            raise ValueError(f'{filename}: public editing controls remain')
    preprints = pages['preprints.html']
    if any(text in preprints for text in ('Uploaded PDFs', BEGIN, 'preprint-list', 'preprint-empty')):
        raise ValueError('Preprints must contain arXiv papers only')


def main() -> None:
    originals = {filename: (ROOT / filename).read_text(encoding='utf-8')
                 for _, filename, _ in PAGES if (ROOT / filename).is_file()}
    if 'index.html' not in originals or 'ai-aided-papers.html' not in originals:
        raise ValueError('The homepage and AI-paper page must both exist')
    pages = dict(originals)
    if 'publications' in Audit(originals['index.html']).sections:
        # One-time migration: copy the existing HTML, preserving every citation.
        for section, filename, label in PAGES:
            if section == 'ai-papers':
                continue
            if filename != 'index.html' and filename in originals:
                raise ValueError(f'Refusing to overwrite existing page during migration: {filename}')
            content = extract_section(originals['index.html'], section)
            if section == 'preprints':
                content = arxiv_only(content)
            pages[filename] = render_page(originals['index.html'], content, filename, label)
    missing = [filename for _, filename, _ in PAGES if filename not in pages]
    if missing:
        raise ValueError('Missing dedicated pages: ' + ', '.join(missing))
    for _, filename, _ in PAGES:
        pages[filename] = normalize_navigation(pages[filename], filename)
    pages['preprints.html'] = arxiv_only(pages['preprints.html'])
    pages['ai-aided-papers.html'] = refresh_ai(pages['ai-aided-papers.html'])
    validate(pages)
    # Validate all seven outputs before changing any file. Never delete assets.
    pending = [(filename, source) for filename, source in pages.items()
               if source != originals.get(filename)]
    for filename, source in pending:
        (ROOT / filename).write_text(source, encoding='utf-8')
        print(f'Updated {filename}')
    if not pending:
        print('All seven public pages are already current')


if __name__ == '__main__':
    main()
