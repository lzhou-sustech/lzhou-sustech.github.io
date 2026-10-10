#!/usr/bin/env python3
"""Regenerate index.html from content.json. Uses Python's standard library only."""
import json
import os
import re
from datetime import date
from urllib.parse import quote, urlsplit
from html import escape
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent
DATA = json.loads((ROOT / 'content.json').read_text(encoding='utf-8'))
p = DATA['profile']

def e(value):
    return escape(str(value), quote=True)

def link(url, label, class_name=''):
    return f'<a class="{e(class_name)}" href="{e(url)}">{e(label)}</a>'

def person_authors(value, corresponding=False):
    name = '<strong>Lin Zhou</strong>'
    if corresponding is True:
        name += '<sup class="corresponding-marker" title="Corresponding author" aria-label="Corresponding author">*</sup>'
    return re.sub(r'(?<!\w)Lin Zhou(?!\w)', lambda match: name, e(value))

def publication(item):
    search = ' '.join(str(item.get(k, '')) for k in ['title', 'authors', 'year', 'venue', 'topic'])
    title = link(item['url'], item['title']) if item.get('url') else e(item['title'])
    details = ', ' + e(item['details']) if item.get('details') else ''
    status = ' <span class="status">To appear.</span>' if item['status'] == 'accepted' else ''
    kind = ' <span class="publication-kind">[Book / monograph]</span>' if item['type'] == 'book' else ''
    publisher_label = '[IEEE]' if urlsplit(item.get('url', '')).hostname == 'ieeexplore.ieee.org' else '[Publisher]'
    publisher_link = ' ' + link(item['url'], publisher_label, 'publication-publisher') if item.get('url') else ''
    arxiv_links = ''.join(' ' + link(record['url'], '[arXiv]', 'publication-arxiv') for record in PUBLICATION_ARXIV.get(item['id'], []))
    return f'''<li class="publication" id="{e(item['id'])}" data-type="{e(item['type'])}" data-selected="{str(item['selected']).lower()}" data-search="{e(search)}"><p>{person_authors(item['authors'], corresponding=(item['type'] == 'journal' and item.get('correspondingAuthor') is True))}. <span class="publication-title">“{title}.”</span> <cite>{e(item['venue'])}</cite>{details}, {e(item['year'])}.{status}{kind}{publisher_link}{arxiv_links}</p></li>'''

def secure_https(value, field):
    """Accept an explicit HTTPS URL, with no credentials or control characters."""
    if not isinstance(value, str) or not value or any(c.isspace() or ord(c) < 32 for c in value) or '\\' in value:
        raise ValueError(f'{field} must be a valid HTTPS URL.')
    parsed = urlsplit(value)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError(f'{field} must be a valid HTTPS URL without credentials.')
    try:
        parsed.port
    except ValueError as exc:
        raise ValueError(f'{field} has an invalid port.') from exc
    return value


def load_publications():
    """Each JSON file is canonical; deleting it permanently removes the listing."""
    directory = ROOT / 'publications'
    if not directory.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError('publications/ must remain inside the repository.')
    items = []
    for path in sorted(directory.glob('*.json')):
        if not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError(f'Publication file points outside publications/: {path.name}')
        item = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(item, dict):
            raise ValueError(f'{path.name} must contain one publication object.')
        identifier = item.get('id', '')
        if not isinstance(identifier, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', identifier) or identifier != path.stem:
            raise ValueError(f'{path.name}: id must be a safe identifier matching the filename.')
        for key in ('title', 'authors', 'venue', 'topic'):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f'{path.name}: {key} must be a nonempty string.')
        if type(item.get('year')) is not int or not 1000 <= item['year'] <= 9999:
            raise ValueError(f'{path.name}: year must be a four-digit integer.')
        if item.get('type') not in ('book', 'journal', 'conference'):
            raise ValueError(f'{path.name}: type must be book, journal, or conference.')
        if item.get('status') not in ('published', 'accepted') or type(item.get('selected')) is not bool:
            raise ValueError(f'{path.name}: status and selected must identify public publication status and selection.')
        if item.get('correspondingAuthor') is not None and type(item['correspondingAuthor']) is not bool:
            raise ValueError(f'{path.name}: correspondingAuthor must be true, false, or null when supplied.')
        if item.get('url'):
            secure_https(item['url'], f'{path.name} url')
        items.append(item)
    return items

