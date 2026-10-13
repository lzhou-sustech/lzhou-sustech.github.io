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
import json
from datetime import datetime
from html import escape, unescape
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
    # Only the biography must be permanently expanded. News archive disclosures
    # are intentional and must be preserved across subsequent site refreshes.
    if re.search(r'<details\b[^>]*\bclass="background-details"', result):
        raise ValueError('A collapsed biography section remains on the homepage')
    return result



# The two dynamic homepage features use the paper citations already published here.
# Changing a publication's selection or adding a preprint automatically refreshes
# the interactive research map and the News feed on the next site build.
ATLAS_START = '<!-- PUBLICATION-ATLAS:START -->'
ATLAS_END = '<!-- PUBLICATION-ATLAS:END -->'
HOME_ATLAS_START = '<!-- HOMEPAGE-ATLAS:START -->'
HOME_ATLAS_END = '<!-- HOMEPAGE-ATLAS:END -->'
HOME_NEWS_START = '<!-- HOMEPAGE-NEWS:START -->'
HOME_NEWS_END = '<!-- HOMEPAGE-NEWS:END -->'
ATLAS_SCRIPT = 'publication-atlas.js?v=research-map-20261013-1'
ATLAS_CSS = 'publication-atlas.css?v=research-map-20261013-1'

# Complete-bibliography map, separate from the 10-paper selected research atlas.
HOME_FULL_MAP_START = '<!-- HOMEPAGE-PUBLICATIONS-MAP:START -->'
HOME_FULL_MAP_END = '<!-- HOMEPAGE-PUBLICATIONS-MAP:END -->'
PAGE_FULL_MAP_START = '<!-- PAGE-PUBLICATIONS-MAP:START -->'
PAGE_FULL_MAP_END = '<!-- PAGE-PUBLICATIONS-MAP:END -->'
FULL_MAP_SCRIPT = 'publications-map.js?v=all-papers-map-20261013-1'
FULL_MAP_CSS = 'publications-map.css?v=all-papers-map-20261013-1'

PAPER_THEMES = {
    'journal-covert-key-generation-2026': 3,
    'journal-multiple-moving-targets-2026': 2,
    'journal-continuous-outlier-2025': 1,
    'journal-mac-rac-2025': 3,
    'journal-sequential-outlier-2025': 1,
    'journal-shannon-cipher-2025': 0,
    'journal-sequence-matching-2024': 1,
    'journal-gaussian-refinement-2023': 0,
    'journal-gray-wyner-2017': 0,
    'journal-successive-refinement-2017': 0,
}


def plain_text(fragment: str) -> str:
    """Extract the visible citation text without introducing new metadata."""
    fragment = re.sub(r'<sup\b[^>]*>.*?</sup>', '', fragment, flags=re.S)
    return ' '.join(unescape(re.sub(r'<[^>]+>', '', fragment)).split())


