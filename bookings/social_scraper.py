"""
Uniwersalny import danych firmy z linku.

Obsługiwane platformy:
- Facebook (strony firmowe)
- Instagram (profile publiczne)
- Google Maps / Wizytówka Google
- TripAdvisor
- Dowolna strona www (OG meta tagi + JSON-LD)

Wystarczy wkleić link — platforma wykrywana automatycznie.
"""

import re
import json
import logging
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TIMEOUT = 10
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ── Platform detection ────────────────────────────────────────────────────────

PLATFORM_PATTERNS = [
    ("facebook",    re.compile(r"(facebook\.com|fb\.com|fb\.me)", re.I)),
    ("instagram",   re.compile(r"instagram\.com", re.I)),
    ("google",      re.compile(r"(google\.\w+/maps|maps\.google|maps\.app\.goo\.gl|g\.co|goo\.gl/maps|g\.page)", re.I)),
    ("tripadvisor", re.compile(r"tripadvisor\.", re.I)),
]


def detect_platform(url: str) -> str:
    """Return platform name or 'website' for unknown URLs."""
    for name, pattern in PLATFORM_PATTERNS:
        if pattern.search(url):
            return name
    return "website"


PLATFORM_LABELS = {
    "facebook":    "Facebook",
    "instagram":   "Instagram",
    "google":      "Google Maps",
    "tripadvisor": "TripAdvisor",
    "website":     "Strona www",
}

