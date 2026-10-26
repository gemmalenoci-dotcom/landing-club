# -*- coding: utf-8 -*-
"""Genera il pop-up «Tutte le lezioni, una per una» della landing del Club e il PDF scaricabile.

Fonte: i titoli delle lezioni pubblicate su Circle (letti il 26/10/2026 con l'API Admin v2, in sola lettura) in
`_lezioni/dati-circle-2026-10-26.json` (spazi: Free 2596473, Premium 2581479, VIP 2598009, AI 2588895, CapCut 2890963).
Per aggiornarli: rileggere da Circle, sostituire il json, rilanciare questo script e poi `_wp/converti_per_wordpress.py`.

Scrive dentro `sorgente.html` fra i marcatori (idempotente):
  /*LEZ-CSS*/ ... /*/LEZ-CSS*/        stili del pop-up
  <!--LEZ-HTML--> ... <!--/LEZ-HTML--> il pop-up con tutte le lezioni e il suo script (senza & negli script)
  <!--LEZ-BTN--> ... <!--/LEZ-BTN-->   il riquadro che lo apre, accanto al confronto e alla mappa dei videocorsi
  <!--LEZ-BTN2--> ... <!--/LEZ-BTN2--> il bottone dentro la mappa dei videocorsi
e `_lezioni/lezioni-pdf.html` + `assets/lezioni/unlike-academy-tutte-le-lezioni.pdf` (Chrome headless).
"""
import html, json, pathlib, re, subprocess, sys

BASE = pathlib.Path(__file__).resolve().parent.parent
D = json.load(open(BASE / '_lezioni' / 'dati-circle-2026-10-26.json', encoding='utf-8'))
AGG = '26 ottobre 2026'
PDF_URL = 'https://academy.unlikeacademy.it/assets/lezioni/unlike-academy-tutte-le-lezioni.pdf'

# nomi dei moduli come li vede chi legge (i titoli su Circle sono in maiuscolo)
SEZ = {
    'INTRODUZIONE': 'Introduzione', 'M1: MINDSET': 'M1 · Mindset',
    'M2: MERCATO DIGITALE E ALGORITMI SOCIAL': 'M2 · Mercato digitale e algoritmi social',
    'M3: ACQUISIZIONE VS VIRALITÀ': 'M3 · Acquisizione vs viralità', 'M4: BRANDING': 'M4 · Branding',
    'M5: TARGET & STRATEGIA': 'M5 · Target e strategia',
    'M6: CONTENUTI & PIANO EDITORIALE - modulo teorico': 'M6 · Contenuti e piano editoriale',
    'WEBINAR "L\'UNICA INTELLIGENZA ARTIFICIALE CHE TI SERVE NEL 2026"': 'Webinar · L\'unica intelligenza artificiale che ti serve nel 2026',
    'REGALO: IL PRIMO TAGLIO SU CAPCUT CON MICKEL': 'Regalo · Il primo taglio su CapCut con Mickel',
    'M7: Social Media Funnel': 'M7 · Social media funnel', 'M8: Unlock your Instagram': 'M8 · Unlock your Instagram',
    'M8.2: MASTERCLASS Instagram Stories-Telling': 'M8.2 · Masterclass Instagram Stories-Telling',
    'M9: Be discovered on Tik Tok': 'M9 · Be discovered on TikTok',
    'INTRODUZIONE E MATERIALI': 'Introduzione e materiali', 'PARTE 1: MINDSET AI': 'Parte 1 · Mindset AI',
    'PARTE 2: PROMPTING CHE CONVERTE': 'Parte 2 · Prompting che converte', 'PARTE 3: AI PER LA STRATEGIA': 'Parte 3 · AI per la strategia',
    'PARTE 4: CASSETTA DEGLI ATTREZZI': 'Parte 4 · Cassetta degli attrezzi', 'PARTE 5: LABORATORIO AI': 'Parte 5 · Laboratorio AI',
    'Inizia da qui': 'Inizia da qui', 'Bonus · Parola a Mickel': 'Bonus · Parola a Mickel', 'Il prossimo passo': 'Il prossimo passo',
}
SPECIALI = {
    'BONUS E PROSSIMI MODULI: nel piano VIP': 'Bonus e prossimi moduli: nel piano VIP',
    '⚠️ Parti da qui: INTRODUZIONE e MATERIALI (leggere bene)': 'Parti da qui: introduzione e materiali',
    'Come aumentare le interazione delle storie': 'Come aumentare le interazioni delle storie',
    'Benvenuto/a': 'Benvenuto',
}


