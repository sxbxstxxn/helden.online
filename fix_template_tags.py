from pathlib import Path

base = Path('web/templates')
files = ['helden.html', 'gruppen.html', 'events.html', 'news.html', 'forum.html']
for name in files:
    p = base / name
    text = p.read_text(encoding='utf-8')
    fixed = text.replace('{%%', '{%').replace('%%}', '%}')
    p.write_text(fixed, encoding='utf-8')
    print(f'fixed {p}')
