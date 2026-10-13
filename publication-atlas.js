/* Research Atlas: an interactive theme-by-year view of selected publications.
 * Data are derived from the same source as the site's Publications page.
 * No network requests, trackers, or third-party chart libraries.
 */
(() => {
  'use strict';
  const dataNode = document.getElementById('publication-atlas-data');
  if (!dataNode) return;
  let papers;
  try {
    papers = JSON.parse(dataNode.textContent || '[]');
  } catch (error) {
    console.error('Research Atlas: invalid publication data.', error);
    return;
  }
  if (!Array.isArray(papers) || papers.length === 0) return;

  const themes = [
    { name: 'Source coding & refinement', color: '#3b6fa8' },
    { name: 'Testing & matching', color: '#248179' },
    { name: 'Adaptive search', color: '#976b35' },
    { name: 'Multiuser & security', color: '#80679c' }
  ];
  const paperById = new Map(papers.map(p => [p.id, p]));
  const svgNS = 'http://www.w3.org/2000/svg';
  const svgElement = (tag, attributes = {}, text = null) => {
    const element = document.createElementNS(svgNS, tag);
    Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, String(value)));
    if (text !== null) element.textContent = text;
    return element;
  };
  const textNode = (tag, className, contents) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    element.textContent = contents;
    return element;
  };
  const makeLink = (text, href) => {
    const a = document.createElement('a');
    a.textContent = text;
    a.href = href;
    return a;
  };
  const minYear = Math.min(...papers.map(p => p.year));
  const maxYear = Math.max(...papers.map(p => p.year));
  const yearSpan = Math.max(1, maxYear - minYear);
  const yearToX = year => 204 + ((year - minYear) / yearSpan) * 706;
  const laneY = i => 80 + i * 83;
  const axes = [];
  for (let year = minYear; year <= maxYear; year += 2) axes.push(year);
  if (axes[axes.length - 1] !== maxYear) axes.push(maxYear);

  function drawAtlas(host, choose) {
    const viewport = textNode('div', 'atlas-viewport', '');
    const svg = svgElement('svg', {
      viewBox: '0 0 960 425', width: '960', height: '425',
      class: 'atlas-svg', role: 'group',
      'aria-label': 'Selected publications by year and research theme; select a paper to read its details.'
    });

    // The colored bands show research themes, not a numerical distance measure.
    themes.forEach((theme, i) => {
      const y = laneY(i);
      svg.appendChild(svgElement('rect', {
        x: 2, y: y - 29, width: 953, height: 60, rx: 10,
        class: i % 2 ? 'atlas-band atlas-band-alt' : 'atlas-band'
      }));
      svg.appendChild(svgElement('rect', {
        x: 8, y: y - 18, width: 4, height: 36, rx: 2, fill: theme.color
      }));
      svg.appendChild(svgElement('text', {
        x: 24, y: y - 3, class: 'atlas-lane-label'
      }, theme.name.split(' & ')[0]));
      if (theme.name.includes(' & ')) {
        svg.appendChild(svgElement('text', {
          x: 24, y: y + 15, class: 'atlas-lane-label'
        }, '& ' + theme.name.split(' & ')[1]));
      }
      svg.appendChild(svgElement('line', {
        x1: 204, y1: y, x2: 915, y2: y, class: 'atlas-lane-guide'
      }));
    });

    axes.forEach(year => {
      const x = yearToX(year);
      svg.appendChild(svgElement('line', {
        x1: x, y1: 43, x2: x, y2: 357, class: 'atlas-year-guide'
      }));
      svg.appendChild(svgElement('text', {
        x: x, y: 395, class: 'atlas-year-label', 'text-anchor': 'middle'
      }, String(year)));
    });
    svg.appendChild(svgElement('text', {
      x: 556, y: 416, class: 'atlas-axis-title', 'text-anchor': 'middle'
    }, 'Publication year'));

    const actualPositions = new Map();
    themes.forEach((theme, index) => {
      const within = papers.filter(p => Number(p.theme) === index)
        .sort((a, b) => a.year - b.year || a.id.localeCompare(b.id));
      const groups = new Map();
      within.forEach(p => {
        const sameYear = groups.get(p.year) || [];
        sameYear.push(p);
        groups.set(p.year, sameYear);
      });
      within.forEach(p => {
        const group = groups.get(p.year);
        const offset = group.indexOf(p) - (group.length - 1) / 2;
        actualPositions.set(p.id, {
          x: yearToX(p.year) + offset * 17,
          y: laneY(index) + offset * 19,
          color: theme.color
        });
      });
      for (let i = 1; i < within.length; i += 1) {
        const previous = actualPositions.get(within[i - 1].id);
        const current = actualPositions.get(within[i].id);
        const midpoint = (previous.x + current.x) / 2;
        svg.appendChild(svgElement('path', {
          d: 'M' + previous.x + ' ' + previous.y +
            ' C' + midpoint + ' ' + previous.y +
            ', ' + midpoint + ' ' + current.y +
            ', ' + current.x + ' ' + current.y,
          stroke: theme.color, class: 'atlas-connection'
        }));
      }
    });

    const nodes = new Map();
    papers.forEach(p => {
      const point = actualPositions.get(p.id);
      if (!point) return;
      const group = svgElement('g', {
        class: 'atlas-paper-node', role: 'button', tabindex: '0',
        'aria-label': p.title + ', ' + p.year + ', ' + themes[p.theme].name,
        'data-paper-id': p.id
      });
      group.appendChild(svgElement('circle', {
        cx: point.x, cy: point.y, r: 17, fill: point.color,
        class: 'atlas-node-halo'
      }));
      group.appendChild(svgElement('circle', {
        cx: point.x, cy: point.y, r: 8.5, fill: point.color,
        class: 'atlas-node-center'
      }));
      group.appendChild(svgElement('title', {}, p.year + ': ' + p.title));
      group.addEventListener('click', () => choose(p.id));
      group.addEventListener('keydown', event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          choose(p.id);
        }
      });
      nodes.set(p.id, group);
      svg.appendChild(group);
    });
    viewport.appendChild(svg);
    host.appendChild(viewport);
    return id => nodes.forEach((node, key) => {
      node.classList.toggle('is-current', key === id);
      node.setAttribute('aria-pressed', String(key === id));
    });
  }

  function makeDetails(host, paper) {
    host.replaceChildren();
    const topic = themes[Number(paper.theme)] || themes[0];
    const tag = textNode('p', 'atlas-detail-kicker', topic.name + ' · ' + paper.year);
    tag.style.setProperty('--atlas-topic-color', topic.color);
    const heading = document.createElement('h3');
    heading.appendChild(makeLink(paper.title, paper.publisherUrl || 'publications.html#' + paper.id));
    const authors = textNode('p', 'atlas-detail-authors', paper.authors);
    const venue = textNode('p', 'atlas-detail-venue', paper.venue + ', ' + paper.year);
    const links = textNode('p', 'atlas-detail-links', '');
    if (paper.publisherUrl) links.appendChild(makeLink('Publisher', paper.publisherUrl));
    if (paper.arxivUrl) links.appendChild(makeLink('arXiv', paper.arxivUrl));
    links.appendChild(makeLink('Full citation', 'publications.html#' + encodeURIComponent(paper.id)));
    host.append(tag, heading, authors, venue, links);
  }

  document.querySelectorAll('[data-publication-atlas]').forEach(container => {
    const map = container.querySelector('[data-atlas-map]');
    const list = container.querySelector('[data-atlas-list]');
    const details = container.querySelector('[data-atlas-detail]');
    const mapButton = container.querySelector('[data-atlas-mode="map"]');
    const listButton = container.querySelector('[data-atlas-mode="list"]');
    if (!map || !list || !details || !mapButton || !listButton) return;

    let selectedId = papers[0].id;
    const choose = id => {
      if (!paperById.has(id)) return;
      selectedId = id;
      makeDetails(details, paperById.get(id));
      updateDots(id);
      list.querySelectorAll('[data-paper-id]').forEach(button => {
        button.setAttribute('aria-pressed', String(button.dataset.paperId === id));
      });
    };
    const updateDots = drawAtlas(map, choose);
    const ordered = papers.slice().sort((a, b) => b.year - a.year || a.id.localeCompare(b.id));
    ordered.forEach(p => {
      const item = textNode('li', 'atlas-list-item', '');
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.paperId = p.id;
      button.className = 'atlas-list-choice';
      const header = textNode('span', 'atlas-list-choice-title', p.title);
      const meta = textNode('span', 'atlas-list-choice-meta', p.year + ' · ' + themes[p.theme].name);
      button.append(header, meta);
      button.addEventListener('click', () => choose(p.id));
      item.appendChild(button);
      list.appendChild(item);
    });

    const useMode = mode => {
      const showMap = mode === 'map';
      map.hidden = !showMap;
      list.hidden = showMap;
      mapButton.setAttribute('aria-pressed', String(showMap));
      listButton.setAttribute('aria-pressed', String(!showMap));
    };
    mapButton.addEventListener('click', () => useMode('map'));
    listButton.addEventListener('click', () => useMode('list'));
    useMode(window.matchMedia && window.matchMedia('(max-width: 560px)').matches ? 'list' : 'map');
    choose(selectedId);
    container.classList.add('atlas-ready');
  });
})();