def pulisci(n):
    n = re.sub(r'\s+', ' ', n).strip()
    if n in SPECIALI:
        return SPECIALI[n]
    n = re.sub(r'^\d+\.\d+\s+', '', n)                      # 10.1, 11.4, 2.1: numeri interni dei moduli
    m = re.match(r'^([A-ZÀ-Ú]{4,})(:?)\s', n)                  # BONUS: / ESERCITAZIONE: / SKILL / TARGET: -> Maiuscola iniziale
    if m:
        n = m.group(1).capitalize() + n[len(m.group(1)):]
    n = re.sub(r'"([^"]+)"', r'«\1»', n)
    return n.replace('Tik Tok', 'TikTok')


def modulo(sec, solo_pubblicate=True):
    ls = [pulisci(l['n']) for l in sec['lessons'] if (l['st'] == 'published' or not solo_pubblicate)]
    return (SEZ.get(sec['name'].strip(), sec['name']), ls)


def moduli(sid, ordine=None, bozza=False):
    out = [modulo(s, not bozza) for s in D[sid]]
    out = [m for m in out if m[1]]
    if ordine:
        out.sort(key=lambda m: ordine.index(m[0]) if m[0] in ordine else 99)
    return out


FREE = moduli('2596473')
ORD = ['Introduzione', 'M1 · Mindset', 'M2 · Mercato digitale e algoritmi social', 'M3 · Acquisizione vs viralità',
       'M4 · Branding', 'M5 · Target e strategia', 'M6 · Contenuti e piano editoriale']
PREMIUM = moduli('2581479', ORD)
VIP_TUTTO = moduli('2598009')
VIP_EXTRA = [m for m in VIP_TUTTO if m[0].split(' ')[0] in ('M7', 'M8', 'M8.2', 'M9')]
AI = moduli('2588895', ['Introduzione e materiali', 'Parte 1 · Mindset AI', 'Parte 2 · Prompting che converte',
                       'Parte 3 · AI per la strategia', 'Parte 4 · Cassetta degli attrezzi', 'Parte 5 · Laboratorio AI'])
# CapCut: le lezioni sono in bozza fino al 29/10 e ci sono due versioni (telefono e PC): si mostra una sola lista
CAP_RAW = moduli('2890963', bozza=True)
CAP = []
for t, ls in CAP_RAW:
    if t.endswith('· PC'):
        continue
    t2 = t.replace(' · Telefono', '')
    ls2 = [re.sub(r' · (Telefono|PC)$', '', x) for x in ls]
    CAP.append((t2, ls2))


def conta(ms):
    return sum(len(m[1]) for m in ms)


n_free, n_prem, n_vip_tot, n_vip_extra, n_ai = conta(FREE), conta(PREMIUM), conta(VIP_TUTTO), conta(VIP_EXTRA), conta(AI)
n_cap = conta(CAP)
print('lezioni: free', n_free, 'premium', n_prem, 'vip totale', n_vip_tot, 'vip extra', n_vip_extra, 'ai', n_ai, 'capcut (una versione)', n_cap)

E = html.escape


def ol(ls):
    return '<ol>' + ''.join('<li%s>%s</li>' % (' class="q"' if l.lower().startswith('quiz') else '', E(l)) for l in ls) + '</ol>'


