#!/usr/bin/env python3
"""
generate_movies_page.py
- legge la lista da https://vixsrc.to/api/list/movie/?lang=It
- estrae tmdb_id
- usa l'API TMDb per ottenere il titolo e il poster (API key da env TMDB_API_KEY)
- genera un file HTML con iframe (src -> https://vixsrc.to/movie/<id>/?)
Nota: non viene fatto alcun delay tra richieste; attenzione ai rate limit.
"""

import os
import sys
import requests

SRC_URL = "https://vixsrc.to/api/list/movie/?lang=It"
SRC_URL = "https://vixsrc.to/api/list/tv/?lang=It"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{}"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"  # modifica dimensione se vuoi
VIX_LINK_TEMPLATE = "https://vixsrc.to/movie/{}/?"
OUTPUT_HTML = "movies_miniplayers.html"
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
    # data è una lista di dict come: [{"tmdb_id":75970}, {"tmdb_id":61575}, ...]
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
        <!doctype html>
        <html lang='it'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
        <title>Movies MiniPlayers</title>
        <style>
        body{font-family:Arial,Helvetica,sans-serif;margin:20px;background:#f7f7f7}
        .grid{display:flex;flex-wrap:wrap;gap:12px}
        .card{background:#fff;border:1px solid #ddd;border-radius:6px;padding:10px;width:320px;box-shadow:0 1px 3px rgba(0,0,0,0.08)}
        .title{font-size:16px;margin-bottom:8px;font-weight:700}
        .poster{width:18%;height:auto;border-radius:3px;margin-bottom:5px} /* Modifica la larghezza qui */
        .playframe{width:100%;height:200px;border:1px solid #ccc;border-radius:4px}
        .note{font-size:12px;color:#666;margin-top:8px}
        </style></head><body>
        <h1>Movies MiniPlayers</h1>
        <div class='grid'>
        
        

    ]
    for movie_id, title, poster_url in entries:
        title_safe = title or f"ID {movie_id}"
        poster_tag = f"<img class='poster' src='{poster_url}' alt='poster'>" if poster_url else ""
        vix_link = VIX_LINK_TEMPLATE.format(movie_id)
        card = (
            f"<div class='card'>"
            f"<div class='title'>{title_safe}</div>"
            f"{poster_tag}"
            f"<iframe class='playframe' src='{vix_link}' loading='lazy' sandbox='allow-scripts allow-same-origin' ></iframe>"
            f"<div class='note'>Se l'iframe non viene caricato, apri il link: <a href='{vix_link}' target='_blank' rel='noopener'>{vix_link}</a></div>"
            f"</div>"
        )
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
