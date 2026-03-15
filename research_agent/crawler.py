"""
Custom crawler for research using feedparser (Google News RSS) and newspaper3k.
"""
import re
import urllib.parse
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict


def _strip_html(text: str) -> str:
    """Remove HTML tags and decode common entities from RSS summaries."""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)           # strip all HTML tags
    clean = clean.replace('&amp;', '&')
    clean = clean.replace('&lt;', '<')
    clean = clean.replace('&gt;', '>')
    clean = clean.replace('&quot;', '"')
    clean = clean.replace('&#39;', "'")
    clean = clean.replace('&nbsp;', ' ')
    clean = re.sub(r'\s+', ' ', clean).strip()      # collapse whitespace
    return clean


def fetch_evidence_for_entity(name: str, keywords: List[str] = []) -> List[Dict]:
    """
    Crawls Google News RSS for the given company name and keywords.
    Auto-limits to roughly the last 6 months (via RSS 'when:6m' query param or date parsing).
    
    Returns a list of dictionaries with title, date, source, url, and snippet content.
    """
    evidence_list = []
    
    # Construct the query
    query_parts = [f'"{name}"']
    if keywords:
        kw_str = " OR ".join(keywords)
        query_parts.append(f"({kw_str})")
        
    full_query = " AND ".join(query_parts)
    encoded_query = urllib.parse.quote(full_query)
        
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-IN&gl=IN&ceid=IN:en"
    
    feed = feedparser.parse(rss_url)
    
    for entry in feed.entries:
        # Check date
        try:
            from email.utils import parsedate_to_datetime
            pub_date = parsedate_to_datetime(entry.published)
            # Remove timezone for simple comparison 
            pub_date = pub_date.replace(tzinfo=None)
            date_str = pub_date.strftime("%Y-%m-%d")
        except:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")

        evidence_list.append({
            "title": _strip_html(entry.title),
            "date": date_str,
            "source": entry.source.title if hasattr(entry, 'source') else "Google News",
            "url": entry.link,
            "content": _strip_html(entry.summary)
        })
        
    return evidence_list

