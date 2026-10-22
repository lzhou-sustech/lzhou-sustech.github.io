#!/usr/bin/env python3
"""Maintain separate, read-only pages and the owner's public AI-paper listing.

The original single-page layout is migrated once, without rewriting its paper
citations. Subsequent runs maintain six public pages, including one consolidated
Preprints page for arXiv and other working manuscripts. Source PDFs, metadata,
and other assets are preserved. GitHub enforces repository write access.
"""
from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PAGES = (
    ('home', 'index.html', 'Home / About'),
    ('research', 'research.html', 'Research'),
    ('publications', 'publications.html', 'Publications'),
    ('preprints', 'preprints.html', 'Preprints'),
    ('teaching', 'teaching.html', 'Teaching & service'),
    ('contact', 'contact.html', 'Contact'),
)
BEGIN = '<!-- PUBLIC-PDFS:START -->'
END = '<!-- PUBLIC-PDFS:END -->'
LEGACY = '''  <script id="legacy-section-links">
    (() => {
      const pages = {research: 'research.html', publications: 'publications.html',
        preprints: 'preprints.html', 'ai-papers': 'preprints.html',
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
        'preprints.html': 'Preprints and working papers by Lin Zhou.',
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
        raise ValueError('Preprints contain legacy public upload controls')


def main() -> None:
    originals = {filename: (ROOT / filename).read_text(encoding='utf-8')
                 for _, filename, _ in PAGES if (ROOT / filename).is_file()}
    if 'index.html' not in originals:
        raise ValueError('The homepage must exist')
    pages = dict(originals)
    if 'publications' in Audit(originals['index.html']).sections:
        # One-time migration: copy the existing HTML, preserving every citation.
        for section, filename, label in PAGES:
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
    validate(pages)
    # Validate all seven outputs before changing any file. Never delete assets.
    pending = [(filename, source) for filename, source in pages.items()
               if source != originals.get(filename)]
    for filename, source in pending:
        (ROOT / filename).write_text(source, encoding='utf-8')
        print(f'Updated {filename}')
    if not pending:
        print('All six public pages are already current')


if __name__ == '__main__':
    main()
