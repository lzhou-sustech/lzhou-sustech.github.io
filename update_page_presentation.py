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
from urllib.parse import urlsplit

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



# Publication features use the existing bibliography and preprints.
# The complete Publications Map, selected TIT citation list, and News feed
# are rebuilt from source citations during website updates.
ATLAS_START = '<!-- PUBLICATION-ATLAS:START -->'
ATLAS_END = '<!-- PUBLICATION-ATLAS:END -->'
HOME_ATLAS_START = '<!-- HOMEPAGE-ATLAS:START -->'
HOME_ATLAS_END = '<!-- HOMEPAGE-ATLAS:END -->'
HOME_NEWS_START = '<!-- HOMEPAGE-NEWS:START -->'
HOME_NEWS_END = '<!-- HOMEPAGE-NEWS:END -->'
ATLAS_CSS = 'publication-atlas.css?v=research-map-20261013-1'

# Complete-bibliography map, separate from the 10-paper TIT citation list.
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
        if not (title_markup and venue_markup and year_match and values.get('id')):
            raise ValueError('Incomplete publication citation: ' + str(values.get('id')))
        pub_id = str(values['id'])
        title = plain_text(title_anchor[2] if title_anchor else title_markup[1]).strip('“”')
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
            'publisherUrl': unescape(title_anchor[1]) if title_anchor else '',
            'forthcoming': bool(re.search(r'\(to appear\)', body, flags=re.I)),
            'arxivUrl': unescape(arxiv[1]) if arxiv else '',
            'theme': topic,
            'selected': values.get('data-selected') == 'true',
            'type': values.get('data-type'),
        })
    if not result or len({p['id'] for p in result}) != len(result):
        raise ValueError('Publication identities are missing or duplicated')
    return result


def selected_tit_markup(publication_source: str) -> str:
    """Render ten first-author or corresponding-author IEEE TIT citations.

    Reuse the published citation HTML and its stable journal identifier.
    A missing corresponding-author marker is not assumed to be present.
    """
    entries = []
    identifiers = set()
    for _, body, values in items(publication_source, 'publication'):
        if values.get('data-selected') != 'true':
            continue
        paper_id = values.get('id')
        number = values.get('data-paper-number')
        if not paper_id or not number or not re.fullmatch(r'J\d+', number):
            raise ValueError('Selected paper needs a stable journal identifier')
        if paper_id in identifiers:
            raise ValueError('Duplicate selected paper: ' + paper_id)
        identifiers.add(paper_id)
        if (values.get('data-type') != 'journal' or
                not re.search(r'<cite>\s*IEEE Transactions on Information Theory\s*</cite>',
                              body, re.S)):
            raise ValueError('Selected paper is not an IEEE TIT article: ' + paper_id)
        author_markup = body.split('<span class="publication-title">', 1)[0]
        first_author = bool(re.search(
            r'<p>\s*<strong>Lin Zhou</strong>', author_markup))
        corresponding = bool(re.search(
            r'<strong>Lin Zhou</strong>\s*<sup\b[^>]*class="corresponding-marker"',
            author_markup))
        if not (first_author or corresponding):
            raise ValueError('Selected paper lacks the required author role: ' + paper_id)

        title_match = re.search(r'<span class="publication-title">(.*?)</span>',
                                body, re.S)
        if not title_match:
            raise ValueError('Selected paper has no title: ' + paper_id)
        href = 'publications.html#' + escape(paper_id, quote=True)
        # Link forthcoming papers to their journal citation until a publisher
        # URL becomes available. Existing publisher and arXiv links are kept.
        if not re.search(r'<a\b', title_match[1]):
            body = body.replace(
                title_match[0],
                f'<span class="publication-title"><a href="{href}">'
                + title_match[1] + '</a></span>', 1)
        entries.append(
            '<li class="selected-tit-item">'
            f'<a class="selected-tit-number" href="{href}">[{escape(number)}]</a>'
            f'<div class="selected-tit-citation">{body}</div></li>'
        )
    if len(entries) != 10:
        raise ValueError(
            f'Expected 10 eligible selected IEEE TIT articles, got {len(entries)}')
    return (
        '<div id="selected-publications" class="home-feature selected-tit-section" '
        'aria-labelledby="selected-publications-title">'
        '<div class="home-feature-heading"><h2 id="selected-publications-title">'
        'Selected Publications</h2><a class="home-feature-link" '
        'href="publications.html">All publications →</a></div>'
        '<p class="home-feature-intro">Ten papers in <em>IEEE Transactions on '
        'Information Theory</em> for which I am first author or corresponding '
        'author. An asterisk marks corresponding authorship.</p>'
        '<ol class="selected-tit-list" role="list">'
        + '\n'.join(entries) +
        '</ol></div>'
    )


