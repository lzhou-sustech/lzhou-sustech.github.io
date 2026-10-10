/* Progressive enhancement: every publication is present in index.html. */
(() => {
  'use strict';
  const tools = document.getElementById('publication-tools');
  const search = document.getElementById('publication-search');
  const buttons = Array.from(document.querySelectorAll('[data-filter]'));
  const publications = Array.from(document.querySelectorAll('.publication'));
  const count = document.getElementById('results-count');
  const empty = document.getElementById('empty-state');
  const clear = document.getElementById('clear-search');
  const reset = document.getElementById('reset-publications');
  if (!tools || !search || !count || !empty || !clear || !reset) return;
  let currentFilter = 'selected';
  const normalize = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const searchable = publications.map(item => normalize(item.dataset.search || ''));
  const labels = { selected: 'selected publications', all: 'publications', journal: 'articles', conference: 'conference papers', book: 'books and monographs' };
  function update() {
    const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let visible = 0;
    publications.forEach((item, index) => {
      const inCollection = currentFilter === 'all' || (currentFilter === 'selected' ? item.dataset.selected === 'true' : item.dataset.type === currentFilter);
      const matches = words.every(word => searchable[index].includes(word));
      item.hidden = !(inCollection && matches);
      if (!item.hidden) visible += 1;
    });
    buttons.forEach(button => button.setAttribute('aria-pressed', String(button.dataset.filter === currentFilter)));
    count.textContent = `Showing ${visible} ${labels[currentFilter]}${words.length ? ' matching your search' : ''}`;
    empty.hidden = visible !== 0;
    clear.hidden = search.value.length === 0;
  }
  buttons.forEach(button => button.addEventListener('click', () => {
    currentFilter = button.dataset.filter;
    update();
  }));
  search.addEventListener('input', update);
  clear.addEventListener('click', () => { search.value = ''; update(); search.focus(); });
  reset.addEventListener('click', () => { search.value = ''; currentFilter = 'all'; update(); search.focus(); });
  tools.hidden = false;
  update();
})();
