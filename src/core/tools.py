import os
from datetime import date, datetime
from urllib.parse import urlparse

import whois
from tavily import TavilyClient

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def search_company(query: str) -> str:
    """
    Searches the web for information about a company using Tavily.
    Args:
        query: The search query (e.g., "Feathery company size funding")
    Returns:
        A string summary of search results for the LLM to read.
    """
    results = tavily_client.search(query=query, max_results=5)
    formatted = []
    for r in results.get("results", []):
        formatted.append(f"- {r['title']}: {r['content']}")

    return "\n".join(formatted) if formatted else "No results found."

def web_search(query: str) -> str:
    """
    General web search using Tavily - for looking up certifications,
    learning resources, курсы, etc. during gap triage.
    Args:
        query: The search query
    Returns:
        A string summary of search results for the LLM to read.
    """
    results = tavily_client.search(query=query, max_results=5)
    formatted = []
    for r in results.get("results", []):
        formatted.append(f"- {r['title']}: {r['content']}")

    return "\n".join(formatted) if formatted else "No results found."

def _normalize_domain(domain: str) -> str:
    candidate = domain.strip().lower()
    if "@" in candidate and "/" not in candidate:
        candidate = candidate.split("@", 1)[1]
    if "://" not in candidate:
        candidate = f"https://{candidate}"
    parsed = urlparse(candidate)
    host = parsed.netloc or parsed.path
    host = host.split("/", 1)[0].split(":", 1)[0]
    if host.startswith("www."):
        host = host[4:]

    return host

def _normalize_whois_value(value):
    if isinstance(value, list):
        normalized_items = [
            _normalize_whois_value(item)
            for item in value
            if item not in (None, "")
        ]
        if not normalized_items:
            return None
        return normalized_items[0] if len(normalized_items) == 1 else normalized_items
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if value in ("", [], (), {}):
        return None

    return value

def whois_lookup(domain: str) -> dict:
    """
    Looks up WHOIS information for a domain.
    Args:
        domain: Domain or URL to inspect
    Returns:
        A dict containing normalized WHOIS data or an error field.
    """
    normalized_domain = _normalize_domain(domain)
    if not normalized_domain:
        return {
            "domain": domain,
            "error": "No domain provided.",
        }

    try:
        result = whois.whois(normalized_domain)
    except Exception as e:
        return {
            "domain": normalized_domain,
            "error": str(e),
        }

    return {
        "domain": normalized_domain,
        "registrar": _normalize_whois_value(result.get("registrar")),
        "creation_date": _normalize_whois_value(result.get("creation_date")),
        "expiration_date": _normalize_whois_value(result.get("expiration_date")),
        "updated_date": _normalize_whois_value(result.get("updated_date")),
        "registrant_org": _normalize_whois_value(
            result.get("org") or result.get("registrant_org")
        ),
        "country": _normalize_whois_value(result.get("country")),
        "name_servers": _normalize_whois_value(result.get("name_servers")),
        "status": _normalize_whois_value(result.get("status")),
        "error": None,
    }