def blocco(ms):
    return '<div class="lez-cols">' + ''.join('<div class="lez-mod"><h4>%s</h4>%s</div>' % (E(t), ol(ls)) for t, ls in ms) + '</div>'


TABS = [
    ('free', 'Free', '%d lezioni' % n_free,
     'Il videocorso gratuito <b>From Zero to Visible</b>: un assaggio del metodo, con due lezioni per ogni modulo, il webinar sull\'AI e il primo taglio su CapCut con Mickel',
     blocco(FREE)),
    ('premium', 'Premium', '%d lezioni' % n_prem,
     'Il videocorso <b>From Visible to Profitable</b>, dall\'introduzione ai contenuti e al piano editoriale (moduli da M1 a M6). I moduli si sbloccano un po\' alla volta, con esercizi e quiz di fine modulo',
     blocco(PREMIUM)),
    ('vip', 'VIP', '+%d lezioni' % n_vip_extra,
     'Il videocorso <b>From Profitable to Unstoppable</b>: tutto il Premium, con i moduli da M1 a M6 già sbloccati (le lezioni sono quelle del tab Premium), più i moduli avanzati qui sotto: funnel, Instagram, storie e TikTok',
     blocco(VIP_EXTRA)),
    ('ai', 'Corso AI', '%d lezioni' % n_ai,
     '<b>AI per i social + Claude</b>: usare l\'intelligenza artificiale senza sembrare AI, con esercitazioni, skill pronte e laboratori. Nel VIP e nell\'All-Access',
     blocco(AI)),
    ('capcut', 'CapCut', 'dal 29 ottobre',
     'Il corso di <b>Mickel Buratin</b>, da clip grezza a video professionale: 15 lezioni in tre livelli, base, intermedio e avanzato, più il benvenuto e il saluto finale, in due versioni (le stesse lezioni su <b>telefono</b> e su <b>PC</b>). Nel VIP e nell\'All-Access',
     blocco(CAP)),
]