PLATFORM_ICONS = {
    "facebook":    "bi-facebook",
    "instagram":   "bi-instagram",
    "google":      "bi-google",
    "tripadvisor": "bi-star-half",
    "website":     "bi-globe",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _fetch(url: str) -> str | None:
    """Fetch URL content, return HTML or None."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.warning("Nie udalo sie pobrac %s: %s", url, exc)
        return None


def _og(soup: BeautifulSoup, prop: str) -> str:
    tag = soup.find("meta", property=f"og:{prop}")
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""


def _meta(soup: BeautifulSoup, name: str) -> str:
    tag = soup.find("meta", attrs={"name": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""


def _jsonld_all(soup: BeautifulSoup) -> list[dict]:
    """Extract all JSON-LD blocks from the page."""
    results = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                results.extend(d for d in data if isinstance(d, dict))
            elif isinstance(data, dict):
                results.append(data)
        except (json.JSONDecodeError, TypeError):
            pass
    return results


def _extract_images_from_jsonld(data: dict) -> list[str]:
    """Pull image URLs from a JSON-LD object."""
    imgs = []
    raw = data.get("image")
    if not raw:
        return imgs
    if isinstance(raw, str):
        imgs.append(raw)
    elif isinstance(raw, dict) and raw.get("url"):
        imgs.append(raw["url"])
    elif isinstance(raw, list):
        for item in raw:
            if isinstance(item, str):
                imgs.append(item)
            elif isinstance(item, dict) and item.get("url"):
                imgs.append(item["url"])
    return imgs


def _empty_result() -> dict:
    return {
        "name": "",
        "description": "",
        "image_url": "",
        "images": [],
        "phone": "",
        "website": "",
        "address": "",
        "city": "",
        "platform": "",
        "platform_label": "",
    }


# ── Platform-specific importers ──────────────────────────────────────────────

def _import_facebook(url: str, html: str) -> dict:
    result = _empty_result()
    result["platform"] = "facebook"
    result["platform_label"] = "Facebook"

    soup = BeautifulSoup(html, "html.parser")

    # Name
    name = _og(soup, "title")
    if not name and soup.title:
        name = soup.title.get_text().strip()
    if name:
        name = re.sub(r"\s*[-\u2013|]\s*(Facebook|FB).*$", "", name, flags=re.I).strip()
    result["name"] = name

    # Description
    desc = _og(soup, "description") or _meta(soup, "description") or ""
    if desc:
        desc = re.sub(
            r"^.*?(polubi[l\u0142][oa]?|lubi to|like[sd]?).*?\.\s*",
            "", desc, count=1, flags=re.I,
        ).strip()
    result["description"] = desc

    # OG image
    og_img = _og(soup, "image")
    if og_img:
        result["image_url"] = og_img
        result["images"].append(og_img)

    # JSON-LD
    for data in _jsonld_all(soup):
        for img in _extract_images_from_jsonld(data):
            if img not in result["images"]:
                result["images"].append(img)
        addr = data.get("address", {})
        if isinstance(addr, dict):
            result["address"] = result["address"] or addr.get("streetAddress", "")
            result["city"] = result["city"] or addr.get("addressLocality", "")
        result["phone"] = result["phone"] or data.get("telephone", "")
        url_val = data.get("url", "")
        if url_val and "facebook.com" not in url_val:
            result["website"] = result["website"] or url_val

    # FB CDN images
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src or any(s in src for s in ["emoji", "pixel", "tr?", "1x1", ".gif", "static"]):
            continue
        if ("scontent" in src or "fbcdn" in src) and src not in result["images"]:
            result["images"].append(src)
        if len(result["images"]) >= 10:
            break

    return result


def _import_instagram(url: str, html: str) -> dict:
    result = _empty_result()
    result["platform"] = "instagram"
    result["platform_label"] = "Instagram"

    soup = BeautifulSoup(html, "html.parser")

    # Name
    name = _og(soup, "title") or ""
    if name:
        name = re.sub(r"\s*\(@[^)]+\).*$", "", name).strip()
        name = re.sub(r"\s*[\u2022\u00b7|]\s*Instagram.*$", "", name, flags=re.I).strip()
    result["name"] = name

    # Description / bio
    desc = _og(soup, "description") or _meta(soup, "description") or ""
    if desc:
        bio = re.search(r'[\u201c\u201d""](.+?)[\u201c\u201d""]', desc)
        if bio:
            desc = bio.group(1).strip()
        else:
            desc = re.sub(
                r"\d+\s*(Followers?|Following|Posts?|Obserwuj[a\u0105]c[ye]|obserwowani|post[o\u00f3]w).*?[-\u2013]?\s*",
                "", desc, flags=re.I,
            ).strip()
            desc = re.sub(r"See Instagram.*$", "", desc, flags=re.I).strip()
    result["description"] = desc

    # OG image
    og_img = _og(soup, "image")
    if og_img:
        result["image_url"] = og_img
        result["images"].append(og_img)

    # Inline JSON data
    for script in soup.find_all("script"):
        text = script.string or ""
        if "display_url" in text or "profile_pic_url" in text:
            for m in re.finditer(r'"display_url"\s*:\s*"([^"]+)"', text):
                img_url = m.group(1).replace("\\u0026", "&")
                if img_url not in result["images"]:
                    result["images"].append(img_url)
                if len(result["images"]) >= 10:
                    break
            for m in re.finditer(r'"profile_pic_url_hd"\s*:\s*"([^"]+)"', text):
                img_url = m.group(1).replace("\\u0026", "&")
                if not result["image_url"]:
                    result["image_url"] = img_url
                if img_url not in result["images"]:
                    result["images"].insert(0, img_url)

    return result


def _import_google(url: str, html: str) -> dict:
    """Import z Wizytowki Google / Google Maps."""
    result = _empty_result()
    result["platform"] = "google"
    result["platform_label"] = "Google Maps"

    soup = BeautifulSoup(html, "html.parser")

    # OG data
    result["name"] = _og(soup, "title") or ""
    if result["name"]:
        result["name"] = re.sub(r"\s*[-\u2013]\s*Google Maps.*$", "", result["name"], flags=re.I).strip()
        result["name"] = re.sub(r"\s*[\u00b7\u2022]\s*.*$", "", result["name"]).strip()

    result["description"] = _og(soup, "description") or _meta(soup, "description") or ""
    if result["description"]:
        result["description"] = re.sub(r"\u2b50.*$", "", result["description"]).strip()

    og_img = _og(soup, "image")
    if og_img:
        result["image_url"] = og_img
        result["images"].append(og_img)

    # JSON-LD
    for data in _jsonld_all(soup):
        result["name"] = result["name"] or data.get("name", "")
        result["description"] = result["description"] or data.get("description", "")
        result["phone"] = result["phone"] or data.get("telephone", "")
        url_val = data.get("url", "")
        if url_val and "google." not in url_val:
            result["website"] = result["website"] or url_val
        addr = data.get("address", {})
        if isinstance(addr, dict):
            result["address"] = result["address"] or addr.get("streetAddress", "")
            result["city"] = result["city"] or addr.get("addressLocality", "")
        for img in _extract_images_from_jsonld(data):
            if img not in result["images"]:
                result["images"].append(img)

    # Google hosted images
    for img in soup.find_all("img"):
        src = img.get("src", "") or img.get("data-src", "")
        if not src:
            continue
        if any(s in src for s in ["googleusercontent.com", "lh3.", "lh4.", "lh5.", "streetviewpixels"]):
            if src not in result["images"]:
                result["images"].append(src)
        if len(result["images"]) >= 10:
            break

    return result


def _import_tripadvisor(url: str, html: str) -> dict:
    """Import z TripAdvisor."""
    result = _empty_result()
    result["platform"] = "tripadvisor"
    result["platform_label"] = "TripAdvisor"

    soup = BeautifulSoup(html, "html.parser")

    # OG
    result["name"] = _og(soup, "title") or ""
    if result["name"]:
        result["name"] = re.sub(r"\s*[-\u2013,]\s*(Recenzje|Reviews|TripAdvisor).*$", "", result["name"], flags=re.I).strip()

    result["description"] = _og(soup, "description") or _meta(soup, "description") or ""

    og_img = _og(soup, "image")
    if og_img:
        result["image_url"] = og_img
        result["images"].append(og_img)

    # JSON-LD
    for data in _jsonld_all(soup):
        result["name"] = result["name"] or data.get("name", "")
        result["description"] = result["description"] or data.get("description", "")
        result["phone"] = result["phone"] or data.get("telephone", "")
        url_val = data.get("url", "")
        if url_val and "tripadvisor" not in url_val:
            result["website"] = result["website"] or url_val
        addr = data.get("address", {})
        if isinstance(addr, dict):
            result["address"] = result["address"] or addr.get("streetAddress", "")
            result["city"] = result["city"] or addr.get("addressLocality", "")
        for img in _extract_images_from_jsonld(data):
            if img not in result["images"]:
                result["images"].append(img)

    # Photo tiles
    for img in soup.find_all("img"):
        src = img.get("src", "") or img.get("data-lazyurl", "")
        if src and "photo" in src and "tripadvisor" in src and src not in result["images"]:
            result["images"].append(src)
        if len(result["images"]) >= 10:
            break

    return result


def _import_website(url: str, html: str) -> dict:
    """Fallback: import z dowolnej strony www (OG + JSON-LD)."""
    result = _empty_result()
    result["platform"] = "website"
    result["platform_label"] = "Strona www"

    soup = BeautifulSoup(html, "html.parser")

    # OG / meta
    result["name"] = _og(soup, "site_name") or _og(soup, "title") or ""
    if not result["name"] and soup.title:
        result["name"] = soup.title.get_text().strip()
    result["description"] = _og(soup, "description") or _meta(soup, "description") or ""

    og_img = _og(soup, "image")
    if og_img:
        result["image_url"] = og_img
        result["images"].append(og_img)

    # JSON-LD
    for data in _jsonld_all(soup):
        result["name"] = result["name"] or data.get("name", "")
        result["description"] = result["description"] or data.get("description", "")
        result["phone"] = result["phone"] or data.get("telephone", "")
        addr = data.get("address", {})
        if isinstance(addr, dict):
            result["address"] = result["address"] or addr.get("streetAddress", "")
            result["city"] = result["city"] or addr.get("addressLocality", "")
        for img in _extract_images_from_jsonld(data):
            if img not in result["images"]:
                result["images"].append(img)

    return result


# ── Public API ────────────────────────────────────────────────────────────────

_IMPORTERS = {
    "facebook":    _import_facebook,
    "instagram":   _import_instagram,
    "google":      _import_google,
    "tripadvisor": _import_tripadvisor,
    "website":     _import_website,
}


def import_from_url(url: str) -> dict:
    """
    Import business data from a single URL.

    Auto-detects the platform and returns:
        name, description, image_url, images[], phone, website, address, city,
        platform, platform_label
    """
    if not url:
        return _empty_result()

    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    platform = detect_platform(url)

    html = _fetch(url)
    if not html:
        result = _empty_result()
        result["platform"] = platform
        result["platform_label"] = PLATFORM_LABELS.get(platform, platform)
        return result

    importer = _IMPORTERS.get(platform, _import_website)
    result = importer(url, html)

    # Deduplicate & cap images
    seen = set()
    unique = []
    for img in result["images"]:
        if img not in seen:
            seen.add(img)
            unique.append(img)
    result["images"] = unique[:12]

    return result


def import_from_urls(urls: list[str]) -> dict:
    """
    Import from multiple URLs, merging results.

    First URL with data wins for each field; images are merged.
    """
    merged = _empty_result()
    merged["sources"] = []

    for url in urls:
        if not url or not url.strip():
            continue
        data = import_from_url(url)
        merged["sources"].append({
            "url": url.strip(),
            "platform": data["platform"],
            "platform_label": data["platform_label"],
        })
        merged["name"] = merged["name"] or data["name"]
        merged["description"] = merged["description"] or data["description"]
        merged["image_url"] = merged["image_url"] or data["image_url"]
        merged["phone"] = merged["phone"] or data["phone"]
        merged["website"] = merged["website"] or data["website"]
        merged["address"] = merged["address"] or data["address"]
        merged["city"] = merged["city"] or data["city"]
        for img in data["images"]:
            if img not in merged["images"]:
                merged["images"].append(img)

    # cap
    merged["images"] = merged["images"][:12]
    return merged
