/* All Publications Map — independently rendered alongside the Selected Papers atlas.
 * The map aggregates every published work by year and research theme.  It does
 * not imply similarity distances or bibliometric quality comparisons.
 * No remote services, trackers, or chart libraries are needed.
 */
(() => {
  'use strict';
  const types = [
    {id:'all',name:'All publications'},
    {id:'journal',name:'Journals'},
    {id:'conference',name:'Conferences'},
    {id:'magazine',name:'Magazines'},
    {id:'book',name:'Books'}
  ];
  const themes = [
    {name:'Source coding & refinement',short:['Source coding','& refinement'],color:'#316aab'},
    {name:'Statistical testing & matching',short:['Statistical testing','& matching'],color:'#258579'},
    {name:'20 questions & search',short:['20 questions','& search'],color:'#b07637'},
    {name:'Security & covert communication',short:['Security & covert','communication'],color:'#8363a7'},
    {name:'Wireless & networks',short:['Wireless','& networks'],color:'#487c9b'}
  ];
  const ns = 'http://www.w3.org/2000/svg';
  const svg = (tag,atts={},label) => {
    const e = document.createElementNS(ns,tag);
    for (const [k,v] of Object.entries(atts)) e.setAttribute(k,String(v));
    if (label!==undefined) e.textContent=String(label);
    return e;
  };
  const el = (tag,cls,text) => {
    const e=document.createElement(tag);
    if(cls)e.className=cls;
    if(text!==undefined)e.textContent=text;
    return e;
  };
  const link = (text,href) => {
    const a=el('a','',text);
    a.href=href;
    return a;
  };
  const order = {book:0,magazine:1,journal:2,conference:3};
  const plural = (n,singular,plural)=>n===1?singular:plural;

  document.querySelectorAll('[data-full-publications-map]').forEach(host => {
    const data=host.querySelector('[data-full-map-data]');
    const filters=host.querySelector('[data-full-map-filters]');
    const chart=host.querySelector('[data-full-map-chart]');
    const list=host.querySelector('[data-full-map-list]');
    const details=host.querySelector('[data-full-map-detail]');
    const buttons=host.querySelectorAll('[data-full-map-mode]');
    if(!data||!filters||!chart||!list||!details||buttons.length!==2)return;
    let papers;
    try {papers=JSON.parse(data.textContent||'[]');}
    catch(e){console.error('Publications Map: invalid data.',e);return;}
    if(!Array.isArray(papers)||!papers.length)return;
    if(papers.some(p=>!Number.isInteger(p.year)||!Number.isInteger(p.mapTheme)||
                       p.mapTheme<0||p.mapTheme>=themes.length||!p.id||!p.title))return;
    const counts=Object.fromEntries(types.map(t=>[t.id,t.id==='all'?papers.length:
                               papers.filter(p=>p.type===t.id).length]));
    let selectedType='all';
    let selectedKey='';
    let selectedPaperId='';
    let mode='map';
    const yearMin=Math.min(...papers.map(p=>p.year));
    const yearMax=Math.max(...papers.map(p=>p.year));
    const years=Array.from({length:yearMax-yearMin+1},(_,i)=>yearMin+i);
    const xYear=y=>230+(y-yearMin)*725/Math.max(1,yearMax-yearMin);
    const yTheme=i=>79+i*92;
    const grouped=rows=>{
      const m=new Map();
      rows.forEach(p=>{
        const key=p.mapTheme+'|'+p.year;
        if(!m.has(key))m.set(key,[]);
        m.get(key).push(p);
      });
      return m;
    };
    const visiblePapers=()=>papers.filter(p=>selectedType==='all'||p.type===selectedType);
    const paperLinks=p=>{
      const wrap=el('span','full-map-paper-links');
      wrap.append(link('Full citation','publications.html#'+encodeURIComponent(p.id)));
      if(p.publisherUrl)wrap.append(link('Publisher',p.publisherUrl));
      if(p.arxivUrl)wrap.append(link('arXiv',p.arxivUrl));
      return wrap;
    };
    const paperRow=p=>{
      const li=el('li','full-map-paper');
      li.append(el('span','full-map-paper-number','['+(p.number||'?')+']'));
      const block=el('div','full-map-paper-content');
      const main=el('p','full-map-paper-title');
      main.append(link(p.title,p.publisherUrl||'publications.html#'+encodeURIComponent(p.id)));
      const meta=el('p','full-map-paper-meta',p.venue+' · '+p.year);
      block.append(main,meta,paperLinks(p));
      li.append(block);
      return li;
    };
    const setDetails=(rows,heading,helper)=>{
      details.replaceChildren();
      details.append(el('p','full-map-detail-kicker',helper));
      details.append(el('h3','full-map-detail-title',heading));
      const ol=el('ol','full-map-paper-results');
      rows.slice().sort((a,b)=>b.year-a.year||(order[a.type]||0)-(order[b.type]||0)||a.title.localeCompare(b.title))
          .forEach(p=>ol.append(paperRow(p)));
      details.append(ol);
      details.hidden=false;
    };
    const showBin=(key,rows)=>{
      if(!rows.length)return;
      selectedKey=key;
      selectedPaperId='';
      const p=rows[0],theme=themes[p.mapTheme];
      setDetails(rows,p.year+' · '+theme.name,
                 rows.length+' '+plural(rows.length,'publication','publications')+' in this group');
      chart.querySelectorAll('[data-bin-key]').forEach(node=>{
        const active=node.getAttribute('data-bin-key')===key;
        node.classList.toggle('is-active',active);
        node.setAttribute('aria-pressed',String(active));
      });
    };
    const showPaper=p=>{
      selectedPaperId=p.id; selectedKey='';
      setDetails([p],p.title,p.year+' · '+themes[p.mapTheme].name);
      list.querySelectorAll('[data-map-paper-id]').forEach(node=>
        node.setAttribute('aria-pressed',String(node.dataset.mapPaperId===p.id)));
    };
    const renderFilters=()=>{
      filters.replaceChildren();
      types.forEach(t=>{
        if(t.id!=='all'&&counts[t.id]===0)return;
        const button=el('button','full-map-filter',t.name+' ('+counts[t.id]+')');
        button.type='button';
        button.setAttribute('aria-pressed',String(selectedType===t.id));
        button.addEventListener('click',()=>{
          selectedType=t.id;
          selectedKey='';selectedPaperId='';
          renderFilters();renderMap();renderList();
        });
        filters.append(button);
      });
    };
    const renderMap=()=>{
      chart.replaceChildren();
      const rows=visiblePapers(),bins=grouped(rows);
      const viewport=el('div','full-map-viewport');
      const picture=svg('svg',{
        viewBox:'0 0 1000 555',width:1000,height:555,
        class:'full-map-svg',role:'group',
        'aria-label':'Publications by year and topic; each numbered circle shows the number of papers.'
      });
      themes.forEach((t,i)=>{
        const cy=yTheme(i);
        picture.append(svg('rect',{x:1,y:cy-38,width:998,height:77,rx:10,
                                 class:i%2?'full-map-band full-map-band-alt':'full-map-band'}));
        picture.append(svg('rect',{x:11,y:cy-18,width:5,height:38,rx:3,fill:t.color}));
        t.short.forEach((line,j)=>picture.append(svg('text',{x:29,y:cy-5+j*18,
                           class:'full-map-theme-label'},line)));
        picture.append(svg('line',{x1:228,y1:cy,x2:962,y2:cy,class:'full-map-baseline'}));
      });
      years.forEach(y=>{
        const x=xYear(y);
        picture.append(svg('line',{x1:x,y1:38,x2:x,y2:483,class:'full-map-year-line'}));
        picture.append(svg('text',{x,y:521,'text-anchor':'middle',
                                  class:'full-map-year-label'},String(y)));
      });
      picture.append(svg('text',{x:600,y:548,'text-anchor':'middle',
                                 class:'full-map-axis-caption'},'Publication year'));
      const ordered=[...bins.entries()].sort((a,b)=>a[0].localeCompare(b[0]));
      ordered.forEach(([key,items])=>{
        const p=items[0],x=xYear(p.year),y=yTheme(p.mapTheme);
        const radius=Math.min(28,10+4.5*Math.sqrt(items.length));
        const node=svg('g',{class:'full-map-bin',role:'button',tabindex:'0',
          'data-bin-key':key,'aria-pressed':String(selectedKey===key),
          'aria-label':p.year+', '+themes[p.mapTheme].name+', '+items.length+' publications'});
        node.append(svg('circle',{cx:x,cy:y,r:radius+5,
                                 class:'full-map-bin-halo',fill:themes[p.mapTheme].color}));
        node.append(svg('circle',{cx:x,cy:y,r:radius,
                                 class:'full-map-bin-circle',fill:themes[p.mapTheme].color}));
        node.append(svg('text',{x,y:y+5,'text-anchor':'middle',
                                class:'full-map-bin-count'},String(items.length)));
        node.append(svg('title',{},p.year+' · '+themes[p.mapTheme].name+
                            ' · '+items.length+' papers'));
        node.addEventListener('click',()=>showBin(key,items));
        node.addEventListener('keydown',event=>{
          if(event.key==='Enter'||event.key===' '){
            event.preventDefault();showBin(key,items);
          }
        });
        if(selectedKey===key)node.classList.add('is-active');
        picture.append(node);
      });
      viewport.append(picture);
      chart.append(viewport);
      const binsSorted=[...bins.entries()].sort((a,b)=>{
        const aYear=Number(a[0].split('|')[1]),bYear=Number(b[0].split('|')[1]);
        return bYear-aYear||b[1].length-a[1].length;
      });
      if(selectedKey && bins.has(selectedKey))showBin(selectedKey,bins.get(selectedKey));
      else if(binsSorted.length)showBin(binsSorted[0][0],binsSorted[0][1]);
    };
    const renderList=()=>{
      list.replaceChildren();
      const sorted=visiblePapers().slice().sort((a,b)=>
           b.year-a.year||(order[a.type]||0)-(order[b.type]||0)||a.title.localeCompare(b.title));
      sorted.forEach(p=>{
        const item=el('li','full-map-list-row');
        const button=el('button','full-map-list-button');
        button.type='button';
        button.dataset.mapPaperId=p.id;
        button.setAttribute('aria-pressed',String(p.id===selectedPaperId));
        button.append(el('span','full-map-list-name','['+(p.number||'?')+'] '+p.title),
                      el('span','full-map-list-meta',p.year+' · '+themes[p.mapTheme].name));
        button.addEventListener('click',()=>showPaper(p));
        item.append(button);list.append(item);
      });
    };
    const setMode=next=>{
      mode=next;
      chart.hidden=next!=='map';
      list.hidden=next!=='list';
      buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.fullMapMode===next)));
    };
    buttons.forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.fullMapMode)));
    renderFilters();renderMap();renderList();setMode('map');
    host.classList.add('full-map-ready');
  });
})();
