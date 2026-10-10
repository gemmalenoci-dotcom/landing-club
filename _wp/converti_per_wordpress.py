"""Trasforma sorgente.html (pagina statica del Club) nel contenuto di una pagina WordPress.

Uso: python3 _wp/converti_per_wordpress.py  -> scrive _wp/contenuto.html

- Le immagini puntano alla libreria media di unlikeacademy.it (caricate con il nome club-<cartella>-<file>)
- I font restano su academy.unlikeacademy.it (GitHub Pages manda l'intestazione CORS)
- Tutto il CSS viene chiuso dentro #ulc, cosi il tema e il kit di Elementor non lo sovrascrivono
"""
import re, pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
SRC = (BASE / 'sorgente.html').read_text(encoding='utf-8')
MEDIA = 'https://unlikeacademy.it/wp-content/uploads/2026/10/club-'
FONTS = 'https://academy.unlikeacademy.it/assets/fonts/'


def media(path):
    return MEDIA + path.replace('assets/', '').replace('/', '-')


def fix_urls(text):
    text = re.sub(r'assets/fonts/', FONTS, text)
    return re.sub(r'(?<![\w/.])assets/[A-Za-z0-9_./-]+\.(?:jpg|png|webp)', lambda m: media(m.group(0)), text)


def prefix_selector(sel):
    sel = sel.strip()
    if not sel:
        return sel
    if sel.startswith('html'):
        return sel
    if sel == 'body':
        return '#ulc'
    if sel == '*':
        return '#ulc,#ulc *'
    if sel.startswith('body'):
        return '#ulc' + sel[4:]
    return '#ulc ' + sel


def scope_css(css):
    out, i = [], 0
    while i < len(css):
        j = css.find('{', i)
        if j < 0:
            out.append(css[i:])
            break
        head = css[i:j].strip()
        if head.startswith('@media') or head.startswith('@supports'):
            depth, k = 1, j + 1
            while depth:
                if css[k] == '{':
                    depth += 1
                elif css[k] == '}':
                    depth -= 1
                k += 1
            out.append(head + '{' + scope_css(css[j + 1:k - 1]) + '}')
            i = k
            continue
        k = css.find('}', j)
        body = css[j + 1:k]
        if head.startswith('@font-face') or head.startswith(':root') or head.startswith('@'):
            out.append(head + '{' + body + '}')
        else:
            sels = ','.join(prefix_selector(s) for s in head.split(','))
            out.append(sels + '{' + body + '}')
        i = k + 1
    return '\n'.join(out)


style = re.search(r'<style>(.*?)</style>', SRC, re.S).group(1)
style = re.sub(r'/\*.*?\*/', '', style, flags=re.S)
style = scope_css(fix_urls(style))
# niente scroll orizzontale ma senza rompere l'header fisso
style = style.replace('overflow-x:hidden', 'overflow-x:clip')
style += '\n#ulc{min-height:100vh}\n#ulc a{text-decoration:inherit}\n#ulc .hd nav a,#ulc footer a{text-decoration:none}\n'

jsonld = re.search(r'(<script type="application/ld\+json">.*?</script>)', SRC, re.S).group(1)
jsonld = jsonld.replace('https://academy.unlikeacademy.it/assets/logo/logo.webp', media('assets/logo/logo.webp'))
jsonld = jsonld.replace('https://academy.unlikeacademy.it/', 'https://unlikeacademy.it/')

body = re.search(r'<body>(.*)</body>', SRC, re.S).group(1)
scripts = re.findall(r'<script>.*?</script>', body, re.S)
body = re.sub(r'<script>.*?</script>', '', body, flags=re.S)
body = fix_urls(body).strip()
script = '\n'.join(scripts).replace("const PIXEL_ID=", "var PIXEL_ID=")
# WordPress trasforma & in &#038; e rompe gli script: negli script di sorgente.html niente & (per && si usano if annidati, nelle regex \\x26)
assert '&' not in script, 'Negli script di sorgente.html non usare &: WordPress lo trasforma in &#038; e rompe la pagina'

content = ('<!-- wp:html -->\n<style>\n' + style + '\n</style>\n' + jsonld + '\n<div id="ulc">\n' + body +
           '\n</div>\n' + script + '\n<!-- /wp:html -->\n')
(BASE / '_wp' / 'contenuto.html').write_text(content, encoding='utf-8')
print('ok', len(content), 'caratteri')
