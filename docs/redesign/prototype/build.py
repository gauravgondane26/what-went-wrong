"""Inline data.json into template.html -> index.html (a single self-contained prototype page).

Non-ASCII characters are escaped so the page renders the same whether or not the
server sends a charset: \\uXXXX inside <script>, \\XXXXXX inside <style>, &#x...; in markup.
"""
import pathlib
import re

here = pathlib.Path(__file__).parent
tpl = (here / 'template.html').read_text(encoding='utf-8')
data = (here / 'data.json').read_text(encoding='utf-8')
out = tpl.replace('/*__DATA__*/null', data, 1)


def escape(chunk: str, kind: str) -> str:
    def one(ch: str) -> str:
        c = ord(ch)
        if c < 128:
            return ch
        if kind == 'js':
            return '\\u%04x' % c
        if kind == 'css':
            return '\\%06x' % c
        return '&#x%x;' % c
    return ''.join(one(ch) for ch in chunk)


parts = re.split(r'(<script>.*?</script>|<style>.*?</style>)', out, flags=re.S)
out = ''.join(
    escape(p, 'js' if p.startswith('<script>') else 'css' if p.startswith('<style>') else 'html')
    for p in parts
)
(here / 'index.html').write_text(out, encoding='ascii', newline='\n')
print(f'index.html {len(out):,} bytes')
