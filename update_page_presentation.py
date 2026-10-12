#!/usr/bin/env python3
"""Publish explicit descending labels, separate publication categories, and an open biography.

Run after maintain_public_site.py. Citation HTML and links are preserved verbatim.
Journal, magazine, conference, and book identifiers remain unchanged when visitors filter.
Preprints form one continuous visible list. Top-level total-count summaries are
omitted. Only the three presentation HTML files are written. No PDF or metadata
is changed.
"""
from __future__ import annotations

import re
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = 'magazines-20261012-1'
GROUP_BEGIN = '<!-- PUBLICATION-GROUPS:START -->'
GROUP_END = '<!-- PUBLICATION-GROUPS:END -->'
CATEGORIES = (
    ('book', 'B', 'Books and monographs'),
    ('magazine', 'M', 'Magazines'),
    ('journal', 'J', 'Journal articles'),
    ('conference', 'C', 'Conference papers'),
)
MAGAZINE_IDS = frozenset({
    'journal-lawn-survey-2026',
    'survey-fanets-2026',
    'survey-dd-isac-2024',
})
NUMBER_STYLE = '''  <style id="paper-list-presentation">
    ol.publication-list, ol.arxiv-list {padding-left:0;list-style:none;}
    li.publication, li.arxiv-paper {position:relative;list-style:none;padding-left:3.8em;}
    .paper-number {position:absolute;left:0;top:0;font-weight:700;font-variant-numeric:tabular-nums;white-space:nowrap;}
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


def remove_total_summary(source: str, section: str) -> str:
    """Remove the old page-level count sentence without touching paper labels."""
    pattern = rf'\s*<p\b[^>]*\bid="{section}-total"[^>]*>.*?</p>'
    return re.sub(pattern, '', source, flags=re.S)


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


def publication_category(values: dict[str, str | None], body: str) -> str:
    """Classify magazine, survey, and review pieces separately from journals."""
    category = values.get('data-type')
    if category not in {c for c, _, _ in CATEGORIES}:
        raise ValueError('Unknown publication type requires review')
    if category not in ('journal', 'magazine'):
        return str(category)
    # Explicit decisions for existing papers; titles and venues classify new ones.
    title_match = re.search(r'<span class="publication-title">(.*?)</span>', body, re.S)
    venue_match = re.search(r'<cite>(.*?)</cite>', body, re.S)
    title = re.sub(r'<[^>]*>', '', title_match[1]) if title_match else ''
    venue = re.sub(r'<[^>]*>', '', venue_match[1]) if venue_match else ''
    if (values.get('id') in MAGAZINE_IDS or
            re.search(r'\b(survey|review|tutorial)\b', title, re.I) or
            re.search(r'\bmagazine\b|\bIEEE Wireless Communications\b', venue, re.I)):
        return 'magazine'
    return str(category)


def publications(source: str) -> str:
    original_papers = items(source, 'publication')
    if not original_papers:
        raise ValueError('Publication list is missing; refusing to remove it')
    papers = []
    for attributes, body, values in original_papers:
        category = publication_category(values, body)
        attributes = re.sub(r'\bdata-type="[^"]+"', f'data-type="{category}"', attributes)
        papers.append((attributes, body, {**values, 'data-type': category}))
    known = {name for name, _, _ in CATEGORIES}
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
            f'<h2 id="{category}-publications-title">{label}</h2>\n'
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
    # Insert the magazine button when refreshing an older publication layout.
    if 'data-filter="magazine"' not in source:
        pattern = r'(<button\b[^>]*data-filter="journal"[^>]*>.*?</button>)'
        source, count = re.subn(
            pattern,
            lambda match: match[1] + '\n            <button type="button" data-filter="magazine">Magazines</button>',
            source, count=1, flags=re.S,
        )
        if count != 1:
            raise ValueError('Expected a journal filter to add Magazines')
    button = re.compile(r'<button\b(?P<attrs>[^>]*\bdata-filter="(?P<filter>[^"]+)"[^>]*)>(?P<body>.*?)</button>', re.S)
    labels = {'selected': 'Selected', 'all': 'All', 'journal': 'Journals', 'magazine': 'Magazines', 'conference': 'Conferences', 'book': 'Books'}
    counts['all'] = len(papers)
    counts['selected'] = sum(v.get('data-selected') == 'true' for _, _, v in papers)
    def update_button(match: re.Match[str]) -> str:
        name = match['filter']
        if name not in labels:
            raise ValueError('Unknown publication filter')
        attributes = remove_attrs(match['attrs'], 'aria-pressed')
        return f'<button{attributes} aria-pressed="{str(name == "all").lower()}">{labels[name]} <span>({counts[name]})</span></button>'
    source = button.sub(update_button, source)
    # Keep filter tabs in the same category order as the displayed sections.
    filter_group = re.compile(
        r'(?P<open><div class="filter-group"[^>]*>)(?P<body>.*?)(?P<close></div>)', re.S)
    def order_filter_buttons(match: re.Match[str]) -> str:
        seen = list(button.finditer(match['body']))
        desired = ('selected', 'all', 'book', 'magazine', 'journal', 'conference')
        by_name = {item['filter']: item[0] for item in seen}
        if len(seen) != len(desired) or set(by_name) != set(desired):
            raise ValueError('Expected one button per publication filter')
        return (match['open'] + '\n            ' +
                '\n            '.join(by_name[name] for name in desired) +
                '\n          ' + match['close'])
    source, group_count = filter_group.subn(order_filter_buttons, source, count=1)
    if group_count != 1:
        raise ValueError('Expected exactly one publication filter group')
    return presentation(remove_total_summary(source, 'publications'), publication=True)


def preprints(source: str) -> str:
    # Older papers belong in the same visible list, never a disclosure control.
    disclosure = re.compile(
        r'<details\b(?P<attrs>[^>]*)>(?P<body>.*?)</details>', re.S)

    def unwrap_older(match: re.Match[str]) -> str:
        values = attrs('<details' + match['attrs'] + '>')
        if 'older-arxiv' not in (values.get('class') or '').split():
            return match[0]
        if re.search(r'<details\b', match['body']):
            raise ValueError('Nested preprint disclosure requires review')
        body, count = re.subn(r'^\s*<summary\b[^>]*>.*?</summary>\s*', '',
                              match['body'], count=1, flags=re.S)
        if count != 1:
            raise ValueError('Expected one older-preprints disclosure label')
        return body

    source = disclosure.sub(unwrap_older, source)
    block_pattern = re.compile(
        r'<(?P<tag>ol|ul)\b(?P<attrs>[^>]*\bclass="arxiv-list"[^>]*)>'
        r'(?P<body>.*?)</(?P=tag)>', re.S)
    blocks = list(block_pattern.finditer(source))
    if not blocks:
        raise ValueError('Preprint list is missing; refusing to remove it')
    # Merge only adjacent lists. Unexpected content between lists is not deleted.
    for left, right in zip(blocks, blocks[1:]):
        if source[left.end():right.start()].strip():
            raise ValueError('Unexpected content between preprint lists requires review')
    papers = []
    for block in blocks:
        block_papers = items(block['body'], 'arxiv-paper')
        if (re.search(r'<(?:ol|ul)\b', block['body']) or
                len(re.findall(r'<li\b', block['body'])) != len(block_papers)):
            raise ValueError('Unexpected preprint-list structure requires review')
        papers.extend(block_papers)
    if len(papers) != len(items(source, 'arxiv-paper')):
        raise ValueError('Could not account for every arXiv paper')
    identifiers = [values.get('id') for _, _, values in papers]
    if not all(identifiers) or len(set(identifiers)) != len(identifiers):
        raise ValueError('Every preprint must have one unique existing ID')
    total = len(papers)
    entries = [labelled_item(a, b, total-i, '', 'Preprint')
               for i, (a, b, _) in enumerate(papers)]
    attributes = remove_attrs(blocks[0]['attrs'], 'start|reversed|role')
    replacement = (f'<ol{attributes} reversed start="{total or 1}" role="list">'
                   + '\n'.join(entries) + '</ol>')
    source = source[:blocks[0].start()] + replacement + source[blocks[-1].end():]
    return presentation(remove_total_summary(source, 'preprints'), publication=False)


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