PUBLICATIONS = load_publications()


def content_directory(folder):
    directory = ROOT / folder
    if directory.is_symlink() or not directory.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError(f'{folder}/ must remain inside the repository and cannot be a symlink.')
    return directory

def collection_pdf_path(value, folder):
    if not isinstance(value, str) or any(ord(c) < 32 for c in value) or '\\' in value:
        raise ValueError(f'A PDF must be a local path beneath {folder}/.')
    parts = value.split('/')
    path = PurePosixPath(value)
    if len(parts) < 2 or parts[0] != folder or any(part in ('', '.', '..') for part in parts) or path.suffix.lower() != '.pdf':
        raise ValueError(f'A PDF must be a local path such as {folder}/paper.pdf.')
    directory = content_directory(folder)
    target = ROOT / path
    if target.is_symlink() or not target.resolve().is_relative_to(directory.resolve()):
        raise ValueError(f'A PDF cannot point outside {folder}/ or be a symlink.')
    return value

def preprint_pdf_path(value):
    return collection_pdf_path(value, 'preprints')

def validate_iso_date(value, field):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError(f'{field} must use YYYY-MM-DD.')
    date.fromisoformat(value)

def uploaded_metadata(folder='preprints', data_key='preprints'):
    entries = DATA.get(data_key, [])
    if not isinstance(entries, list):
        raise ValueError(f'{data_key} must be a list.')
    result = {}
    for item in entries:
        if not isinstance(item, dict):
            raise ValueError(f'Each {data_key} metadata entry must be an object.')
        path = collection_pdf_path(item.get('pdf'), folder)
        if path in result:
            raise ValueError(f'Duplicate PDF metadata: {path}')
        for key in ('title', 'authors', 'version', 'abstract'):
            if key in item and not isinstance(item[key], str):
                raise ValueError(f'PDF {key} must be a string.')
        if item.get('updated'):
            validate_iso_date(item['updated'], 'PDF updated')
        if item.get('year') is not None and (type(item['year']) is not int or not 1000 <= item['year'] <= 9999):
            raise ValueError('PDF year must be a four-digit integer.')
        for key in ('arxiv_url', 'code_url'):
            if item.get(key):
                secure_https(item[key], key)
        result[path] = item
    return result

def preprint_metadata():
    return uploaded_metadata()

def uploaded_files(folder):
    directory = content_directory(folder)
    files = []
    if directory.exists():
        for path in sorted(directory.rglob('*'), key=lambda x: x.as_posix().casefold()):
            if path.is_symlink():
                raise ValueError(f'Uploaded content cannot be a symlink: {path.relative_to(ROOT)}')
            if path.is_file() and path.suffix.lower() == '.pdf':
                collection_pdf_path(path.relative_to(ROOT).as_posix(), folder)
                files.append(path)
    return files

