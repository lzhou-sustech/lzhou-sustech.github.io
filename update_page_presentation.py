#!/usr/bin/env python3
"""Keep paper lists reverse-numbered and the homepage biography fully visible.

Run after maintain_public_site.py. Only presentation in index.html,
publications.html, and preprints.html changes; citations, links, ordering, and
source metadata are preserved. Uses only the Python standard library.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NUMBER_STYLE = '''  <style id="paper-list-presentation">
    ol.publication-list, ol.arxiv-list {padding-left:2.6em;list-style-type:decimal;}
    .publication::marker, .arxiv-paper::marker {font-variant-numeric:tabular-nums;}
    .paper-total {margin:-8px 0 14px;}
  </style>
'''


def without_number_attributes(attributes: str) -> str:
    """Remove only attributes owned by this presentation pass."""
    return re.sub(
        r'''\s+(?:reversed|start|value)(?:\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+))?(?=\s|$)''',
        '', attributes, flags=re.I,
    )


def number_papers(source: str, *, list_class: str, item_class: str,
                  section: str, noun: str) -> str:
    # These existing paper lists have no nested lists. Refuse unexpected markup
    # instead of silently modifying or dropping a citation.
    block_pattern = re.compile(
        rf'<(?P<tag>ol|ul)\b(?P<attrs>[^>]*\bclass="{re.escape(list_class)}"[^>]*)>'
        rf'(?P<body>.*?)</(?P=tag)>', re.S,
    )
    item_pattern = re.compile(
        rf'<li\b(?P<attrs>[^>]*\bclass="{re.escape(item_class)}"[^>]*)>', re.S,
    )
    blocks = list(block_pattern.finditer(source))
    if not blocks:
        raise ValueError(f'{section}: expected at least one paper list')
    total = sum(len(item_pattern.findall(block['body'])) for block in blocks)
    remaining = total

    def number_block(block: re.Match[str]) -> str:
        nonlocal remaining
        body = block['body']
        if re.search(r'<(?:ol|ul)\b', body, flags=re.I):
            raise ValueError(f'{section}: nested paper list requires review')
        if len(re.findall(r'<li\b', body)) != len(item_pattern.findall(body)):
            raise ValueError(f'{section}: unrecognized list item requires review')
        start = remaining or 1

        def number_item(item: re.Match[str]) -> str:
            nonlocal remaining
            attributes = without_number_attributes(item['attrs'])
            replacement = f'<li{attributes} value="{remaining}">'
            remaining -= 1
            return replacement

        body = item_pattern.sub(number_item, body)
        attributes = without_number_attributes(block['attrs'])
        return f'<ol{attributes} reversed start="{start}">{body}</ol>'

    source = block_pattern.sub(number_block, source)
    if remaining != 0:
        raise ValueError(f'{section}: inconsistent paper count')
    summary_id = f'{section}-total'
    summary = f'<p class="secondary paper-total" id="{summary_id}"><strong>Total: {total} {noun}.</strong></p>'
    summary_pattern = rf'<p\b[^>]*\bid="{re.escape(summary_id)}"[^>]*>.*?</p>'
    if re.search(summary_pattern, source, flags=re.S):
        source, count = re.subn(summary_pattern, lambda _: summary, source, flags=re.S)
    else:
        heading_pattern = rf'(<h1\b[^>]*\bid="{re.escape(section)}-title"[^>]*>.*?</h1>)'
        source, count = re.subn(heading_pattern, lambda m: m[1] + '\n        ' + summary,
                                source, flags=re.S)
    if count != 1:
        raise ValueError(f'{section}: expected exactly one paper-count location')
    source = re.sub(r'  <style id="paper-list-presentation">.*?</style>\n?',
                    '', source, flags=re.S)
    if source.count('</head>') != 1:
        raise ValueError(f'{section}: expected one document head')
    return source.replace('</head>', NUMBER_STYLE + '</head>', 1)


def expand_homepage(source: str) -> str:
    pattern = re.compile(
        r'<details\b(?P<attrs>[^>]*\bclass="background-details"[^>]*)>'
        r'(?P<body>.*?)</details>', re.S,
    )

    def expand(match: re.Match[str]) -> str:
        if '<details' in match['body']:
            raise ValueError('Nested homepage disclosure requires review')
        body, count = re.subn(r'\s*<summary\b[^>]*>.*?</summary>', '', match['body'],
                              count=1, flags=re.S)
        if count != 1:
            raise ValueError('Expected one homepage disclosure label')
        return '<div class="background-details">' + body + '</div>'

    updated = pattern.sub(expand, source)
    if re.search(r'<details\b', updated):
        raise ValueError('A collapsed information section remains on the homepage')
    return updated


def main() -> None:
    originals = {name: (ROOT / name).read_text(encoding='utf-8')
                 for name in ('index.html', 'publications.html', 'preprints.html')}
    updated = {
        'index.html': expand_homepage(originals['index.html']),
        'publications.html': number_papers(
            originals['publications.html'], list_class='publication-list',
            item_class='publication', section='publications', noun='publications'),
        'preprints.html': number_papers(
            originals['preprints.html'], list_class='arxiv-list',
            item_class='arxiv-paper', section='preprints', noun='arXiv preprints'),
    }
    # Compute and validate every output before saving any change.
    for name, content in updated.items():
        if content != originals[name]:
            (ROOT / name).write_text(content, encoding='utf-8')
            print(f'Updated presentation: {name}')


if __name__ == '__main__':
    main()
