"""Regression checks for dated publication announcements and safe rebuilding."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import update_page_presentation as presentation


PUBLICATIONS = '''<ul>
<li class="publication" id="journal-online" data-type="journal">
<p>Lin Zhou. <span class="publication-title"><a href="https://ieeexplore.ieee.org/document/1/">Online article</a></span>
<cite>IEEE Transactions on Information Theory</cite>, 2026.
<a class="publication-arxiv" href="https://arxiv.org/abs/2501.00001">[arXiv]</a></p></li>
<li class="publication" id="journal-forthcoming" data-type="journal">
<p>Lin Zhou. <span class="publication-title">Forthcoming article</span>
<cite>IEEE Transactions on Information Theory</cite> (to appear), 2026.</p></li></ul>'''


def preprints():
    result = ['<ul>']
    for number in range(1, 8):
        identity = f'2610.{number:05d}'
        date = f'2026-10-{29-number:02d}'
        result.append(
            f'<li class="arxiv-paper" id="arxiv-{identity.replace(".", "-")}">'
            f'<span class="publication-title"><a href="https://arxiv.org/pdf/{identity}">'
            f'Preprint {number}</a></span><a class="publication-arxiv" '
            f'href="https://arxiv.org/abs/{identity}">[arXiv]</a>'
            f'<time datetime="{date}">{date}</time></li>')
    result.append('<li class="arxiv-paper preprint-working" id="working">Private draft</li></ul>')
    return ''.join(result)


def event(**changes):
    result = {
        'id': 'online-1', 'recordId': 'journal-online', 'kind': 'publication-online',
        'date': '2026-11-20', 'title': 'Online article',
        'url': 'https://ieeexplore.ieee.org/document/1/',
        'venue': 'IEEE Transactions on Information Theory',
        'sources': ['https://ieeexplore.ieee.org/document/1/'],
    }
    result.update(changes)
    return result


def ledger(*events):
    return {'schemaVersion': 1, 'lastChecked': '2026-11-21', 'events': list(events)}


class PublicationNewsTests(unittest.TestCase):
    def test_online_publications_and_revisions_mix_with_all_submissions(self):
        revision = event(
            id='revision-1', recordId='arxiv-2610-00001', kind='arxiv-revision',
            date='2026-11-19', title='Preprint 1', venue='',
            url='https://arxiv.org/abs/2610.00001v2',
            sources=['https://arxiv.org/abs/2610.00001'])
        data = ledger(event(), revision)
        events, checked = presentation.news_events(PUBLICATIONS, preprints(), data)
        self.assertEqual([e['id'] for e in events[:2]], ['online-1', 'revision-1'])
        self.assertEqual(sum(e['kind'] == 'arxiv-submission' for e in events), 7)
        self.assertNotIn('working', [e['recordId'] for e in events])
        self.assertEqual(checked, '2026-11-21')
        markup = presentation.news_markup(PUBLICATIONS, preprints(), data)
        self.assertIn('datetime="2026-11-20">20 Nov 2026', markup)
        self.assertIn('Revised arXiv preprint', markup)
        visible, archived = markup.split('<details class="news-older">', 1)
        self.assertEqual(visible.count('class="news-entry"'), 6)
        self.assertIn('Preprint 7', archived)

    def test_explicit_arxiv_submission_deduplicates_derived_submission(self):
        submission = event(
            id='verified-submission-1', recordId='arxiv-2610-00001',
            kind='arxiv-submission', date='2026-10-28', title='Preprint 1', venue='',
            url='https://arxiv.org/abs/2610.00001',
            sources=['https://arxiv.org/abs/2610.00001'])
        events, _ = presentation.news_events(PUBLICATIONS, preprints(), ledger(submission))
        matching = [e for e in events if e['recordId'] == 'arxiv-2610-00001']
        self.assertEqual([e['id'] for e in matching], ['verified-submission-1'])
        # A published paper's arXiv ID remains valid after it leaves Preprints.
        older = dict(submission, id='older', recordId='arxiv-2501-00001',
                     date='2025-01-01', url='https://arxiv.org/abs/2501.00001',
                     sources=['https://arxiv.org/abs/2501.00001'])
        presentation.news_events(PUBLICATIONS, preprints(), ledger(older))

    def test_forthcoming_status_cannot_be_reported_as_published(self):
        accepted = event(id='acceptance', recordId='journal-forthcoming',
                         kind='accepted', title='Forthcoming article')
        markup = presentation.news_markup(PUBLICATIONS, preprints(), ledger(accepted))
        self.assertIn('Accepted / forthcoming', markup)
        self.assertNotIn('Published online', markup)
        with self.assertRaisesRegex(ValueError, 'forthcoming citation'):
            presentation.news_events(PUBLICATIONS, preprints(),
                                     ledger(dict(accepted, kind='publication-online')))

    def test_online_verification_date_is_explicitly_distinguished(self):
        verified = event(kind='publication-verified', date='2026-11-21', publicationYear=2026)
        markup = presentation.news_markup(PUBLICATIONS, preprints(), ledger(verified))
        self.assertIn('datetime="2026-11-21">Verified 21 Nov 2026', markup)
        self.assertIn('Online publication verified', markup)
        self.assertIn('exact online publication date is unavailable', markup)
        with self.assertRaisesRegex(ValueError, 'publisher citation'):
            presentation.news_events(PUBLICATIONS, preprints(),
                                     ledger(dict(verified, url='https://ieeexplore.ieee.org/document/2/')))
        with self.assertRaisesRegex(ValueError, 'Duplicate News event'):
            presentation.news_events(PUBLICATIONS, preprints(),
                                     ledger(verified, event(id='exact-online-date')))

    def test_bad_dates_records_sources_and_duplicate_events_fail(self):
        cases = [
            ledger(event(date='2026-02-30')),
            ledger(event(date='2026-13')),
            ledger(event(date='yesterday')),
            ledger(event(date='2026-12-01')),
            ledger(event(recordId='unknown')),
            ledger(event(sources=[])),
            ledger(event(url='javascript:alert(1)')),
            ledger(event(), event()),
            ledger(event(), event(id='another-id')),
            ledger(event(kind='invented-status')),
        ]
        for data in cases:
            with self.subTest(data=data):
                with self.assertRaises(ValueError):
                    presentation.news_events(PUBLICATIONS, preprints(), data)

    def test_imprecise_dates_remain_imprecise_and_checks_are_not_invented(self):
        data = ledger(event(date='2026-10'))
        events, _ = presentation.news_events(PUBLICATIONS, preprints(), data)
        self.assertEqual(events[0]['date'], '2026-10-28')
        self.assertEqual(events[-1]['date'], '2026')
        markup = presentation.news_markup(PUBLICATIONS, preprints(), data)
        self.assertIn('datetime="2026-10">Oct 2026', markup)
        self.assertNotIn('datetime="2026-01-01"', markup)
        with tempfile.TemporaryDirectory() as directory, patch.object(
                presentation, 'ROOT', Path(directory)):
            without_ledger = presentation.news_markup(PUBLICATIONS, preprints())
        self.assertNotIn('Last publication check', without_ledger)
        self.assertNotIn('Checked weekly', without_ledger)

    def test_real_page_generation_is_idempotent_and_preserves_citations(self):
        source = Path(__file__).resolve().parent
        names = ('index.html', 'preprints.html', 'publications.html')
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name in names:
                (target / name).write_text((source / name).read_text(encoding='utf-8'),
                                           encoding='utf-8')
            (target / 'publication-news.json').write_text(json.dumps(ledger()), encoding='utf-8')
            with patch.object(presentation, 'ROOT', target), contextlib.redirect_stdout(io.StringIO()):
                presentation.main()
                first = {name: (target / name).read_bytes() for name in names}
                presentation.main()
            self.assertEqual(first, {name: (target / name).read_bytes() for name in names})
            self.assertEqual(json.loads((target / 'publication-news.json').read_text()), ledger())


if __name__ == '__main__':
    unittest.main()
