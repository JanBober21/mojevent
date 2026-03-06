"""
Scraper stylów CSS i czcionek ze strony WWW restauracji.

Pobiera stronę, wyciąga:
- linki do Google Fonts / zewnętrznych czcionek
- kolory tła, tekstu, akcentowe
- rodziny czcionek
i zwraca gotowy blok CSS do wstrzyknięcia w formularz rezerwacji.
"""

import re
import logging
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

TIMEOUT = 8  # sekundy
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

# Typowe Google Fonts URL
FONT_URL_PATTERNS = [
    r"fonts\.googleapis\.com",
    r"fonts\.gstatic\.com",
    r"use\.typekit\.net",
]


def _fetch_page(url: str) -> str | None:
    """Pobierz HTML strony."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.warning("Nie udało się pobrać %s: %s", url, exc)
        return None


def _fetch_css(url: str) -> str | None:
    """Pobierz zawartość pliku CSS."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "")
        if "css" in ct or "text" in ct:
            return resp.text
        return None
    except Exception:
        return None


def _is_font_url(url: str) -> bool:
    return any(re.search(p, url) for p in FONT_URL_PATTERNS)


def _extract_font_links(soup: BeautifulSoup) -> list[str]:
    """Wyciągnij linki do czcionek z <link> tagów."""
    font_links = []
    for link in soup.find_all("link"):
        href = link.get("href", "")
        if _is_font_url(href):
            font_links.append(href)
        elif link.get("rel") and "preconnect" in link.get("rel", []):
            continue
    return font_links


def _extract_colors_from_css(css_text: str) -> dict:
    """Wyciągnij najczęściej używane kolory z CSS."""
    colors = {
        "bg_colors": [],
        "text_colors": [],
        "accent_colors": [],
    }
    # Background colors
    for m in re.finditer(r"background(?:-color)?\s*:\s*([^;}{]+)", css_text, re.I):
        val = m.group(1).strip()
        if val and val != "transparent" and val != "inherit" and val != "none":
            colors["bg_colors"].append(val)
    # Text colors
    for m in re.finditer(r"(?<!background-)color\s*:\s*([^;}{]+)", css_text, re.I):
        val = m.group(1).strip()
        if val and val != "inherit" and val != "currentColor":
            colors["text_colors"].append(val)
    return colors


def _extract_font_families(css_text: str) -> list[str]:
    """Wyciągnij rodziny czcionek z CSS."""
    families = []
    for m in re.finditer(r"font-family\s*:\s*([^;}{]+)", css_text, re.I):
        val = m.group(1).strip().rstrip(",")
        if val and val not in families:
            families.append(val)
    return families


def _most_common(items: list, default: str = "") -> str:
    """Zwróć najczęściej powtarzający się element."""
    if not items:
        return default
    from collections import Counter
    counter = Counter(items)
    return counter.most_common(1)[0][0]


def scrape_styles(website_url: str) -> str:
    """
    Główna funkcja — pobiera stronę WWW, analizuje style i zwraca blok CSS.

    Returns:
        str: Blok CSS gotowy do <style>...</style>
    """
    if not website_url:
        return ""

    # Normalizuj URL
    if not website_url.startswith(("http://", "https://")):
        website_url = "https://" + website_url

    html = _fetch_page(website_url)
    if not html:
        return ""

    soup = BeautifulSoup(html, "html.parser")

    # 1. Zbierz linki do czcionek
    font_links = _extract_font_links(soup)
    font_imports = "\n".join(f'@import url("{link}");' for link in font_links)

    # 2. Zbierz inline style + external CSS
    all_css = ""

    # Inline <style> tags
    for tag in soup.find_all("style"):
        if tag.string:
            all_css += tag.string + "\n"

    # External CSS files (pierwsze 3, żeby nie ładować zbyt dużo)
    css_links = []
    for link in soup.find_all("link", rel="stylesheet"):
        href = link.get("href", "")
        if href and not _is_font_url(href):
            full_url = urljoin(website_url, href)
            css_links.append(full_url)

    for css_url in css_links[:3]:
        css_content = _fetch_css(css_url)
        if css_content:
            all_css += css_content + "\n"

    # 3. Wyciągnij kolory i czcionki
    colors = _extract_colors_from_css(all_css)
    font_families = _extract_font_families(all_css)

    # 4. Znajdź dominujące wartości
    primary_bg = _most_common(colors["bg_colors"], "#ffffff")
    primary_text = _most_common(colors["text_colors"], "#333333")
    primary_font = font_families[0] if font_families else ""

    # 5. Wyciągnij @font-face z CSS
    font_face_blocks = re.findall(r"@font-face\s*\{[^}]+\}", all_css, re.I | re.S)
    # fix relative URLs in @font-face
    fixed_font_faces = []
    for block in font_face_blocks[:5]:  # max 5
        # Replace relative url() with absolute
        def fix_url(m):
            url = m.group(1).strip("'\"")
            if not url.startswith(("http://", "https://", "data:")):
                url = urljoin(website_url, url)
            return f'url("{url}")'
        fixed = re.sub(r"url\(([^)]+)\)", fix_url, block)
        fixed_font_faces.append(fixed)

    # 6. Buduj finalny CSS
    parts = []

    if font_imports:
        parts.append(f"/* Czcionki ze strony */\n{font_imports}")

    if fixed_font_faces:
        parts.append("/* @font-face ze strony */\n" + "\n".join(fixed_font_faces))

    # Zmienne CSS
    css_vars = []
    if primary_bg:
        css_vars.append(f"  --site-bg: {primary_bg};")
    if primary_text:
        css_vars.append(f"  --site-text: {primary_text};")
    if primary_font:
        css_vars.append(f"  --site-font: {primary_font};")

    if css_vars:
        parts.append(":root {\n" + "\n".join(css_vars) + "\n}")

    body_rules = []
    if primary_font:
        body_rules.append(f"  font-family: {primary_font};")
    if primary_text:
        body_rules.append(f"  color: {primary_text};")
    if primary_bg:
        body_rules.append(f"  background-color: {primary_bg};")

    if body_rules:
        parts.append(".embed-booking-page {\n" + "\n".join(body_rules) + "\n}")

    return "\n\n".join(parts)