CSS = '''/*LEZ-CSS*/
.lezopen{display:flex;justify-content:space-between;align-items:center;gap:14px;width:100%;text-align:left;background:#fff;border:0;border-radius:14px;box-shadow:var(--ombra);padding:18px 22px;cursor:pointer;font-family:inherit;color:var(--ink);transition:transform .2s}
.lezopen:hover{transform:translate(-1px,-2px)}
.lezopen b{display:block;font-weight:800;font-size:16.5px;color:var(--ink)}
.lezopen small{display:block;font-size:13.5px;color:var(--gray);font-weight:600;margin-top:2px}
.lezopen .pdf{flex:0 0 auto;background:var(--fucsia);color:#fff;border-radius:100px;padding:9px 16px;font-weight:900;font-size:12px;letter-spacing:.08em;text-transform:uppercase;box-shadow:3px 4px 0 rgba(34,124,192,.35)}
.lez{position:fixed;inset:0;z-index:1900;background:rgba(30,25,27,.8);display:none;align-items:center;justify-content:center;padding:16px}
.lez.on{display:flex}
.lez-doc{position:relative;background:#FFFEFA;width:min(1000px,100%);max-height:94vh;border-radius:20px;box-shadow:0 40px 90px -20px rgba(0,0,0,.6);display:flex;flex-direction:column;overflow:hidden}
.lez-head{padding:26px 34px 0;border-bottom:1px solid var(--line);background:#fff}
.lez-head .eyebrow{margin-bottom:8px}
.lez-head h2{font-size:clamp(1.5rem,3.2vw,2.1rem);font-weight:900;letter-spacing:-.035em;line-height:1.05;color:var(--ink);margin:0 40px 6px 0}
.lez-head h2 em{font-family:var(--serif);font-style:italic;font-weight:700;color:var(--fucsia)}
.lez-head p.s{font-size:14.5px;margin:0 0 14px;max-width:62ch}
.lez-x{position:absolute;top:14px;right:16px;width:40px;height:40px;border-radius:50%;border:0;background:var(--carta);color:var(--ink);font-size:24px;line-height:1;cursor:pointer}
.lez-tabs{display:flex;gap:8px;flex-wrap:wrap;padding:2px 0 14px}
.lez-tab{border:2px solid var(--line);background:#fff;color:var(--ink);border-radius:100px;padding:9px 16px;font-family:inherit;font-weight:800;font-size:13.5px;cursor:pointer}
.lez-tab small{font-weight:700;color:var(--gray);margin-left:6px;font-size:12px}
.lez-tab.on{background:var(--blu);border-color:var(--blu);color:#fff}
.lez-tab.on small{color:#DCEBF7}
.lez-body{overflow:auto;padding:22px 34px 26px;flex:1 1 auto;-webkit-overflow-scrolling:touch}
.lez-pan{display:none}
.lez-pan.on{display:block}
.lez-pan>p.n{font-size:14.5px;margin:0 0 18px;padding:12px 16px;background:var(--azzurro);border-radius:12px;color:var(--ink)}
.lez-cols{columns:2 320px;column-gap:38px}
.lez-mod{break-inside:avoid;margin:0 0 24px}
.lez-mod h4{font-size:15px;font-weight:900;letter-spacing:-.01em;color:var(--fucsia);margin:0 0 6px;padding-bottom:6px;border-bottom:2px solid var(--fucsia)}
.lez-mod ol{list-style:none;margin:0;padding:0;counter-reset:l}
.lez-mod li{counter-increment:l;display:flex;gap:10px;font-size:14px;line-height:1.35;padding:6px 0;border-bottom:1px dashed var(--line);color:var(--ink);font-weight:600}
.lez-mod li::before{content:counter(l);flex:0 0 22px;color:var(--blu);font-weight:900;text-align:right}
.lez-mod li.q{color:var(--gray);font-style:italic;font-weight:600}
.lez-foot{display:flex;gap:12px;flex-wrap:wrap;align-items:center;justify-content:space-between;padding:14px 34px;border-top:1px solid var(--line);background:#fff}
.lez-foot span{font-size:12.5px;color:var(--gray)}
.lez-foot .b{display:flex;gap:10px;flex-wrap:wrap}
.lez-foot .btn{padding:12px 20px;font-size:14px}
html.lezlock,html.lezlock body{overflow:hidden}
@media (max-width:640px){.lez{padding:0}.lez-doc{max-height:100vh;height:100vh;border-radius:0}.lez-head{padding:20px 18px 0}.lez-body{padding:16px 18px 20px}.lez-foot{padding:12px 18px}.lez-tab{padding:8px 12px;font-size:12.5px}.lezopen{padding:14px 16px}.lezopen small{font-size:12.5px}}
/*/LEZ-CSS*/'''

tabs_html = ''.join('<button type="button" class="lez-tab%s" role="tab" data-t="%s" id="lt-%s" aria-controls="lp-%s" aria-selected="%s">%s<small>%s</small></button>'
                    % (' on' if i == 0 else '', k, k, k, 'true' if i == 0 else 'false', E(n), E(c)) for i, (k, n, c, _, _) in enumerate(TABS))
pan_html = ''.join('<div class="lez-pan%s" role="tabpanel" id="lp-%s" aria-labelledby="lt-%s"><p class="n">%s</p>%s</div>'
                   % (' on' if i == 0 else '', k, k, nota, corpo) for i, (k, n, c, nota, corpo) in enumerate(TABS))

