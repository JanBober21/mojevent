"""
Import danych firmy z Facebooka i Instagrama.

Pobiera publicznie dostępne informacje z profili:
- Nazwa firmy
- Opis / bio
- Zdjęcie profilowe / cover photo
- Adres, telefon, strona www (Facebook)
- Linki do zdjęć z galerii
"""

import re
import json
import logging
from urllib.parse import urljoin, urlparse

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


def _fetch(url: str) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as exc:
        logger.warning("Nie udało się pobrać %s: %s", url, exc)
        return None


def _og(soup: BeautifulSoup, prop: str) -> str:
    """Wyciągnij wartość Open Graph meta tag."""
    tag = soup.find("meta", property=f"og:{prop}")
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""


def _meta(soup: BeautifulSoup, name: str) -> str:
    """Wyciągnij wartość <meta name=...> tag."""
    tag = soup.find("meta", attrs={"name": name})
    if tag and tag.get("content"):
        return tag["content"].strip()
    return ""


def import_from_facebook(url: str) -> dict:
    """
    Importuj dane z publicznej strony Facebook.

    Returns dict with keys:
        name, description, image_url, images, phone, website, address, city
    """
    result = {
        "name": "",
        "description": "",
        "image_url": "",
        "images": [],
        "phone": "",
        "website": "",
        "address": "",
        "city": "",
    }

    if not url:
        return result

    # Normalizuj URL
    if not url.startswith("http"):
        url = "https://" + url

    html = _fetch(url)
    if not html:
        return result

    soup = BeautifulSoup(html, "html.parser")

    # Nazwa
    result["name"] = _og(soup, "title") or soup.title.get_text().strip() if soup.title else ""
    # Oczyść nazwy typu "Nazwa - Facebook"
    if result["name"]:
        result["name"] = re.sub(r"\s*[-–|]\s*(Facebook|FB).*$", "", result["name"], flags=re.I).strip()

    # Opis
    result["description"] = _og(soup, "description") or _meta(soup, "description") or ""
    # Oczyść opisy Facebooka
    if result["description"]:
        # Usuń standardowe prefiksy FB
        result["description"] = re.sub(
            r"^.*?(polubi[łl][oa]?|lubi to|like[sd]?).*?\.\s*",
            "", result["description"], count=1, flags=re.I
        ).strip()

    # Zdjęcie
    og_img = _og(soup, "image")
    if og_img:
        result["image_url"] = og_img
        result["images"].append(og_img)

    # Szukaj dodatkowych zdjęć w JSON-LD lub data atrybutach
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, dict):
                if data.get("image"):
                    img = data["image"]
                    if isinstance(img, str) and img not in result["images"]:
                        result["images"].append(img)
                    elif isinstance(img, dict) and img.get("url"):
                        if img["url"] not in result["images"]:
                            result["images"].append(img["url"])
                    elif isinstance(img, list):
                        for i in img:
                            u = i if isinstance(i, str) else (i.get("url", "") if isinstance(i, dict) else "")
                            if u and u not in result["images"]:
                                result["images"].append(u)
                # Adres
                addr = data.get("address", {})
                if isinstance(addr, dict):
                    result["address"] = addr.get("streetAddress", "")
                    result["city"] = addr.get("addressLocality", "")
                # Telefon
                if data.get("telephone"):
                    result["phone"] = data["telephone"]
                # Strona
                if data.get("url") and "facebook.com" not in data["url"]:
                    result["website"] = data["url"]
        except (json.JSONDecodeError, TypeError):
            pass

    # Szukaj zdjęć w <img> tagach z dużymi rozmiarami
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue
        # Pomijaj ikony/emoji/trackers
        if any(skip in src for skip in ["emoji", "pixel", "tr?", "1x1", ".gif", "static"]):
            continue
        # Tylko duże zdjęcia z Facebooka
        if ("scontent" in src or "fbcdn" in src) and src not in result["images"]:
            result["images"].append(src)
        if len(result["images"]) >= 10:
            break

    return result


