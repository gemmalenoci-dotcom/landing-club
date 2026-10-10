// Da incollare nella console del browser (o con javascript_tool) sulla pagina del Club, a 1440, 1180, 1000, 768 e 375 px.
// Elenca ogni elemento posizionato (badge, adesivi, polaroid, pallini del sentiero) che copre un testo. Lista vuota = ok
(() => {
  document.querySelectorAll('.reveal').forEach(e => { e.classList.add('in', 'vis', 'on', 'shown'); e.style.opacity = 1; e.style.transform = 'none'; });
  const pos = [...document.querySelectorAll('body *')].filter(e => {
    const cs = getComputedStyle(e);
    return (cs.position === 'absolute' || cs.position === 'fixed') && e.offsetWidth > 0 && !e.closest('.pop,#ckb,.hd,.top-bar,[aria-hidden=true],.joinchat');
  });
  const testi = [...document.querySelectorAll('h1,h2,h3,p,li,a.btn,.sotto,.nome,.prezzo,.alt,.frase,small,b,td,.tag,.eyebrow,.mano,.lead,.gradino .card span.d')]
    .filter(e => e.offsetWidth > 0 && e.innerText.trim() && !e.closest('.pop'));
  const out = [];
  for (const a of [...pos, ...document.querySelectorAll('#sentiero circle')]) {
    const ra = a.getBoundingClientRect();
    for (const t of testi) {
      if (a.contains(t) || t.contains(a)) continue;
      const rt = t.getBoundingClientRect();
      const ix = Math.min(ra.right, rt.right) - Math.max(ra.left, rt.left), iy = Math.min(ra.bottom, rt.bottom) - Math.max(ra.top, rt.top);
      if (ix > 2 && iy > 2) out.push(innerWidth + ': ' + (a.tagName === 'circle' ? 'pallino' : a.className) + ' copre «' + t.innerText.trim().slice(0, 40) + '»');
    }
  }
  return [...new Set(out)];
})();