HTML = '''<!--LEZ-HTML-->
<div class="lez" id="lez" role="dialog" aria-modal="true" aria-labelledby="lezT" aria-hidden="true">
  <div class="lez-doc">
    <button class="lez-x" type="button" id="lezX" aria-label="Chiudi">&times;</button>
    <div class="lez-head">
      <div class="eyebrow">Il programma dei videocorsi</div>
      <h2 id="lezT">Tutte le lezioni del Club, <em>una per una</em></h2>
      <p class="s">I nomi di ogni lezione dei videocorsi, come li trovi dentro il Club. Quali apri dipende dal piano: nel Free un assaggio, nel Premium da M1 a M6, nel VIP anche i moduli avanzati, l'AI e CapCut, nell'All-Access tutto sbloccato dal primo giorno</p>
      <div class="lez-tabs" role="tablist">%s</div>
    </div>
    <div class="lez-body" id="lezBody">%s</div>
    <div class="lez-foot">
      <span>Aggiornato al %s · le lezioni nuove si aggiungono ogni mese</span>
      <div class="b"><a class="btn btn-linea" href="%s" target="_blank" rel="noopener" download>Scarica il PDF</a><a class="btn btn-fu" href="#piani" id="lezPiani">Scegli il tuo piano</a></div>
    </div>
  </div>
</div>
<script>
(function(){
  const el=document.getElementById('lez');
  if(!el){return;}
  const tabs=el.querySelectorAll('.lez-tab'),pans=el.querySelectorAll('.lez-pan'),body=document.getElementById('lezBody');
  let ultimo=null;
  function tab(k){
    tabs.forEach(function(t){const on=t.dataset.t===k;t.classList.toggle('on',on);t.setAttribute('aria-selected',on?'true':'false');});
    pans.forEach(function(p){p.classList.toggle('on',p.id==='lp-'+k);});
    body.scrollTop=0;
  }
  function apri(k){
    ultimo=document.activeElement;
    if(k){tab(k);}
    el.classList.add('on');el.setAttribute('aria-hidden','false');
    document.documentElement.classList.add('lezlock');
    document.getElementById('lezX').focus();
    try{if(location.hash!=='#lezioni'){history.replaceState(null,'','#lezioni');}}catch(e){}
  }
  function chiudi(){
    el.classList.remove('on');el.setAttribute('aria-hidden','true');
    document.documentElement.classList.remove('lezlock');
    try{if(location.hash==='#lezioni'){history.replaceState(null,'',location.pathname+location.search);}}catch(e){}
    if(ultimo){if(ultimo.focus){ultimo.focus();}}
  }
  document.querySelectorAll('[data-lez-open]').forEach(function(b){b.addEventListener('click',function(){apri();});});
  tabs.forEach(function(t){t.addEventListener('click',function(){tab(t.dataset.t);});});
  document.getElementById('lezX').addEventListener('click',chiudi);
  document.getElementById('lezPiani').addEventListener('click',function(){chiudi();});
  el.addEventListener('click',function(e){if(e.target===el){chiudi();}});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'){if(el.classList.contains('on')){chiudi();}}});
  if(location.hash==='#lezioni'){setTimeout(function(){apri();},400);}
  window.addEventListener('hashchange',function(){if(location.hash==='#lezioni'){if(!el.classList.contains('on')){apri();}}});
})();
</script>
<!--/LEZ-HTML-->''' % (tabs_html, pan_html, AGG, PDF_URL)

BTN = '''<!--LEZ-BTN-->
    <div class="confronto reveal" id="lezioni-btn">
      <button type="button" class="lezopen" data-lez-open>
        <span><b>Tutte le lezioni, una per una</b><small>I nomi di ogni lezione dei videocorsi, da sfogliare o scaricare in PDF</small></span>
        <span class="pdf">Apri</span>
      </button>
    </div>
<!--/LEZ-BTN-->'''
BTN2 = '''<!--LEZ-BTN2-->
        <p style="padding:6px 22px 20px;margin:0"><button type="button" class="btn btn-fu" data-lez-open>Vedi tutte le lezioni, una per una</button></p>
<!--/LEZ-BTN2-->'''

src = (BASE / 'sorgente.html').read_text(encoding='utf-8')


