#!/usr/bin/env python3
# search_scraper_pro.py (only Nexdrive links + max 4 screenshots)
import os, sys, re, json, time, requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from termcolor import colored

BASE = "https://vegamovies.menu/"
HEADERS = {"User-Agent": "Mozilla/5.0 (Linux; Android 12; Mobile) Chrome/124 Safari/537.36"}
KNOWN_HOSTS = ["nexdrive"]  # only nexdrive links allowed
QUALITY_RE = re.compile(r"(\d{3,4}p|4k)", re.I)
SIZE_RE = re.compile(r"(\d+(?:\.\d+)?\s?(?:MB|GB))", re.I)

def soup_from(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def safe_text(el):
    return el.get_text(" ", strip=True) if el else ""

def likely_download(href, text):
    if not href or href.startswith("javascript") or href.strip() in ("#", ""):
        return False
    if any(x in href for x in ["/wp-json/", "mailto:", "tel:", "comment"]):
        return False
    # ✅ only nexdrive
    if "nexdrive" in href.lower():
        return True
    t = text.lower()
    if re.search(r"(download|480p|720p|1080p|2160p|4k|web-dl|webrip)", t):
        return "nexdrive" in href.lower()
    return False

def find_movie(query):
    q = quote_plus(query)
    url = f"{BASE}?s={q}"
    soup = soup_from(url)
    link = soup.select_one("h2 a, h3 a, .entry-title a")
    if link and link.get("href"):
        return urljoin(BASE, link["href"])
    return None

def get_host(url):
    from urllib.parse import urlparse
    try: return urlparse(url).hostname or ""
    except: return ""

def extract_downloads(soup, page_url):
    groups, current = [], None
    for el in soup.find_all(["p", "div", "li", "strong", "span", "a"]):
        text = safe_text(el)
        q = QUALITY_RE.search(text)
        s = SIZE_RE.search(text)
        if q:
            current = {"quality": q.group(1).upper(), "size": s.group(1) if s else "", "links": []}
            groups.append(current)
        if el.name == "a" and el.get("href"):
            href = urljoin(page_url, el["href"].strip())
            label = safe_text(el)
            if likely_download(href, label):
                if not current:
                    current = {"quality": "", "size": "", "links": []}
                    groups.append(current)
                if not any(l["url"] == href for l in current["links"]):
                    current["links"].append({
                        "label": label or href,
                        "url": href,
                        "host": get_host(href)
                    })
    groups = [g for g in groups if g["links"]]
    return groups

def scrape_movie(url):
    soup = soup_from(url)
    title = safe_text(soup.find("h1")) or safe_text(soup.title)
    desc = ""
    for p in soup.select("article p, .post-body p, .entry-content p"):
        t = safe_text(p)
        if len(t) > 30:
            desc = t; break
    poster = ""
    m = soup.find("meta", property="og:image")
    if m and m.get("content"): poster = urljoin(url, m["content"])
    # ✅ max 4 screenshots
    screenshots = [urljoin(url, img["src"]) for img in soup.select(".post-body img, .entry-content img")[:4] if img.get("src")]
    downloads = extract_downloads(soup, url)
    return {"title": title, "poster": poster, "summary": desc, "screenshots": screenshots, "downloads": downloads, "page_url": url}

def colorful_print(movie):
    print(colored(f"\n🎬  {movie['title']}", "cyan", attrs=["bold"]))
    print(colored(f"📜  {movie['summary'][:200]}...", "white"))
    print(colored(f"🖼  Poster: {movie['poster']}", "yellow"))
    print(colored("─"*40, "blue"))
    for g in movie["downloads"]:
        q = g["quality"] or "Other"
        s = g["size"] or ""
        print(colored(f"🔰  {q} {s}", "green"))
        for l in g["links"]:
            print(colored(f"➡️  {l['host']}: {l['url']}", "magenta"))
        print(colored("─"*40, "blue"))
    print(colored("💾  Saved: data/search_result.json\n", "yellow"))

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_scraper_pro.py \"Movie Name\""); sys.exit(0)
    query = " ".join(sys.argv[1:])
    print(colored(f"[INFO] Searching for {query}", "cyan"))
    link = find_movie(query)
    if not link:
        print(colored("❌ Movie not found!", "red")); sys.exit(1)
    print(colored(f"[FOUND] {link}", "yellow"))
    movie = scrape_movie(link)
    os.makedirs("data", exist_ok=True)
    with open("data/search_result.json", "w", encoding="utf-8") as f:
        json.dump(movie, f, indent=2, ensure_ascii=False)
    colorful_print(movie)

if __name__ == "__main__":
    main()
