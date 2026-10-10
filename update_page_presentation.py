#!/usr/bin/env python3
"""Publish explicit descending labels, separate publication categories, and an open biography.

Run after maintain_public_site.py. Citation HTML and links are preserved verbatim.
Journal, conference, and book identifiers remain unchanged when visitors filter.
Only the three presentation HTML files are written. No PDF or metadata is changed.
"""
from __future__ import annotations

import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = 'category-numbering-20261010-1'
GROUP_BEGIN = '<!-- PUBLICATION-GROUPS:START -->'
GROUP_END = '<!-- PUBLICATION-GROUPS:END -->'
CATEGORIES = (
    ('journal', 'J', 'Journal articles'),
    ('conference', 'C', 'Conference papers'),
    ('book', 'B', 'Books and monographs'),
)
NUMBER_STYLE = '''  <style id="paper-list-presentation">
    ol.publication-list, ol.arxiv-list {padding-left:0;list-style:none;}
    li.publication, li.arxiv-paper {position:relative;list-style:none;padding-left:3.8em;}
    .paper-number {position:absolute;left:0;top:0;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;}
    .paper-total {margin:-8px 0 14px;}
    .publication-group > h2 {margin-top:25px;}
    .publication-group[hidden], li.publication[hidden] {display:none!important;}
    @media(max-width:430px) {li.publication, li.arxiv-paper {padding-left:3.5em;}}
    @media print {.publication-group[hidden] {display:block!important;} li.publication[hidden] {display:list-item!important;}}
  </style>
'''


class StartTag(HTMLParser):
    def __init__(self, tag: str) -> None:
        super().__init__(convert_charrefs=True)
        self.attrs: dict[str, str | None] = {}
        self.feed(tag)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.attrs = dict(attrs)


def attrs(tag: str) -> dict[str, str | None]:
    return StartTag(tag).attrs


def remove_attrs(attributes: str, names: str) -> str:
    return re.sub(
        rf'''\s+(?:{names})(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?(?=\s|$)''',
        '', attributes, flags=re.I,
    )


def items(source: str, item_class: str) -> list[tuple[str, str, dict[str, str | None]]]:
    found = []
    for match in re.finditer(r'<li\b(?P<attrs>[^>]*)>(?P<body>.*?)</li>', source, re.S):
        values = attrs('<li' + match['attrs'] + '>')
        if item_class not in (values.get('class') or '').split():
            continue
        if '<li' in match['body'] or re.search(r'<(?:ol|ul)\b', match['body']):
            raise ValueError('Nested paper content requires review')
        body = re.sub(r'^\s*<span class="paper-number"[^>]*>.*?</span>', '', match['body'], count=1, flags=re.S)
        found.append((remove_attrs(match['attrs'], 'value|hidden|data-paper-number'), body, values))
    return found


def labelled_item(attributes: str, body: str, number: int, prefix: str, label: str) -> str:
    identifier = f'{prefix}{number}'
    return (f'<li{attributes} value="{number}" data-paper-number="{identifier}">'
            f'<span class="paper-number" aria-label="{escape(label)} {number}">'
            f'[{identifier}]</span>{body}</li>')


def summary(source: str, section: str, text: str) -> str:
    element = f'<p class="secondary paper-total" id="{section}-total"><strong>{escape(text)}</strong></p>'
    pattern = rf'<p\b[^>]*\bid="{section}-total"[^>]*>.*?</p>'
    if re.search(pattern, source, re.S):
        result, count = re.subn(pattern, lambda _: element, source, flags=re.S)
    else:
        heading = rf'(<h1\b[^>]*\bid="{section}-title"[^>]*>.*?</h1>)'
        result, count = re.subn(heading, lambda m: m[1] + '\n        ' + element, source, flags=re.S)
    if count != 1:
        raise ValueError(f'{section}: expected one count location')
    return result


def presentation(source: str, *, publication: bool) -> str:
    source = re.sub(r'\s*<style id="paper-list-presentation">.*?</style>', '', source, flags=re.S)
    # A new script URL avoids reuse of the old cached filter/renumbering code.
    source = re.sub(r'\s*<script\b[^>]*\bsrc="(?:script|paper-filters)\.js(?:\?[^"<>]*)?"[^>]*>\s*</script>', '', source, flags=re.S)
    addition = NUMBER_STYLE
    if publication:
        addition += f'  <script src="paper-filters.js?v={VERSION}" defer></script>\n'
    if source.count('</head>') != 1:
        raise ValueError('Expected one document head')
    return source.replace('</head>', addition + '</head>', 1)