def sost(src, a, b, nuovo, ancora=None, dopo=False):
    pat = re.compile(re.escape(a) + r'.*?' + re.escape(b), re.S)
    if pat.search(src):
        return pat.sub(lambda m: nuovo, src, count=1)
    if ancora is None or ancora not in src:
        sys.exit('ancora non trovata per ' + a)
    return src.replace(ancora, (ancora + '\n' + nuovo) if dopo else (nuovo + '\n' + ancora), 1)


src = sost(src, '/*LEZ-CSS*/', '/*/LEZ-CSS*/', CSS, ancora='/* lightbox, cookie, reveal */')
src = sost(src, '<!--LEZ-HTML-->', '<!--/LEZ-HTML-->', HTML, ancora='<div class="lb" id="lb"')
# riquadro accanto alla mappa dei videocorsi: dopo il blocco #moduli
if '<!--LEZ-BTN-->' in src:
    src = sost(src, '<!--LEZ-BTN-->', '<!--/LEZ-BTN-->', BTN)
else:
    src = src.replace('''        </div>
      </details>
    </div>
  </div>
</section>

<!-- CLUB O PERCORSO -->''', '''        </div>
      </details>
    </div>

''' + BTN + '''
  </div>
</section>

<!-- CLUB O PERCORSO -->''', 1)
    if '<!--LEZ-BTN-->' not in src:
        sys.exit('punto di inserimento del riquadro non trovato')
if '<!--LEZ-BTN2-->' in src:
    src = sost(src, '<!--LEZ-BTN2-->', '<!--/LEZ-BTN2-->', BTN2)
else:
    mod_fine = '''<div class="mod"><b>B3</b><span>Lezioni di aggiornamento</span><small>VIP · ogni mese</small></div>
        </div>'''
    if mod_fine not in src:
        sys.exit('fine della mappa moduli non trovata')
    src = src.replace(mod_fine, mod_fine + '\n' + BTN2, 1)
(BASE / 'sorgente.html').write_text(src, encoding='utf-8')
print('sorgente.html aggiornato')

# ---------- PDF
def pdf_blocco(titolo, sotto, ms, colore):
    corpo = ''.join('<div class="m"><h4>%s</h4>%s</div>' % (E(t), ol(ls)) for t, ls in ms)
    return '<section class="c %s"><div class="ch"><h2>%s</h2><p>%s</p></div><div class="cols">%s</div></section>' % (colore, E(titolo), sotto, corpo)


