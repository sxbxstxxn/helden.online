from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base = Path('web/templates')
files = ['helden.html', 'gruppen.html', 'events.html', 'news.html', 'forum.html']
for name in files:
    p = base / name
    text = p.read_text(encoding='utf-8')
    fixed = text.replace('{%%', '{%').replace('%%}', '%}')
    p.write_text(fixed, encoding='utf-8')
    logger.info('fixed %s', p)