def publication_details(source: str) -> list[dict]:
    result = []
    for _, body, values in items(source, 'publication'):
        title_markup = re.search(
            r'<span class="publication-title">(.*?)</span>', body, flags=re.S)
        title_anchor = re.search(
            r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', title_markup[1], flags=re.S
        ) if title_markup else None
        venue_markup = re.search(r'<cite>(.*?)</cite>', body, flags=re.S)
        year_match = re.search(r'\b(20\d{2})\.', body)
        if not (title_anchor and venue_markup and year_match and values.get('id')):
            raise ValueError('Incomplete publication citation: ' + str(values.get('id')))
        pub_id = str(values['id'])
        title = plain_text(title_anchor[2]).strip('“”')
        authors_markup = body.split('<span class="publication-title">', 1)[0]
        authors = plain_text(authors_markup).strip().rstrip('.')
        arxiv = re.search(
            r'<a\b[^>]*class="publication-arxiv"[^>]*href="([^"]+)"',
            body, flags=re.S)
        # Some older records place class after href; retain the exact source URL.
        if not arxiv:
            arxiv = re.search(
                r'<a\b[^>]*href="([^"]+)"[^>]*class="publication-arxiv"',
                body, flags=re.S)
        topic = PAPER_THEMES.get(pub_id)
        if topic is None:
            words = title.lower()
            if any(k in words for k in ('outlier', 'matching', 'classification', 'detection')):
                topic = 1
            elif any(k in words for k in ('questions', 'target', 'adaptive search')):
                topic = 2
            elif any(k in words for k in ('covert', 'secret key', 'multi-access', 'mac and rac')):
                topic = 3
            else:
                topic = 0
        result.append({
            'id': pub_id,
            'number': str(values.get('data-paper-number') or ''),
            'title': title,
            'authors': authors,
            'venue': plain_text(venue_markup[1]),
            'year': int(year_match[1]),
            'publisherUrl': unescape(title_anchor[1]),
            'arxivUrl': unescape(arxiv[1]) if arxiv else '',
            'theme': topic,
            'selected': values.get('data-selected') == 'true',
            'type': values.get('data-type'),
        })
    if not result or len({p['id'] for p in result}) != len(result):
        raise ValueError('Publication identities are missing or duplicated')
    return result