def uploaded_pdf_cards(folder='preprints', data_key='preprints', ai=False):
    """List explicitly uploaded files without reading or inferring their contents."""
    metadata = uploaded_metadata(folder, data_key)
    cards = []
    for path in uploaded_files(folder):
        relative = collection_pdf_path(path.relative_to(ROOT).as_posix(), folder)
        item = metadata.get(relative, {})
        title = item.get('title') or re.sub(r'[_-]+', ' ', path.stem).strip() or path.name
        pdf_url = quote(relative, safe='/')
        size = path.stat().st_size
        size_label = f'{size / (1024 * 1024):.1f} MB' if size >= 1024 * 1024 else f'{max(1, round(size / 1024))} KB'
        byline = f'<p class="preprint-authors">{person_authors(item["authors"])}</p>' if item.get('authors') else ''
        labels = [str(item['year'])] if item.get('year') else []
        if item.get('version'):
            labels.append(e(item['version']))
        if item.get('updated'):
            labels.append(f'Updated <time datetime="{e(item["updated"])}">{e(item["updated"])}</time>')
        info = f'<p class="preprint-meta">{" · ".join(labels)}</p>' if labels else ''
        abstract = f'<details class="preprint-abstract"><summary>Abstract</summary><p>{e(item["abstract"])}</p></details>' if item.get('abstract') else ''
        links = [f'<a class="preprint-pdf" href="{e(pdf_url)}">Read PDF <span aria-hidden="true">↗</span><span class="visually-hidden">: {e(title)}</span></a><span class="preprint-size">{size_label}</span>']
        for field, label in [('arxiv_url', 'arXiv'), ('code_url', 'Code')]:
            if item.get(field):
                links.append(link(secure_https(item[field], field), label + ' ↗'))
        state = '<p class="ai-state">Not fully checked</p>' if ai else ''
        cards.append(f'<li class="preprint-card"><h3>{e(title)}</h3>{state}{byline}{info}{abstract}<div class="preprint-links">{"".join(links)}</div></li>')
    if not cards:
        message = 'No AI-assisted PDFs have been uploaded.' if ai else 'No PDFs have been uploaded here yet.'
        return f'<div class="preprint-empty"><p>{message}</p></div>'
    return '<ul class="preprint-list">' + '\n'.join(cards) + '</ul>'

def preprint_cards():
    return uploaded_pdf_cards()

