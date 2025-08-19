#!/usr/bin/env python3
import os
import sys
import requests

SRC_URL = "https://vixsrc.to/api/list/movie/?lang=It"
SRC_URL = "https://vixsrc.to/api/list/tv/?lang=It"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{}"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w200"  # poster più piccoli
VIX_LINK_TEMPLATE = "https://vixsrc.to/movie/{}/?"
OUTPUT_HTML = "movies_gallery.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; script/1.0)"}

def get_api_key():
    key = os.getenv("TMDB_API_KEY")
    if not key:
        print("Errore: imposta la variabile d'ambiente TMDB_API_KEY con la tua API key.", file=sys.stderr)
        sys.exit(1)
    return key

def fetch_list():
    r = requests.get(SRC_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()

def extract_ids(data):
    ids = []
    if isinstance(data, list):
        items = data
    else:
        items = data.get("results", []) if isinstance(data, dict) else []
    for item in items:
        if not isinstance(item, dict):
            continue
        val = None
        for key in ("tmdb_id", "tmdbId", "id"):
            if key in item and item[key]:
                val = item[key]
                break
        if val:
            ids.append(str(val))
    return sorted(set(ids), key=int)

def tmdb_get_movie(api_key, movie_id, language="it-IT"):
    url = TMDB_MOVIE_URL.format(movie_id)
    r = requests.get(url, params={"api_key": api_key, "language": language}, timeout=15)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

def build_html(entries):
    parts = [
        "<!doctype html>",
        "<html lang='it'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>Movies Gallery</title>",
        "<style>",
        "body{font-family:Arial,Helvetica,sans-serif;margin:20px;background:#000;color:#fff}",
        ".search{margin-bottom:20px}",
        ".search input{padding:8px;font-size:16px;width:100%;max-width:400px;border-radius:6px;border:none}",
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}",
        ".card{background:none;padding:0;text-align:center}",
        ".poster{width:100%;border-radius:6px;cursor:pointer;transition:transform 0.2s}",
        ".poster:hover{transform:scale(1.05)}",
        ".title{font-size:14px;margin-top:6px;color:#fff}",
        "</style>",
        "<script>",
        "function searchMovies(){",
        "  let input=document.getElementById('searchInput').value.toLowerCase();",
        "  let cards=document.getElementsByClassName('card');",
        "  for(let i=0;i<cards.length;i++){",
        "    let title=cards[i].getAttribute('data-title').toLowerCase();",
        "    cards[i].style.display=title.includes(input)?'block':'none';",
        "  }",
        "}",
        "</script>",
        "</head><body>",
        "<h1>Movies Gallery</h1>",
        "<div class='search'><input type='text' id='searchInput' onkeyup='searchMovies()' placeholder='Cerca un film...'></div>",
        "<div class='grid'>"
    ]
    for movie_id, title, poster_url in entries:
        title_safe = title or f"ID {movie_id}"
        vix_link = VIX_LINK_TEMPLATE.format(movie_id)
        poster_tag = f"<a href='{vix_link}' target='_blank'><img class='poster' src='{poster_url}' alt='{title_safe}'></a>" if poster_url else ""
        card = f"<div class='card' data-title='{title_safe}'>{poster_tag}<div class='title'>{title_safe}</div></div>"
        parts.append(card)
    parts.extend(["</div></body></html>"])
    return "\n".join(parts)

def main():
    api_key = get_api_key()
    data = fetch_list()
    ids = extract_ids(data)
    if not ids:
        print("Nessun id trovato.")
        return
    entries = []
    for movie_id in ids:
        try:
            info = tmdb_get_movie(api_key, movie_id)
        except Exception as e:
            print(f"Errore TMDb per {movie_id}: {e}", file=sys.stderr)
            info = None
        title = info.get("title") if info else None
        poster_path = info.get("poster_path") if info else None
        poster_url = TMDB_IMAGE_BASE + poster_path if poster_path else None
        entries.append((movie_id, title, poster_url))
    html = build_html(entries)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generato {OUTPUT_HTML} con {len(entries)} elementi")

if __name__ == "__main__":
    main()