def publications(source: str) -> str:
    papers = items(source, 'publication')
    if not papers:
        raise ValueError('Publication list is missing; refusing to remove it')
    known = {category for category, _, _ in CATEGORIES}
    if any(values.get('data-type') not in known for _, _, values in papers):
        raise ValueError('Unknown publication type requires review')
    identifiers = [values.get('id') for _, _, values in papers]
    if not all(identifiers) or len(set(identifiers)) != len(identifiers):
        raise ValueError('Every publication must have one unique existing ID')
    counts = {category: sum(v.get('data-type') == category for _, _, v in papers) for category in known}
    groups = []
    for category, prefix, label in CATEGORIES:
        selected = [(a, b) for a, b, v in papers if v.get('data-type') == category]
        n = len(selected)
        entries = [labelled_item(a, b, n-i, prefix, label) for i, (a, b) in enumerate(selected)]
        groups.append(
            f'<div class="publication-group" data-category="{category}" aria-labelledby="{category}-publications-title">\n'
            f'<h2 id="{category}-publications-title">{label} ({n})</h2>\n'
            f'<ol class="publication-list" reversed start="{n or 1}" role="list" aria-label="{label}">\n'
            + '\n'.join(entries) + '\n</ol>\n</div>')
    replacement = GROUP_BEGIN + '\n<div id="publication-list">\n' + '\n'.join(groups) + '\n</div>\n' + GROUP_END
    if GROUP_BEGIN in source or GROUP_END in source:
        if source.count(GROUP_BEGIN) != 1 or source.count(GROUP_END) != 1:
            raise ValueError('Incomplete publication group markers')
        pattern = re.escape(GROUP_BEGIN) + r'.*?' + re.escape(GROUP_END)
    else:
        pattern = r'<ol\b[^>]*\bid="publication-list"[^>]*>.*?</ol>'
    source, count = re.subn(pattern, lambda _: replacement, source, flags=re.S)
    if count != 1:
        raise ValueError('Expected one complete publication-list container')
    # Default to the complete, separately numbered categories, not a selected subset.
    button = re.compile(r'<button\b(?P<attrs>[^>]*\bdata-filter="(?P<filter>[^"]+)"[^>]*)>(?P<body>.*?)</button>', re.S)
    labels = {'selected': 'Selected', 'all': 'All', 'journal': 'Journals', 'conference': 'Conferences', 'book': 'Books'}
    counts['all'] = len(papers)
    counts['selected'] = sum(v.get('data-selected') == 'true' for _, _, v in papers)
    def update_button(match: re.Match[str]) -> str:
        name = match['filter']
        if name not in labels:
            raise ValueError('Unknown publication filter')
        attributes = remove_attrs(match['attrs'], 'aria-pressed')
        return f'<button{attributes} aria-pressed="{str(name == "all").lower()}">{labels[name]} <span>({counts[name]})</span></button>'
    source = button.sub(update_button, source)
    text = (f'Total: {len(papers)} publications — {counts["journal"]} journal articles, '
            f'{counts["conference"]} conference papers, and {counts["book"]} books and monographs.')
    return presentation(summary(source, 'publications', text), publication=True)


def preprints(source: str) -> str:
    block_pattern = re.compile(r'<(?P<tag>ol|ul)\b(?P<attrs>[^>]*\bclass="arxiv-list"[^>]*)>(?P<body>.*?)</(?P=tag)>', re.S)
    total = len(items(source, 'arxiv-paper'))
    remaining = total
    def number_block(match: re.Match[str]) -> str:
        nonlocal remaining
        papers = items(match['body'], 'arxiv-paper')
        start = remaining
        entries = []
        for attributes, body, _ in papers:
            entries.append(labelled_item(attributes, body, remaining, '', 'Preprint'))
            remaining -= 1
        attributes = remove_attrs(match['attrs'], 'start|reversed|role')
        return f'<ol{attributes} reversed start="{start or 1}" role="list">' + '\n'.join(entries) + '</ol>'
    source, count = block_pattern.subn(number_block, source)
    if count < 1 or remaining != 0:
        raise ValueError('Could not account for every arXiv paper')
    return presentation(summary(source, 'preprints', f'Total: {total} arXiv preprints.'), publication=False)


def expand_homepage(source: str) -> str:
    pattern = re.compile(r'<details\b(?P<attrs>[^>]*\bclass="background-details"[^>]*)>(?P<body>.*?)</details>', re.S)
    def expand(match: re.Match[str]) -> str:
        if '<details' in match['body']:
            raise ValueError('Nested homepage disclosure requires review')
        body, count = re.subn(r'\s*<summary\b[^>]*>.*?</summary>', '', match['body'], count=1, flags=re.S)
        if count != 1:
            raise ValueError('Expected one homepage disclosure label')
        return '<div class="background-details">' + body + '</div>'
    result = pattern.sub(expand, source)
    if re.search(r'<details\b', result):
        raise ValueError('A collapsed information section remains on the homepage')
    return result


def main() -> None:
    names = ('index.html', 'publications.html', 'preprints.html')
    original = {name: (ROOT / name).read_text(encoding='utf-8') for name in names}
    updated = {'index.html': expand_homepage(original['index.html']),
               'publications.html': publications(original['publications.html']),
               'preprints.html': preprints(original['preprints.html'])}
    # Verify citation contents and links by ID, independently of category order.
    for name, item_class in [('publications.html', 'publication'), ('preprints.html', 'arxiv-paper')]:
        before = {v['id']: body for _, body, v in items(original[name], item_class)}
        after = {v['id']: body for _, body, v in items(updated[name], item_class)}
        if before != after:
            raise ValueError(f'{name}: citation content changed; refusing to write')
    for name, content in updated.items():
        if content != original[name]:
            (ROOT / name).write_text(content, encoding='utf-8')
            print(f'Updated presentation: {name}')


if __name__ == '__main__':
    main()