PDF = '''<!doctype html><html lang="it"><head><meta charset="utf-8"><title>Unlike Academy · Tutte le lezioni del Club</title>
<style>
@font-face{font-family:'Open Sauce Sans';src:url(../assets/fonts/open-sauce-sans-600.woff2) format('woff2');font-weight:600}
@font-face{font-family:'Open Sauce Sans';src:url(../assets/fonts/open-sauce-sans-800.woff2) format('woff2');font-weight:800}
@font-face{font-family:'Open Sauce Sans';src:url(../assets/fonts/open-sauce-sans-900.woff2) format('woff2');font-weight:900}
@font-face{font-family:'Playfair Display';src:url(../assets/fonts/playfair-display-italic-base.woff2) format('woff2');font-weight:400 900;font-style:italic}
@page{size:A4;margin:14mm 13mm 14mm}
*{box-sizing:border-box}
body{margin:0;font-family:'Open Sauce Sans',system-ui,sans-serif;color:#3B3638;font-size:9.6pt;line-height:1.35}
.top{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid #CD2471;padding-bottom:8mm;margin-bottom:8mm}
.top img{height:15mm}
.top .t{text-align:right}
.top small{display:block;font-weight:800;letter-spacing:.16em;text-transform:uppercase;font-size:7.5pt;color:#227CC0}
h1{margin:0;font-weight:900;font-size:25pt;letter-spacing:-.03em;line-height:1}
h1 em{font-family:'Playfair Display',serif;font-style:italic;color:#CD2471;font-weight:700}
.intro{margin:0 0 8mm;font-size:10.5pt;max-width:150mm}
.c{margin:0 0 9mm}
.c+.c{break-before:page}
.ch{break-inside:avoid;break-after:avoid;border-radius:3mm;padding:3.2mm 5mm;color:#fff;margin-bottom:4mm}
.ch h2{margin:0;font-size:14pt;font-weight:900;letter-spacing:-.02em}
.ch p{margin:1mm 0 0;font-size:8.8pt;font-weight:600;opacity:.95}
.c.fu .ch{background:#CD2471}.c.bl .ch{background:#227CC0}
.cols{columns:2;column-gap:9mm}
.m{break-inside:avoid;margin:0 0 5mm}
h4{margin:0 0 1.6mm;font-size:10pt;font-weight:900;color:#CD2471;border-bottom:.5mm solid #CD2471;padding-bottom:1mm}
ol{list-style:none;margin:0;padding:0;counter-reset:l}
li{counter-increment:l;display:flex;gap:2.4mm;padding:1.1mm 0;border-bottom:.2mm dashed #D9D4CB;font-weight:600}
li::before{content:counter(l);flex:0 0 5mm;text-align:right;color:#227CC0;font-weight:900}
li.q{color:#665E61;font-style:italic}
.fine{margin-top:6mm;border-top:.4mm solid #E4E0D9;padding-top:4mm;font-size:8.6pt;color:#665E61}
.fine b{color:#3B3638}
</style></head><body>
<div class="top"><img src="../assets/logo/logo.webp" alt="Unlike Academy"><div class="t"><small>Il Club · Videocorsi</small><h1>Tutte le lezioni, <em>una per una</em></h1></div></div>
<p class="intro">I nomi di ogni lezione dei videocorsi del Club di Unlike Academy, come li trovi dentro. Quali apri dipende dal piano: nel Free un assaggio, nel Premium da M1 a M6, nel VIP anche i moduli avanzati, il corso AI e CapCut, nell'All-Access tutto sbloccato dal primo giorno</p>
%s
<div class="fine">Aggiornato al %s · le lezioni nuove si aggiungono ogni mese · tutti i piani e i prezzi su <b>unlikeacademy.it</b></div>
</body></html>''' % (
    pdf_blocco('Free · From Zero to Visible', '%d lezioni · un assaggio del metodo, il webinar sull\'AI e il primo taglio su CapCut con Mickel' % n_free, FREE, 'bl')
    + pdf_blocco('Premium · From Visible to Profitable', '%d lezioni · dall\'introduzione ai contenuti e al piano editoriale, moduli da M1 a M6 con sblocco progressivo' % n_prem, PREMIUM, 'fu')
    + pdf_blocco('VIP · From Profitable to Unstoppable', 'In più rispetto al Premium (che il VIP ha già sbloccato): funnel, Instagram, storie e TikTok · +%d lezioni' % n_vip_extra, VIP_EXTRA, 'bl')
    + pdf_blocco('Corso AI per i social + Claude', '%d lezioni · nel VIP e nell\'All-Access' % n_ai, AI, 'fu')
    + pdf_blocco('Corso CapCut con Mickel Buratin', '15 lezioni in tre livelli, in due versioni (telefono e PC) · nel VIP e nell\'All-Access, dal 29 ottobre', CAP, 'bl'), AGG)
(BASE / '_lezioni' / 'lezioni-pdf.html').write_text(PDF, encoding='utf-8')
(BASE / 'assets' / 'lezioni').mkdir(exist_ok=True)
CH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
r = subprocess.run([CH, '--headless=new', '--disable-gpu', '--no-sandbox', '--no-pdf-header-footer', '--virtual-time-budget=8000',
                    '--print-to-pdf=' + str(BASE / 'assets' / 'lezioni' / 'unlike-academy-tutte-le-lezioni.pdf'),
                    'file://' + str(BASE / '_lezioni' / 'lezioni-pdf.html')], capture_output=True, timeout=180)
print('pdf', (BASE / 'assets' / 'lezioni' / 'unlike-academy-tutte-le-lezioni.pdf').stat().st_size, 'byte')
