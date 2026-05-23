import logging
import re
from datetime import datetime, timezone as datetime_timezone
from email.utils import parsedate_to_datetime
from html import unescape
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.etree import ElementTree

from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

ATOM_NS = {'atom': 'http://www.w3.org/2005/Atom'}
RSS_NS = {'dc': 'http://purl.org/dc/elements/1.1/'}
TAG_RE = re.compile(r'<[^>]+>')


def get_rss_news():
    cache_key = 'rss_news_items'
    cached_news = cache.get(cache_key)
    if cached_news is not None:
        return cached_news

    news_items = []
    for feed in getattr(settings, 'RSS_FEEDS', []):
        news_items.extend(_load_feed(feed))

    news_items.sort(key=lambda item: item['published_at'] or datetime.min.replace(tzinfo=datetime_timezone.utc), reverse=True)
    news_items = news_items[:getattr(settings, 'RSS_FEED_MAX_ITEMS', 24)]
    cache.set(cache_key, news_items, getattr(settings, 'RSS_FEED_CACHE_SECONDS', 1800))
    return news_items


def _load_feed(feed):
    try:
        content = _fetch_feed_content(feed['url'])
        return _parse_feed(content, feed)
    except (ElementTree.ParseError, KeyError, URLError, TimeoutError, OSError) as exc:
        logger.warning('RSS feed could not be loaded: %s', feed.get('name', feed.get('url')), exc_info=exc)
        return []


def _fetch_feed_content(url):
    request = Request(url, headers={'User-Agent': 'helden.online RSS reader'})
    with urlopen(request, timeout=5) as response:
        return response.read()


def _parse_feed(content, feed):
    root = ElementTree.fromstring(content)
    if root.tag.endswith('feed'):
        return _parse_atom(root, feed)
    return _parse_rss(root, feed)


def _parse_rss(root, feed):
    items = []
    for entry in root.findall('.//item')[:getattr(settings, 'RSS_FEED_ITEMS_PER_SOURCE', 8)]:
        title = _text(entry, 'title')
        link = _text(entry, 'link')
        if not title or not link:
            continue
        published_at = _parse_date(_text(entry, 'pubDate') or _text(entry, 'dc:date', RSS_NS))
        items.append(_news_item(feed, title, link, _text(entry, 'description'), published_at))
    return items


def _parse_atom(root, feed):
    items = []
    for entry in root.findall('atom:entry', ATOM_NS)[:getattr(settings, 'RSS_FEED_ITEMS_PER_SOURCE', 8)]:
        title = _text(entry, 'atom:title', ATOM_NS)
        link = _atom_link(entry)
        if not title or not link:
            continue
        published_at = _parse_date(_text(entry, 'atom:updated', ATOM_NS) or _text(entry, 'atom:published', ATOM_NS))
        summary = _text(entry, 'atom:summary', ATOM_NS) or _text(entry, 'atom:content', ATOM_NS)
        items.append(_news_item(feed, title, link, summary, published_at))
    return items


def _news_item(feed, title, link, summary, published_at):
    return {
        'source': feed['name'],
        'source_slug': feed['slug'],
        'title': _clean_text(title),
        'link': link.strip(),
        'summary': _clean_text(summary)[:240],
        'published_at': published_at,
    }


def _text(element, path, namespace=None):
    child = element.find(path, namespace or {})
    if child is None or child.text is None:
        return ''
    return child.text.strip()


def _atom_link(entry):
    for link in entry.findall('atom:link', ATOM_NS):
        href = link.get('href')
        rel = link.get('rel', 'alternate')
        if href and rel == 'alternate':
            return href
    return ''


def _parse_date(value):
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=datetime_timezone.utc)
    return parsed


def _clean_text(value):
    return unescape(TAG_RE.sub('', value or '')).strip()