def news_date(value: str) -> tuple[int, int, int]:
    """Validate a source date without filling unknown months or days."""
    if not isinstance(value, str) or not re.fullmatch(
            r'\d{4}(?:-\d{2}(?:-\d{2})?)?', value):
        raise ValueError('Invalid News date: ' + repr(value))
    pattern = {4: '%Y', 7: '%Y-%m', 10: '%Y-%m-%d'}[len(value)]
    datetime.strptime(value, pattern)
    parts = [int(part) for part in value.split('-')]
    return tuple(parts + [0] * (3 - len(parts)))


def news_url(value: str) -> str:
    """Accept an explicit public HTTPS source, never executable markup."""
    if not isinstance(value, str):
        raise ValueError('News URLs must be strings')
    parsed = urlsplit(value)
    if (parsed.scheme != 'https' or not parsed.hostname or parsed.username
            or parsed.password or any(c.isspace() for c in value)):
        raise ValueError('News needs a public HTTPS URL: ' + repr(value))
    return value


def arxiv_identity(url: str) -> str:
    parsed = urlsplit(news_url(url))
    match = re.fullmatch(r'/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?(?:\.pdf)?/?',
                         parsed.path)
    if parsed.hostname not in ('arxiv.org', 'export.arxiv.org') or not match:
        raise ValueError('News needs an official arXiv paper URL: ' + url)
    return match[1]