def import_from_instagram(url: str) -> dict:
    """
    Importuj dane z publicznego profilu Instagram.

    Returns dict with keys:
        name, description, image_url, images
    """
    result = {
        "name": "",
        "description": "",
        "image_url": "",
        "images": [],
    }

    if not url:
        return result

    if not url.startswith("http"):
        url = "https://" + url

    html = _fetch(url)
    if not html:
        return result

    soup = BeautifulSoup(html, "html.parser")

    # Nazwa
    result["name"] = _og(soup, "title") or ""
    if result["name"]:
        # Oczyść "Nazwa (@handle) • Instagram photos and videos"
        result["name"] = re.sub(r"\s*\(@[^)]+\).*$", "", result["name"]).strip()
        result["name"] = re.sub(r"\s*[•·|]\s*Instagram.*$", "", result["name"], flags=re.I).strip()

    # Opis / bio
    desc = _og(soup, "description") or _meta(soup, "description") or ""
    if desc:
        # Wyciągnij bio — format: "123 Followers, 45 Following, 67 Posts - See Instagram photos..."
        # Bio jest zwykle po ostatnim " - " przed "See Instagram"
        bio_match = re.search(r'[\u201c\u201d""](.+?)[\u201c\u201d""]', desc)
        if bio_match:
            result["description"] = bio_match.group(1).strip()
        else:
            # Spróbuj wyciągnąć cokolwiek sensownego
            cleaned = re.sub(
                r"\d+\s*(Followers?|Following|Posts?|Obserwuj[ąa]c[ye]|obserwowani|post[óo]w).*?[-–]?\s*",
                "", desc, flags=re.I
            ).strip()
            cleaned = re.sub(r"See Instagram.*$", "", cleaned, flags=re.I).strip()
            result["description"] = cleaned

    # Zdjęcie profilowe
    og_img = _og(soup, "image")
    if og_img:
        result["image_url"] = og_img
        result["images"].append(og_img)

    # Szukaj zdjęć w JSON danych na stronie
    for script in soup.find_all("script"):
        text = script.string or ""
        # Instagram osadza dane w shared_data lub window.__additionalDataLoaded
        if "profile_pic_url" in text or "display_url" in text:
            # Wyciągnij URL-e zdjęć
            for m in re.finditer(r'"display_url"\s*:\s*"([^"]+)"', text):
                img_url = m.group(1).replace("\\u0026", "&")
                if img_url not in result["images"]:
                    result["images"].append(img_url)
                if len(result["images"]) >= 10:
                    break
            # Zdjęcie profilowe HD
            for m in re.finditer(r'"profile_pic_url_hd"\s*:\s*"([^"]+)"', text):
                img_url = m.group(1).replace("\\u0026", "&")
                if not result["image_url"]:
                    result["image_url"] = img_url
                if img_url not in result["images"]:
                    result["images"].insert(0, img_url)

    # Szukaj zdjęć w meta tagach
    for meta in soup.find_all("meta", property=re.compile(r"og:image")):
        img = meta.get("content", "")
        if img and img not in result["images"]:
            result["images"].append(img)

    return result


def import_from_social(facebook_url: str = "", instagram_url: str = "") -> dict:
    """
    Importuj dane z obu platform i połącz wyniki.

    Priorytet: Facebook (więcej danych), uzupełnione przez Instagram.

    Returns dict with keys:
        name, description, image_url, images, phone, website, address, city, source
    """
    result = {
        "name": "",
        "description": "",
        "image_url": "",
        "images": [],
        "phone": "",
        "website": "",
        "address": "",
        "city": "",
        "source": [],
    }

    # Facebook
    if facebook_url:
        fb = import_from_facebook(facebook_url)
        if fb["name"]:
            result["name"] = fb["name"]
        if fb["description"]:
            result["description"] = fb["description"]
        if fb["image_url"]:
            result["image_url"] = fb["image_url"]
        result["images"].extend(fb["images"])
        if fb["phone"]:
            result["phone"] = fb["phone"]
        if fb["website"]:
            result["website"] = fb["website"]
        if fb["address"]:
            result["address"] = fb["address"]
        if fb["city"]:
            result["city"] = fb["city"]
        result["source"].append("facebook")

    # Instagram
    if instagram_url:
        ig = import_from_instagram(instagram_url)
        if not result["name"] and ig["name"]:
            result["name"] = ig["name"]
        if not result["description"] and ig["description"]:
            result["description"] = ig["description"]
        if not result["image_url"] and ig["image_url"]:
            result["image_url"] = ig["image_url"]
        for img in ig["images"]:
            if img not in result["images"]:
                result["images"].append(img)
        result["source"].append("instagram")

    # Deduplikuj images
    seen = set()
    unique_images = []
    for img in result["images"]:
        if img not in seen:
            seen.add(img)
            unique_images.append(img)
    result["images"] = unique_images[:12]  # max 12

    return result
