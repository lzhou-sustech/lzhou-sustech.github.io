/* Filter publication groups without changing their category-specific numbers. */
(() => {
  'use strict';
  const tools = document.getElementById('publication-tools');
  const search = document.getElementById('publication-search');
  const list = document.getElementById('publication-list');
  const count = document.getElementById('results-count');
  const empty = document.getElementById('empty-state');
  const clear = document.getElementById('clear-search');
  const reset = document.getElementById('reset-publications');
  if (!tools || !search || !list || !count || !empty || !clear || !reset) return;
  const buttons = Array.from(tools.querySelectorAll('[data-filter]'));
  const publications = Array.from(list.querySelectorAll('li.publication'));
  const groups = Array.from(list.querySelectorAll('.publication-group'));
  const normalize = value => value.normalize('NFKD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const searchable = publications.map(item => normalize(item.dataset.search || item.textContent || ''));
  const labels = {all: 'publications', selected: 'selected publications', journal: 'journal articles', magazine: 'magazines, surveys and reviews', conference: 'conference papers', book: 'books and monographs'};
  let currentFilter = 'all';
  function update() {
    const words = normalize(search.value.trim()).split(/\s+/).filter(Boolean);
    let visible = 0;
    publications.forEach((item, index) => {
      const inCollection = currentFilter === 'all' || (currentFilter === 'selected' ? item.dataset.selected === 'true' : item.dataset.type === currentFilter);
      item.hidden = !(inCollection && words.every(word => searchable[index].includes(word)));
      if (!item.hidden) visible += 1;
    });
    groups.forEach(group => {
      group.hidden = !Array.from(group.querySelectorAll('li.publication')).some(item => !item.hidden);
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