def news_events(publication_source: str, preprint_source: str,
                ledger: dict | None) -> tuple[list[dict], str | None]:
    """Combine source-backed events with existing citation dates.

    The ledger records a publication check; rendering this page does not perform
    one. Year-only legacy citations sort after more precise dates in that year,
    while their visible dates retain their original precision.
    """
    papers = publication_details(publication_source)
    publications_by_id = {paper['id']: paper for paper in papers}
    arxiv_by_record = {}
    for paper in papers:
        if paper['arxivUrl']:
            identity = arxiv_identity(paper['arxivUrl'])
            arxiv_by_record[paper['id']] = identity
            arxiv_by_record['arxiv-' + identity.replace('.', '-')] = identity
    submissions = {}
    for _, body, values in items(preprint_source, 'arxiv-paper'):
        if 'preprint-working' in (values.get('class') or '').split():
            continue
        title_markup = re.search(
            r'<span class="publication-title">(.*?)</span>', body, re.S)
        submitted = re.search(
            r'<time\b[^>]*datetime="(\d{4}-\d{2}-\d{2})"', body)
        arxiv_links = [attrs(anchor)['href'] for anchor in re.findall(
            r'<a\b[^>]*>', body) if 'publication-arxiv' in
            (attrs(anchor).get('class') or '').split()]
        if not (title_markup and submitted and len(arxiv_links) == 1 and values.get('id')):
            raise ValueError('Missing arXiv citation field: ' + str(values.get('id')))
        url = str(arxiv_links[0])
        identity = arxiv_identity(url)
        news_date(submitted[1])
        if identity in submissions:
            raise ValueError('Duplicate arXiv citation: ' + identity)
        arxiv_by_record[str(values['id'])] = identity
        arxiv_by_record['arxiv-' + identity.replace('.', '-')] = identity
        submissions[identity] = {
            'id': 'arxiv-submission-' + identity,
            'recordId': str(values['id']), 'kind': 'arxiv-submission',
            'date': submitted[1], 'title': plain_text(title_markup[1]).strip('“”.'),
            'url': url,
        }

    events = []
    checked = None
    ledger_submissions = set()
    covered_publications = set()
    if ledger is not None:
        if (not isinstance(ledger, dict) or type(ledger.get('schemaVersion')) is not int
                or ledger['schemaVersion'] != 1):
            raise ValueError('Unsupported publication-news.json schemaVersion')
        checked = ledger.get('lastChecked')
        news_date(checked)
        if len(checked) != 10 or not isinstance(ledger.get('events'), list):
            raise ValueError('News ledger needs an exact lastChecked date and events list')
        identifiers, event_keys = set(), set()
        kinds = {'arxiv-submission', 'arxiv-revision', 'publication-online',
                 'publication-issue', 'publication-verified', 'accepted'}
        for event in ledger['events']:
            if not isinstance(event, dict):
                raise ValueError('News events must be objects')
            for field in ('id', 'recordId', 'kind', 'date', 'title', 'url'):
                if not isinstance(event.get(field), str) or not event[field].strip():
                    raise ValueError('Missing News event field: ' + field)
            identifier, kind, record = event['id'], event['kind'], event['recordId']
            if identifier in identifiers or not re.fullmatch(r'[A-Za-z0-9._:-]+', identifier):
                raise ValueError('Invalid or duplicate News event ID: ' + identifier)
            identifiers.add(identifier)
            if kind not in kinds:
                raise ValueError('Unknown News event kind: ' + kind)
            if news_date(event['date']) > news_date(checked):
                raise ValueError('News event is later than its source check: ' + identifier)
            news_url(event['url'])
            sources = event.get('sources')
            if not isinstance(sources, list) or not sources:
                raise ValueError('News event needs primary sources: ' + identifier)
            for source in sources:
                news_url(source)
            if event.get('venue') is not None and not isinstance(event['venue'], str):
                raise ValueError('News event venue must be text: ' + identifier)
            if kind.startswith('arxiv-'):
                identity = arxiv_identity(event['url'])
                if arxiv_by_record.get(record) != identity:
                    raise ValueError('News arXiv event does not match its paper: ' + identifier)
                if not any(arxiv_identity(source) == identity for source in sources
                           if urlsplit(source).hostname in ('arxiv.org', 'export.arxiv.org')):
                    raise ValueError('News arXiv event needs its own arXiv source: ' + identifier)
                key = (identity, kind, event['date'] if kind == 'arxiv-revision' else '')
                if kind == 'arxiv-submission':
                    if identity in submissions and event['date'] != submissions[identity]['date']:
                        raise ValueError('News and Preprints submission dates disagree: ' + identifier)
                    ledger_submissions.add(identity)
            else:
                if record not in publications_by_id:
                    raise ValueError('Unknown News publication record: ' + record)
                paper = publications_by_id[record]
                if kind != 'accepted' and paper['forthcoming']:
                    raise ValueError('A forthcoming citation cannot be announced as published: ' + record)
                if kind == 'publication-verified':
                    if len(event['date']) != 10:
                        raise ValueError('Publication verification needs an exact check date: ' + identifier)
                    known_url = paper['publisherUrl'].rstrip('/')
                    if event['url'].rstrip('/') != known_url:
                        raise ValueError('Verified publication must link to its publisher citation: ' + identifier)
                    if 'publicationYear' in event and (
                            type(event['publicationYear']) is not int or
                            not 1000 <= event['publicationYear'] <= 9999):
                        raise ValueError('Invalid publication year: ' + identifier)
                if 'IEEE' in paper['venue']:
                    hosts = [urlsplit(source).hostname or '' for source in sources]
                    if not any(host == 'ieee.org' or host.endswith('.ieee.org') or
                               host in ('api.crossref.org', 'doi.org') for host in hosts):
                        raise ValueError('IEEE News needs a publisher or DOI source: ' + identifier)
                # Once an exact online date is known, replace the verification
                # event instead of announcing the same publication twice.
                key = (record, 'publication-online' if kind == 'publication-verified' else kind, '')
                covered_publications.add(record)
            if key in event_keys:
                raise ValueError('Duplicate News event for a paper: ' + identifier)
            event_keys.add(key)
            events.append(dict(event))

    events.extend(event for identity, event in submissions.items()
                  if identity not in ledger_submissions)
    # Retain familiar historical summaries until their verified event dates are
    # recorded. The publication year is not presented as an online/acceptance date.
    for paper in [p for p in papers if p['type'] == 'journal'][:3]:
        if paper['id'] not in covered_publications:
            events.append({
                'id': 'publication-summary-' + paper['id'], 'recordId': paper['id'],
                'kind': 'forthcoming-summary' if paper['forthcoming'] else 'publication-summary',
                'date': str(paper['year']), 'title': paper['title'].rstrip('.'),
                'url': paper['publisherUrl'] or ('publications.html#' + paper['id']),
                'venue': paper['venue'],
            })
    events.sort(key=lambda event: (news_date(event['date']), event['id']), reverse=True)
    return events, checked