def build_atlas_data(publication_source: str) -> str:
    selected = [paper for paper in publication_details(publication_source)
                if paper['selected']]
    if not selected:
        raise ValueError('Research map requires at least one selected paper')
    # The location of an SVG dot is determined by year and theme, not a metric.
    public = [{k: p[k] for k in (
        'id', 'title', 'authors', 'venue', 'year',
        'publisherUrl', 'arxivUrl', 'theme')} for p in selected]
    return json.dumps(public, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c')


def atlas_markup(data: str, *, homepage: bool) -> str:
    if homepage:
        title = ('<div class="home-feature-heading"><h2 id="selected-publications-title">'
                 'Selected Publications</h2><a class="home-feature-link" '
                 'href="publications.html">All publications →</a></div>'
                 '<p class="home-feature-intro">Explore selected '
                 'IEEE Transactions on Information Theory papers by research '
                 'theme and publication year. Each point opens its citation '
                 'and links.</p>')
        opener = '<div id="selected-publications" class="home-feature" aria-labelledby="selected-publications-title">'
        closer = '</div>'
    else:
        title = ('<h2 class="atlas-section-title" id="selected-map-title">Research map</h2>'
                 '<p class="home-feature-intro">Your selected papers organized '
                 'by research theme and publication year. Choose a dot to '
                 'see its citation and publisher links.</p>')
        opener = ('<div id="selected-publication-visualization" '
                  'aria-labelledby="selected-map-title" hidden>')
        closer = '</div>'
    controls = (
        '<div class="publication-atlas" data-publication-atlas>'
        '<div class="atlas-toolbar">'
        '<div class="atlas-switch" role="group" aria-label="Publication view">'
        '<button type="button" data-atlas-mode="map" aria-pressed="true">Map</button>'
        '<button type="button" data-atlas-mode="list" aria-pressed="false">List</button>'
        '</div>'
        '<p class="atlas-caption">Theme × year · select a point to explore a paper</p>'
        '</div>'
        '<div class="atlas-map" data-atlas-map></div>'
        '<ol class="atlas-list" data-atlas-list hidden></ol>'
        '<div class="atlas-detail" data-atlas-detail aria-label="Selected paper details"></div>'
        '<p class="atlas-fallback">See the complete citations in '
        '<a href="publications.html">Publications</a>.</p>'
        '</div>'
    )
    return (opener + '\n' + title + '\n' + controls + '\n'
            + '<script id="publication-atlas-data" type="application/json">'
            + data + '</script>\n' + closer)


def news_markup(publication_source: str, preprint_source: str) -> str:
    entries = []
    for _, body, values in items(preprint_source, 'arxiv-paper')[:4]:
        title_markup = re.search(
            r'<span class="publication-title">(.*?)</span>', body, flags=re.S)
        title_anchor = re.search(
            r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', title_markup[1], flags=re.S
        ) if title_markup else None
        submitted = re.search(r'<time\b[^>]*datetime="(\d{4}-\d{2}-\d{2})"', body)
        arxiv = re.search(
            r'<a\b[^>]*class="publication-arxiv"[^>]*href="([^"]+)"',
            body, flags=re.S)
        if not (title_anchor and submitted and arxiv):
            raise ValueError('Missing arXiv citation field: ' + str(values.get('id')))
        date = datetime.strptime(submitted[1], '%Y-%m-%d')
        entries.append(
            '<li class="news-entry">'
            f'<time class="news-date" datetime="{date.strftime("%Y-%m")}">'
            f'{date.strftime("%b %Y")}</time>'
            '<div class="news-copy"><p class="news-type">New arXiv preprint</p>'
            f'<a href="{escape(unescape(arxiv[1]), quote=True)}">'
            f'{escape(plain_text(title_anchor[2]))}</a>.</div></li>'
        )
    journals = [p for p in publication_details(publication_source)
                if p['type'] == 'journal'][:3]
    for paper in journals:
        entries.append(
            '<li class="news-entry">'
            f'<time class="news-date" datetime="{paper["year"]}">'
            f'{paper["year"]}</time>'
            f'<div class="news-copy"><p class="news-type">Journal publication · '
            f'{escape(paper["venue"])}</p>'
            f'<a href="{escape(paper["publisherUrl"], quote=True)}">'
            f'{escape(paper["title"])}</a>.</div></li>'
        )
    if not entries:
        return '<p class="secondary">Publication updates will appear here.</p>'
    latest = entries[:6]
    older = entries[6:]
    html_news = '<ul class="news-feed">' + '\n'.join(latest) + '</ul>'
    if older:
        html_news += ('<details class="news-older"><summary>Earlier publication updates</summary>'
                      '<ul class="news-feed">' + '\n'.join(older) + '</ul></details>')
    return (
        '<div id="news" class="home-feature" aria-labelledby="news-title">'
        '<div class="home-feature-heading"><h2 id="news-title">News</h2>'
        '<a class="home-feature-link" href="preprints.html">Preprints →</a></div>'
        '<p class="news-intro">Recent papers from my arXiv and publication lists. '
        'Preprint dates are submission dates; journal entries show publication '
        'years rather than acceptance dates.</p>'
        + html_news +
        '<p class="news-meta-note">This feed is refreshed whenever the '
        '<a href="preprints.html">Preprints</a> or '
        '<a href="publications.html">Publications</a> page is updated.</p>'
        '</div>'
    )


def marked_area(source: str, start: str, end: str, markup: str,
                *, insert_before: str) -> str:
    block = start + '\n' + markup + '\n' + end
    if start in source or end in source:
        if source.count(start) != 1 or source.count(end) != 1:
            raise ValueError('Incomplete feature markers: ' + start)
        regex = re.escape(start) + r'.*?' + re.escape(end)
        return re.sub(regex, lambda _: block, source, count=1, flags=re.S)
    if source.count(insert_before) != 1:
        raise ValueError('Cannot find a unique feature placement for ' + start)
    return source.replace(insert_before, block + '\n' + insert_before, 1)


def feature_scripts(source: str) -> str:
    link = f'<link rel="stylesheet" href="{ATLAS_CSS}">'
    script = f'<script src="{ATLAS_SCRIPT}" defer></script>'
    if 'publication-atlas.css?' not in source:
        source = source.replace('</head>', '  ' + link + '\n</head>', 1)
    if 'publication-atlas.js?' not in source:
        source = source.replace('</head>', '  ' + script + '\n</head>', 1)
    full_css = f'<link rel="stylesheet" href="{FULL_MAP_CSS}">'
    full_script = f'<script src="{FULL_MAP_SCRIPT}" defer></script>'
    if 'publications-map.css?' not in source:
        source = source.replace('</head>', '  ' + full_css + '\n</head>', 1)
    if 'publications-map.js?' not in source:
        source = source.replace('</head>', '  ' + full_script + '\n</head>', 1)
    return source



def full_map_theme(paper: dict) -> int:
    """Group works by the research subject of the title (not journal quality)."""
    title = paper['title'].lower()
    # Query/search work is grouped together, including privacy-search tradeoffs.
    if any(phrase in title for phrase in (
            '20 questions', 'twenty questions', 'moving target',
            'multiple targets', 'beam alignment', 'adaptive querying',
            'adaptive noisy', 'querying')):
        return 2
    if any(phrase in title for phrase in (
            'covert', 'secret', 'privacy', 'cipher', 'maximal leakage',
            'key generation', 'physical-layer security')):
        return 3
    if any(phrase in title for phrase in (
            'outlier', 'hypothesis testing', 'hypothesis test',
            'statistical sequence matching', 'statistical classification',
            'distributed detection', 'outlying sequence',
            'identification with lossy recovery', 'm-ary classification',
            'binary classification')):
        return 1
    if any(phrase in title for phrase in (
            'source coding', 'rate-distortion', 'rate distortion',
            'gray-wyner', 'wyner-ziv', 'successive refinement',
            'joint source-channel', 'jscc', 'lossy recovery',
            'lossy multi-connectivity', 'gaussian codebooks',
            'streaming compression', 'streaming slepian-wolf',
            'kaspi problem', 'multiple description coding',
            'finite blocklength lossy', 'slepian-wolf',
            'codebooks for arbitrary sources')):
        return 0
    return 4


def build_full_publications_map_data(publications_page: str) -> tuple[str, int, int, int]:
    papers = publication_details(publications_page)
    if not papers:
        raise ValueError('Cannot draw a complete publications map without papers')
    types = {'journal', 'conference', 'magazine', 'book'}
    if any(paper['type'] not in types for paper in papers):
        raise ValueError('Unknown publication type in publications map')
    for paper in papers:
        paper['mapTheme'] = full_map_theme(paper)
        if not paper['number']:
            raise ValueError('Missing canonical publication number: ' + paper['id'])
    fields = ('id', 'number', 'title', 'authors', 'venue', 'year',
              'publisherUrl', 'arxivUrl', 'type', 'mapTheme')
    data = [{key: paper[key] for key in fields} for paper in papers]
    rendered = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    return rendered.replace('<', '\\u003c'), len(data), min(
        p['year'] for p in papers), max(p['year'] for p in papers)


def full_map_markup(data: str, count: int, first_year: int,
                    last_year: int, *, homepage: bool) -> str:
    if homepage:
        opener = ('<div id="publications-map" class="home-feature full-map-section" '
                  'aria-labelledby="publications-map-title">')
        intro = (
            '<div class="home-feature-heading">'
            '<h2 id="publications-map-title">Publications Map</h2>'
            '<a class="home-feature-link" href="publications.html">'
            'View publications →</a></div>'
        )
    else:
        opener = ('<div id="publication-map-on-publications" '
                  'class="full-map-section" '
                  'aria-labelledby="full-publication-map-title">')
        intro = (
            '<div class="home-feature-heading">'
            '<h2 id="full-publication-map-title">Publications Map</h2>'
            '<a class="home-feature-link" href="#publication-list">'
            'Full publication list ↓</a></div>'
        )
    summary = (
        '<p class="home-feature-intro">Explore all '
        f'{count} published works by research topic and year. '
        'Bubble numbers show how many works belong to each group. '
        'Select one to see the papers and their links. '
        'Topic assignments are approximate; arXiv-only preprints are listed separately.</p>'
    )
    controls = (
        '<div class="full-map-shell" data-full-publications-map>'
        '<div class="full-map-topbar">'
        '<div class="full-map-mode" role="group" aria-label="Publications map mode">'
        '<button type="button" data-full-map-mode="map" aria-pressed="true">Map</button>'
        '<button type="button" data-full-map-mode="list" aria-pressed="false">List</button>'
        '</div>'
        f'<p class="full-map-meta">{count} works · '
        f'{first_year}–{last_year}</p></div>'
        '<div class="full-map-filters" data-full-map-filters '
        'role="group" aria-label="Filter the map by publication type"></div>'
        '<div class="full-map-chart" data-full-map-chart></div>'
        '<ol class="full-map-list" data-full-map-list hidden></ol>'
        '<div class="full-map-detail" data-full-map-detail '
        'aria-label="Publication group details" aria-live="polite"></div>'
        '<p class="full-map-fallback">Browse the full bibliography at '
        '<a href="publications.html">Publications</a>.</p>'
        '<script type="application/json" data-full-map-data>'
        + data +
        '</script></div>'
    )
    return opener + '\n' + intro + '\n' + summary + '\n' + controls + '\n</div>'


def update_research_features(homepage: str, publications_page: str,
                             preprints_page: str) -> tuple[str, str]:
    data = build_atlas_data(publications_page)
    homepage = marked_area(
        homepage, HOME_ATLAS_START, HOME_ATLAS_END,
        atlas_markup(data, homepage=True),
        insert_before='      </section>\n      <footer>'
    )
    homepage = marked_area(
        homepage, HOME_NEWS_START, HOME_NEWS_END,
        news_markup(publications_page, preprints_page),
        insert_before='      </section>\n      <footer>'
    )
    # Add small navigation anchors without altering the seven-page sidebar.
    if 'id="home-quicklinks"' not in homepage:
        anchor = '        <div id="about">'
        links = ('        <div id="home-quicklinks" class="home-quicklinks">'
                 '<a href="#selected-publications">Selected Publications</a>'
                 '<a href="#news">News</a></div>\n')
        if homepage.count(anchor) != 1:
            raise ValueError('Cannot locate homepage About section')
        homepage = homepage.replace(anchor, links + anchor, 1)
    publications_page = marked_area(
        publications_page, ATLAS_START, ATLAS_END,
        atlas_markup(data, homepage=False),
        insert_before='        <!-- PUBLICATION-GROUPS:START -->'
    )
    all_data, n_all, oldest, newest = build_full_publications_map_data(publications_page)
    homepage = marked_area(
        homepage, HOME_FULL_MAP_START, HOME_FULL_MAP_END,
        full_map_markup(all_data, n_all, oldest, newest, homepage=True),
        insert_before=HOME_ATLAS_START
    )
    publications_page = marked_area(
        publications_page, PAGE_FULL_MAP_START, PAGE_FULL_MAP_END,
        full_map_markup(all_data, n_all, oldest, newest, homepage=False),
        insert_before='        <div class="publication-tools" id="publication-tools" hidden>'
    )
    # Keep quick navigation aligned with the on-page section order.
    if '<a href="#publications-map">Publications Map</a>' not in homepage:
        selected_link = '<a href="#selected-publications">Selected Publications</a>'
        if homepage.count(selected_link) != 1:
            raise ValueError('Could not locate selected-publications navigation link')
        homepage = homepage.replace(
            selected_link,
            '<a href="#publications-map">Publications Map</a>' + selected_link,
            1
        )
    return feature_scripts(homepage), feature_scripts(publications_page)


def main() -> None:
    names = ('index.html', 'publications.html', 'preprints.html')
    original = {name: (ROOT / name).read_text(encoding='utf-8') for name in names}
    updated = {'index.html': expand_homepage(original['index.html']),
               'publications.html': publications(original['publications.html']),
               'preprints.html': preprints(original['preprints.html'])}
    updated['index.html'], updated['publications.html'] = update_research_features(
        updated['index.html'], updated['publications.html'], updated['preprints.html'])
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
