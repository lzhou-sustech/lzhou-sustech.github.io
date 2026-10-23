/* Static, dependency-free gallery for GitHub Pages. Data lives in research-gallery-data.js. */
(() => {
  'use strict';
  const themes = window.LZ_RESEARCH_GALLERY;
  if (!Array.isArray(themes) || !themes.length) return;
  const escape = value => String(value).replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const roots = document.querySelectorAll('[data-research-gallery]');
  if (!roots.length) return;
  const dialog = document.createElement('dialog');
  dialog.className = 'rg-dialog';
  dialog.setAttribute('aria-labelledby', 'rg-modal-title');
  document.body.append(dialog);
  let activeTheme = 0, activeLens = 0, opener = null;
  let previousOverflow = null;
  function showTheme(index, trigger) {
    activeTheme = (index + themes.length) % themes.length;
    activeLens = 0;
    if (trigger) opener = trigger;
    const theme = themes[activeTheme];
    dialog.innerHTML = `
      <div class="rg-dialog-top"><p>Lin Zhou · Research in focus / 0${activeTheme+1}</p><button class="rg-close" type="button" aria-label="Close research detail">×</button></div>
      <div class="rg-modal-heading"><p class="rg-eyebrow">${escape(theme.title)}</p><h2 id="rg-modal-title">${escape(theme.headline)}</h2><p>${escape(theme.question)}</p></div>
      <div class="rg-exhibit"><div class="rg-visual"><img src="assets/research-gallery/${escape(theme.image)}" width="1536" height="864" alt="${escape(theme.alt)}"><div class="rg-focus-marker" aria-hidden="true"></div><div class="rg-visual-caption"><small>Contribution 01 / 03</small><h3></h3></div></div>
      <div class="rg-insight"><div class="rg-lenses" role="tablist" aria-label="Explore research contributions">${theme.contributions.map((item,i)=>`<button type="button" class="rg-lens" id="rg-tab-${i}" role="tab" aria-selected="${i===0}" aria-controls="rg-contribution-panel" tabindex="${i===0?0:-1}" data-lens="${i}"><span>0${i+1}</span>${escape(item.title)}</button>`).join('')}</div>
      <div class="rg-contribution" id="rg-contribution-panel" role="tabpanel" tabindex="0" aria-labelledby="rg-tab-0"><p></p><a class="rg-paper-shortcut" target="_blank" rel="noopener noreferrer">Read the paper ↗</a></div></div></div>
      <details class="rg-papers"><summary>Selected publications · ${theme.papers.length} papers</summary><ol>${theme.papers.map((paper,i)=>`<li data-paper="${i}"><span class="rg-paper-year">${escape(paper.year)}</span><a href="${escape(paper.url)}" target="_blank" rel="noopener noreferrer">${escape(paper.title)} ↗</a></li>`).join('')}</ol></details>
      <div class="rg-bottom-nav"><p>Concept illustrations · Lin Zhou and collaborators</p><button type="button" class="rg-next">Next: ${escape(themes[(activeTheme+1)%themes.length].title)} →</button></div>`;
    dialog.querySelector('.rg-close').addEventListener('click', () => dialog.close());
    dialog.querySelector('.rg-next').addEventListener('click', () => {showTheme(activeTheme+1);dialog.querySelector('.rg-close').focus();});
    dialog.querySelectorAll('[data-lens]').forEach(button => {
      button.addEventListener('click', () => selectLens(Number(button.dataset.lens)));
      button.addEventListener('keydown', event => {
        const key = event.key;
        if (!['ArrowLeft','ArrowRight','Home','End'].includes(key)) return;
        event.preventDefault();
        const next = key==='Home'?0:key==='End'?2:(activeLens+(key==='ArrowRight'?1:2))%3;
        selectLens(next);dialog.querySelector(`[data-lens="${next}"]`).focus();
      });
    });
    selectLens(0);
    dialog.scrollTop = 0;
    if (!dialog.open) {
      if (previousOverflow === null) previousOverflow = document.body.style.overflow;
      dialog.showModal();
      document.body.style.overflow = 'hidden';
    }
  }
  function selectLens(index) {
    activeLens=index;
    const theme=themes[activeTheme], item=theme.contributions[index];
    dialog.querySelectorAll('[data-lens]').forEach((button,i)=>{
      button.setAttribute('aria-selected',String(i===index));button.tabIndex=i===index?0:-1;
    });
    const visual=dialog.querySelector('.rg-visual');
    visual.style.setProperty('--focus-x',item.focus[0]+'%');
    visual.style.setProperty('--focus-y',item.focus[1]+'%');
    visual.classList.toggle('rg-zoom',index!==0);
    visual.querySelector('small').textContent=`Contribution 0${index+1} / 03`;
    visual.querySelector('h3').textContent=item.title;
    const panel=dialog.querySelector('.rg-contribution');
    panel.setAttribute('aria-labelledby',`rg-tab-${index}`);
    panel.querySelector('p').textContent=item.caption;
    panel.querySelector('a').href=theme.papers[item.paper].url;
    dialog.querySelectorAll('[data-paper]').forEach((node,i)=>node.classList.toggle('rg-related',i===item.paper));
  }
  dialog.addEventListener('close',()=>{if(dialog.open)return;document.body.style.overflow=previousOverflow ?? '';previousOverflow=null;if(opener?.isConnected)opener.focus();});
  dialog.addEventListener('click',event=>{if(event.target!==dialog)return;const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();});
  roots.forEach(root=>{
    root.classList.add('rg-gallery');
    root.innerHTML=`<div class="rg-heading"><div><p class="rg-eyebrow">Five connected research directions</p><h2>Explore my research</h2></div><p class="rg-help"><span class="rg-live-dot"></span>Click a scene to explore</p></div>
      <div class="rg-world"><img src="assets/research-gallery/overview.webp" width="1672" height="941" loading="lazy" alt="A three-dimensional research landscape connects source coding, statistical inference, noisy search, security and privacy, and wireless networks through information theory.">${themes.map((theme,i)=>`<button class="rg-hotspot" style="left:${theme.area[0]}%;top:${theme.area[1]}%;width:${theme.area[2]}%;height:${theme.area[3]}%" type="button" data-theme="${i}" aria-label="Explore ${escape(theme.title)}" aria-haspopup="dialog"><span>Explore <b>↗</b></span></button>`).join('')}</div>
      <div class="rg-themes" aria-label="Research areas">${themes.map((theme,i)=>`<button type="button" class="rg-theme" data-theme="${i}" aria-haspopup="dialog"><em>0${i+1}</em>${escape(theme.title)}</button>`).join('')}</div>
      <div class="rg-footer"><span>Fundamental limits · Algorithms · System design</span><a href="publications.html">Publications ↗</a></div>`;
    root.querySelectorAll('[data-theme]').forEach(button=>button.addEventListener('click',()=>showTheme(Number(button.dataset.theme),button)));
  });
})();