def news_markup(publication_source: str, preprint_source: str,
                ledger: dict | None = None) -> str:
    """Render one chronological feed from verified, distinct paper events."""
    ledger_path = ROOT / 'publication-news.json'
    if ledger is None and ledger_path.is_file():
        ledger = json.loads(ledger_path.read_text(encoding='utf-8'))
    events, checked = news_events(publication_source, preprint_source, ledger)
    labels = {
        'arxiv-submission': 'New arXiv preprint',
        'arxiv-revision': 'Revised arXiv preprint',
        'publication-online': 'Published online',
        'publication-issue': 'Journal issue publication',
        'publication-verified': 'Online publication verified',
        'accepted': 'Accepted / forthcoming',
        'forthcoming-summary': 'Forthcoming journal article',
        'publication-summary': 'Journal publication',
    }
    entries = []
    for event in events:
        date = event['date']
        pattern = {4: '%Y', 7: '%Y-%m', 10: '%Y-%m-%d'}[len(date)]
        display = datetime.strptime(date, pattern).strftime(
            {4: '%Y', 7: '%b %Y', 10: '%d %b %Y'}[len(date)]).lstrip('0')
        if event['kind'] == 'publication-verified':
            display = 'Verified ' + display
        label = labels[event['kind']]
        if event.get('venue'):
            label += ' · ' + event['venue']
        title = event['title'].rstrip('.')
        ending = '' if title.endswith(('?', '!')) else '.'
        entries.append(
            '<li class="news-entry" data-news-id="' + escape(event['id'], quote=True) + '">'
            f'<time class="news-date" datetime="{date}">{display}</time>'
            f'<div class="news-copy"><p class="news-type">{escape(label)}</p>'
            f'<a href="{escape(event["url"], quote=True)}">{escape(title)}</a>{ending}'
            '</div></li>')
    html_news = '<ul class="news-feed">' + '\n'.join(entries[:6]) + '</ul>'
    if len(entries) > 6:
        html_news += ('<details class="news-older"><summary>Earlier publication updates</summary>'
                      '<ul class="news-feed">' + '\n'.join(entries[6:]) + '</ul></details>')
    check_note = ''
    if checked:
        display = datetime.strptime(checked, '%Y-%m-%d').strftime('%d %b %Y').lstrip('0')
        check_note = (f'Last publication check: <time datetime="{checked}">{display}</time>. ')
    return (
        '<div id="news" class="home-feature" aria-labelledby="news-title">'
        '<div class="home-feature-heading"><h2 id="news-title">News</h2>'
        '<a class="home-feature-link" href="preprints.html">Preprints →</a></div>'
        '<p class="news-intro">Preprints, revisions, and formal publications, newest first. '
        '“Verified” marks when a publication record was confirmed if its exact online '
        'publication date is unavailable.</p>'
        + html_news + '<p class="news-meta-note">' + check_note +
        'See <a href="preprints.html">Preprints</a> and '
        '<a href="publications.html">Publications</a> for the full records.</p></div>'
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
    # The shared stylesheet also provides homepage News and list formatting.
    link = f'<link rel="stylesheet" href="{ATLAS_CSS}">'
    if 'publication-atlas.css?' not in source:
        source = source.replace('</head>', '  ' + link + '\n</head>', 1)
    # No second interactive atlas: retain only the complete Publications Map.
    source = re.sub(
        r'\s*<script src="publication-atlas\.js\?[^"]+" defer></script>',
        '', source)
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
    homepage = marked_area(
        homepage, HOME_ATLAS_START, HOME_ATLAS_END,
        selected_tit_markup(publications_page),
        insert_before='      </section>\n      <footer>'
    )
    homepage = marked_area(
        homepage, HOME_NEWS_START, HOME_NEWS_END,
        news_markup(publications_page, preprints_page),
        insert_before='      </section>\n      <footer>'
    )
    # Keep homepage quicklinks without modifying the six-page navigation.
    if 'id="home-quicklinks"' not in homepage:
        anchor = '        <div id="about">'
        links = ('        <div id="home-quicklinks" class="home-quicklinks">'
                 '<a href="#selected-publications">Selected Publications</a>'
                 '<a href="#news">News</a></div>\n')
        if homepage.count(anchor) != 1:
            raise ValueError('Cannot locate homepage About section')
        homepage = homepage.replace(anchor, links + anchor, 1)
    # Retire the second, redundant Selected Publications visualization.
    # The Publications page keeps the full map and Selected (10) filter.
    if ATLAS_START in publications_page or ATLAS_END in publications_page:
        if (publications_page.count(ATLAS_START) != 1 or
                publications_page.count(ATLAS_END) != 1):
            raise ValueError('Incomplete legacy selected-map markers')
        publications_page = re.sub(
            re.escape(ATLAS_START) + r'.*?' + re.escape(ATLAS_END),
            '', publications_page, count=1, flags=re.S)
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