def load_arxiv():
    directory = content_directory('arxiv')
    items = []
    for path in sorted(directory.glob('*.json')):
        if path.is_symlink() or not path.resolve().is_relative_to(directory.resolve()):
            raise ValueError(f'Unsupported arXiv metadata path: {path.name}')
        item = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(item, dict):
            raise ValueError(f'{path.name} must contain one arXiv record.')
        identifier = item.get('id', '')
        arxiv_id = item.get('arxivId', '')
        if not isinstance(identifier, str) or not re.fullmatch(r'arxiv-[a-z0-9_-]+', identifier) or identifier != path.stem:
            raise ValueError(f'{path.name}: id must match its safe arxiv- filename.')
        if not isinstance(arxiv_id, str) or not re.fullmatch(r'\d{4}\.\d{4,5}', arxiv_id):
            raise ValueError(f'{path.name}: arxivId must use YYMM.NNNN or YYMM.NNNNN.')
        for key in ('title', 'authors'):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise ValueError(f'{path.name}: {key} must be a nonempty string.')
        if type(item.get('year')) is not int or not 1000 <= item['year'] <= 9999:
            raise ValueError(f'{path.name}: year must be a four-digit integer.')
        for key in ('submitted', 'updated'):
            if item.get(key):
                validate_iso_date(item[key], f'{path.name} {key}')
        for key in ('journalRef', 'topic', 'publicationNote'):
            if item.get(key) is not None and not isinstance(item[key], str):
                raise ValueError(f'{path.name}: {key} must be a string.')
        if item.get('publicationStatus', 'preprint') not in ('published', 'preprint'):
            raise ValueError(f'{path.name}: publicationStatus must be published or preprint.')
        matches = item.get('publishedPublicationIds', [])
        if not isinstance(matches, list) or any(not isinstance(value, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', value) for value in matches) or len(matches) != len(set(matches)):
            raise ValueError(f'{path.name}: publishedPublicationIds must be unique publication identifiers.')
        if item.get('publicationStatus') == 'published' and not matches:
            raise ValueError(f'{path.name}: a published arXiv record must identify its publication counterpart.')
        for key, prefix in [('url', '/abs/'), ('pdfUrl', '/pdf/')]:
            parsed = urlsplit(secure_https(item.get(key), f'{path.name} {key}'))
            tail = re.escape(prefix + arxiv_id) + (r'(?:v\d+)?(?:\.pdf)?' if key == 'pdfUrl' else r'(?:v\d+)?')
            if parsed.hostname not in ('arxiv.org', 'www.arxiv.org') or parsed.port is not None or parsed.query or parsed.fragment or not re.fullmatch(tail, parsed.path):
                raise ValueError(f'{path.name}: {key} must point to this paper on arxiv.org.')
        items.append(item)
    if len({item['arxivId'] for item in items}) != len(items):
        raise ValueError('Duplicate arXiv identifiers are not allowed.')
    return sorted(items, key=lambda x: (x.get('submitted') or x.get('updated') or f'{x["year"]}-01-01', x['arxivId']), reverse=True)

def arxiv_entry(item):
    dates = []
    if item.get('submitted'):
        dates.append(f'Submitted <time datetime="{e(item["submitted"])}">{e(item["submitted"])}</time>')
    if item.get('updated') and item.get('updated') != item.get('submitted'):
        dates.append(f'Updated <time datetime="{e(item["updated"])}">{e(item["updated"])}</time>')
    if not dates:
        dates.append(str(item['year']))
    journal = f'<p class="arxiv-reference">Journal reference: {e(item["journalRef"])}</p>' if item.get('journalRef') else ''
    note = f'<p class="arxiv-reference">{e(item["publicationNote"])}</p>' if item.get('publicationNote') else ''
    return f'<li class="arxiv-paper" id="{e(item["id"])}"><p>{person_authors(item["authors"])}. “{e(item["title"])}.”</p><p class="arxiv-dates">{" · ".join(dates)}</p>{journal}{note}<p class="arxiv-links">{link(item["pdfUrl"], "Read PDF")} · {link(item["url"], "arXiv:"+item["arxivId"])}</p></li>'

def arxiv_section(items):
    if not items:
        return '<p class="secondary">No unpublished arXiv papers are currently listed.</p>'
    latest = '<ul class="arxiv-list">'+'\n'.join(arxiv_entry(item) for item in items[:10])+'</ul>'
    if len(items) > 10:
        latest += f'<details class="older-arxiv"><summary>Older arXiv papers ({len(items)-10})</summary><ul class="arxiv-list">'+ '\n'.join(arxiv_entry(item) for item in items[10:])+'</ul></details>'
    return latest

ARXIV = load_arxiv()
PUBLICATION_ARXIV = {}
for record in ARXIV:
    if record.get('publicationStatus') == 'published':
        for identifier in record['publishedPublicationIds']:
            PUBLICATION_ARXIV.setdefault(identifier, []).append(record)
arxiv_papers = arxiv_section([record for record in ARXIV if record.get('publicationStatus') != 'published'])
preprints = preprint_cards()
ai_papers = uploaded_pdf_cards('ai-papers', 'aiPapers', ai=True)

repository = os.environ.get('GITHUB_REPOSITORY', '')
if repository:
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('GITHUB_REPOSITORY must identify one owner/repository.')
    branch = os.environ.get('GITHUB_REF_NAME', 'main')
    upload_url = f'https://github.com/{repository}/upload/{quote(branch, safe="")}/preprints'
else:
    upload_url = p.get('preprintUploadUrl', '')
preprint_upload = ('<div class="preprint-upload">' + link(secure_https(upload_url, 'preprintUploadUrl'), 'Upload PDF ↗', 'button') + '<p>For site maintainers · GitHub sign-in required</p></div>') if upload_url else '<div class="preprint-upload"><button type="button" class="button" disabled aria-describedby="upload-availability">Upload PDF</button><p id="upload-availability">Available after GitHub Pages setup.</p></div>'




def removal_entry(title, path, kind):
    label = f'Remove {title}'
    if repository:
        target = f'https://github.com/{repository}/delete/{quote(branch, safe="")}/{quote(path, safe="/")}'
        control = f'<a class="remove-paper" href="{e(target)}" aria-label="{e(label)}">Remove</a>'
    else:
        control = f'<button type="button" class="remove-paper" disabled aria-label="{e(label)}">Remove</button>'
    return f'<li><span><span class="managed-kind">{e(kind)}</span>{e(title)}</span>{control}</li>'

def management_list(rows, summary='Manage papers'):
    note = 'For site maintainers · GitHub sign-in required. Select Remove, then confirm and commit the deletion on GitHub. The website updates automatically.' if repository else 'Removal becomes available after GitHub Pages setup. No papers have been removed.'
    listing = '<ul class="managed-papers">'+'\n'.join(rows)+'</ul>' if rows else '<p>No papers to manage.</p>'
    return '<details class="paper-manager"><summary>'+e(summary)+'</summary><p class="management-note">'+e(note)+'</p>'+listing+'</details>'

def uploaded_management_rows(folder, data_key, kind):
    metadata = uploaded_metadata(folder, data_key)
    rows = []
    for path in uploaded_files(folder):
        relative = collection_pdf_path(path.relative_to(ROOT).as_posix(), folder)
        title = metadata.get(relative, {}).get('title') or re.sub(r'[_-]+', ' ', path.stem).strip() or path.name
        rows.append(removal_entry(title, relative, kind))
    return rows

def paper_management():
    rows = [removal_entry(item['title'], f'publications/{item["id"]}.json', 'Publication') for item in sorted(PUBLICATIONS, key=lambda x: (-x['year'], x['title'].casefold()))]
    rows += [removal_entry(item['title'], f'arxiv/{item["id"]}.json', 'Publication arXiv link' if item.get('publicationStatus') == 'published' else 'arXiv preprint') for item in ARXIV]
    rows += uploaded_management_rows('preprints', 'preprints', 'Preprint PDF')
    return management_list(rows)

paper_manager = paper_management()
ai_paper_manager = management_list(uploaded_management_rows('ai-papers', 'aiPapers', 'AI-assisted PDF'), 'Manage AI-Aided Papers')
ai_upload_url = f'https://github.com/{repository}/upload/{quote(branch, safe="")}/ai-papers' if repository else p.get('aiPaperUploadUrl', '')
ai_upload = ('<div class="preprint-upload">'+link(secure_https(ai_upload_url, 'aiPaperUploadUrl'), 'Upload PDF ↗', 'button')+'<p>For site maintainers · GitHub sign-in required</p></div>') if ai_upload_url else '<div class="preprint-upload"><button type="button" class="button" disabled aria-describedby="ai-upload-availability">Upload PDF</button><p id="ai-upload-availability">Available after GitHub Pages setup.</p></div>'


bio = '\n'.join(f'<p>{e(paragraph)}</p>' for paragraph in p['bio'].split('\n\n') if paragraph.strip())

research = '\n'.join(f'<li><strong>{e(x["title"])}.</strong> {e(x["description"])}</li>' for x in DATA['researchAreas'])
publications = '\n'.join(publication(item) for item in sorted(PUBLICATIONS, key=lambda x: (-x['year'], x['type'] != 'book', x['id'])))
career = '\n'.join(f'<li><strong>{e(x["position"])}</strong>, {e(x["institution"])}, {e(x["period"])}.<br><span class="secondary">{e(x["department"])}</span></li>' for x in DATA['career'])
education = '\n'.join(f'<li><strong>{e(x["degree"])}</strong>, {e(x["institution"])}, {e(x["period"])}.'+('<br><span class="secondary">Advisors: '+e(x['advisors'])+'.</span>' if x.get('advisors') else '')+'</li>' for x in DATA['education'])
teaching = '\n'.join(f'<li><strong>{e(x["course"])}</strong>, {e(x["institution"])}' + (f' ({e(x["level"])})' if x.get('level') else '') + f', {e(x["period"])}.</li>' for x in DATA['teaching'] if x['role'] == 'Lecturer')
def service_entry(item):
    period = ', '+e(item['period']) if item.get('period') else ''
    return f'<li><strong>{e(item["role"])}:</strong> {e(item["organization"])}{period}.</li>'
service_lead = '\n'.join(service_entry(x) for x in DATA['service'][:2])
service_more = '\n'.join(service_entry(x) for x in DATA['service'][2:])
honors = '\n'.join(f'<li>{e(x["title"])}'+(', '+e(x['organization']) if x.get('organization') else '')+f', {e(x["year"])}.</li>' for x in DATA['honors'])
counts = {'all': len(PUBLICATIONS), 'selected': sum(x['selected'] for x in PUBLICATIONS), 'journal': sum(x['type'] == 'journal' for x in PUBLICATIONS), 'book': sum(x['type'] == 'book' for x in PUBLICATIONS), 'conference': sum(x['type'] == 'conference' for x in PUBLICATIONS)}
profile_links = ' · '.join(link(x['url'], x['label']) for x in p['links'])
structured = json.dumps({'@context':'https://schema.org','@type':'Person','name':p['name'],'jobTitle':p['position'],'worksFor':{'@type':'CollegeOrUniversity','name':p['affiliation']},'email':p['email'],'sameAs':[x['url'] for x in p['links']]}, ensure_ascii=False).replace('<', '\\u003c')
html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#224b8d">
  <meta name="description" content="Lin Zhou, Associate Professor at SUSTech. Research in information theory, statistical inference, learning, and wireless communications.">
  <title>Lin Zhou — Academic Homepage</title>
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="styles.css">
  <script src="script.js" defer></script>
  <script type="application/ld+json">{structured}</script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="page-layout">
    <header class="site-header sidebar">
      <a class="site-name" href="#home">Lin Zhou</a>
      <nav aria-label="Main navigation">
        <a href="#home">Home / About</a>
        <a href="#research">Research</a>
        <a href="#publications">Publications</a>
        <a href="#preprints">Preprints</a>
        <a href="ai-aided-papers.html">AI-Aided Papers</a>
        <a href="#teaching">Teaching &amp; service</a>
        <a href="#contact">Contact</a>
      </nav>
    </header>
    <main id="main">
      <section id="home" aria-labelledby="home-title">
        <h1 id="home-title">{e(p['name'])}</h1>
        <div class="profile">
          <img class="portrait" src="assets/lin-zhou.jpg" width="500" height="375" alt="Portrait of Lin Zhou" fetchpriority="high">
          <div class="profile-text">
            <p><strong>{e(p['position'])}</strong><br>{e(p['department'])}<br>{e(p['affiliation'])} ({e(p['affiliationShort'])})<br>{e(p['location'])}</p>
            <p>Email: <a href="mailto:{e(p['email'])}">{e(p['email'])}</a></p>
            <p class="profile-links">{profile_links}</p>
          </div>
        </div>
        <div id="about">
          <h2>About</h2>
          {bio}
          <details class="background-details"><summary>Appointments, education, and honors</summary>
            <h3>Appointments</h3><ul>{career}</ul>
            <h3>Education</h3><ul>{education}</ul>
            <h3>Honors &amp; awards</h3><ul>{honors}</ul>
          </details>
        </div>
      </section>

      <section id="research" aria-labelledby="research-title">
        <h2 id="research-title">Research interests</h2>
        <ul class="research-list">{research}</ul>
      </section>

      <section id="publications" aria-labelledby="publications-title">
        <h2 id="publications-title">Publications</h2>
        <p class="publication-intro">Books, monographs, journal articles, and conference papers. See also <a href="https://scholar.google.com/citations?user=_ibA4RwAAAAJ">Google Scholar</a> and <a href="https://dblp.org/pid/69/6147-2.html">DBLP</a>.</p>
        <p class="publication-legend"><sup class="corresponding-marker">*</sup> Corresponding author.</p>
        <div class="publication-tools" id="publication-tools" hidden>
          <div class="filter-group" role="group" aria-label="Filter publications by collection">
            <button type="button" data-filter="selected" aria-pressed="true">Selected <span>({counts['selected']})</span></button>
            <button type="button" data-filter="all" aria-pressed="false">All <span>({counts['all']})</span></button>
            <button type="button" data-filter="journal" aria-pressed="false">Articles <span>({counts['journal']})</span></button>
            <button type="button" data-filter="conference" aria-pressed="false">Conferences <span>({counts['conference']})</span></button>
            <button type="button" data-filter="book" aria-pressed="false">Books <span>({counts['book']})</span></button>
          </div>
          <div class="search-group" role="search" aria-label="Search publications">
            <label for="publication-search" class="visually-hidden">Search publications by title, author, venue, year, or topic</label>
            <input type="search" id="publication-search" placeholder="Search publications…" autocomplete="off" spellcheck="false" aria-controls="publication-list">
            <button type="button" id="clear-search" aria-label="Clear publication search" hidden>Clear</button>
          </div>
        </div>
        <p class="results-count" id="results-count" role="status" aria-live="polite" aria-atomic="true">{counts['all']} publications</p>
        <noscript><p class="secondary">All publications are shown below. Use your browser’s Find command to search this page.</p></noscript>
        <ol class="publication-list" id="publication-list">{publications}</ol>
        <div class="empty-state" id="empty-state" hidden><p>No matching publications. Try another search or choose All.</p><button type="button" id="reset-publications" class="button">Show all publications</button></div>
        <p class="publication-footnote">“To appear” identifies accepted work. See <a href="https://dblp.org/pid/69/6147-2.html">DBLP</a> for additional bibliographic records.</p>
      </section>

      <section id="preprints" aria-labelledby="preprints-title">
        <h2 id="preprints-title">Preprints</h2>
        {arxiv_papers}
        <h3>Uploaded PDFs</h3>
        {preprints}
        {preprint_upload}
        <p class="secondary">AI-assisted working drafts are listed on the separate <a href="ai-aided-papers.html">AI-Aided Papers</a> page.</p>
      </section>

      {paper_manager}

      <section id="teaching" aria-labelledby="teaching-title">
        <h2 id="teaching-title">Teaching &amp; service</h2>
        <h3>Teaching</h3>
        <ul class="teaching-list">{teaching}</ul>
        <h3>Professional service</h3>
        <ul class="service-list">{service_lead}</ul>
        <details><summary>More professional service</summary><ul class="service-list">{service_more}</ul></details>
      </section>

      <section id="contact" aria-labelledby="contact-title">
        <h2 id="contact-title">Contact</h2>
        <p><a href="mailto:{e(p['email'])}">{e(p['email'])}</a><br>{e(p['department'])}<br>{e(p['affiliation'])}<br>{e(p['location'])}</p>
      </section>
      <footer><span>© {e(p['name'])}</span><a href="#home">Back to top</a></footer>
    </main>
  </div>
</body>
</html>
'''

ai_html = f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#224b8d">
  <meta name="description" content="AI-assisted working drafts by Lin Zhou. These results have not been fully checked and may contain errors.">
  <title>AI-Aided Papers — Lin Zhou</title>
  <link rel="icon" href="assets/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <a class="skip-link" href="#main">Skip to content</a>
  <div class="page-layout">
    <header class="site-header sidebar">
      <a class="site-name" href="index.html#home">Lin Zhou</a>
      <nav aria-label="Main navigation">
        <a href="index.html#home">Home / About</a>
        <a href="index.html#research">Research</a>
        <a href="index.html#publications">Publications</a>
        <a href="index.html#preprints">Preprints</a>
        <a href="#ai-papers" aria-current="page">AI-Aided Papers</a>
        <a href="index.html#teaching">Teaching &amp; service</a>
        <a href="index.html#contact">Contact</a>
      </nav>
    </header>
    <main id="main">
      <section id="ai-papers" aria-labelledby="ai-papers-title">
        <h1 id="ai-papers-title">AI-Aided Papers</h1>
        <p class="draft-notice">AI-assisted working drafts. These results have not been fully checked and may contain errors.</p>
        {ai_papers}
        {ai_upload}
        {ai_paper_manager}
      </section>
      <footer><span>© {e(p['name'])}</span><a href="index.html#home">Back to homepage</a></footer>
    </main>
  </div>
</body>
</html>
'''
(ROOT / 'ai-aided-papers.html').write_text(ai_html, encoding='utf-8')

(ROOT / 'index.html').write_text(html, encoding='utf-8')
print(f'Generated index.html with {len(PUBLICATIONS)} publications.')
