#!/usr/bin/env python3
"""
generate_movies_page.py
- legge le liste da vixsrc.to (film + serie TV)
- estrae tmdb_id
- usa l'API TMDb per ottenere titolo e poster
- genera un file HTML con poster cliccabili
- poster -> apre il player in un overlay con comandi grandi
"""

import os
import sys
import requests

SRC_MOVIES = "https://vixsrc.to/api/list/movie/?lang=It"
SRC_SERIES = "https://vixsrc.to/api/list/tv/?lang=It"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/{}/{}"  # tipo (movie/tv), id
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"
VIX_LINK_TEMPLATE = "https://vixsrc.to/{}/{}"  # tipo (movie/tv), id
OUTPUT_HTML = "movies_miniplayers.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; script/1.0)"}

def get_api_key():
    key = os.getenv("TMDB_API_KEY")
    if not key:
        print("Errore: TMDB_API_KEY mancante", file=sys.stderr)
        sys.exit(1)
    return key

def fetch_list(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()

def extract_ids(data):
    ids = []
    if isinstance(data, list):
        items = data
    else:
        items = data.get("results", []) if isinstance(data, dict) else []
    for item in items:
        if isinstance(item, dict):
            val = item.get("tmdb_id") or item.get("id")
            if val:
                ids.append(str(val))
    return sorted(set(ids), key=int)

def tmdb_get(api_key, tmdb_type, tmdb_id, language="it-IT"):
    url = TMDB_MOVIE_URL.format(tmdb_type, tmdb_id)
    r = requests.get(url, params={"api_key": api_key, "language": language}, timeout=15)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

def build_html(movies, series):
    parts = [
        "<!doctype html>",
        "<html lang='it'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>Movies & Serie TV</title>",
        "<style>",
        "body{font-family:Arial,Helvetica,sans-serif;margin:0;background:#000;color:#fff}",
        "h1{padding:20px;text-align:center;background:#111;margin:0}",
        ".menu{display:flex;justify-content:center;gap:20px;padding:15px;background:#111;}",
        ".menu button{padding:10px 20px;border:none;border-radius:5px;background:#444;color:#fff;font-size:16px;cursor:pointer}",
        ".menu button:hover{background:#666}",
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px;padding:20px}",
        ".card{cursor:pointer;text-align:center}",
        ".poster{width:100%;border-radius:6px;transition:transform 0.2s}",
        ".poster:hover{transform:scale(1.05)}",
        "/* overlay player */",
        "#overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:1000;align-items:center;justify-content:center}",
        "#overlay iframe{width:80%;height:80%;border:none;border-radius:10px}",
        "#overlay .close{position:absolute;top:20px;right:30px;font-size:40px;color:#fff;cursor:pointer}",
        "/* comandi video grandi */",
        "video::-webkit-media-controls{transform:scale(1.5)}",
        "</style></head><body>",
        "<h1>Movies & Serie TV</h1>",
        "<div class='menu'>",
        "<button onclick=\"showSection('movies')\">🎬 Film</button>",
        "<button onclick=\"showSection('series')\">📺 Serie TV</button>",
        "</div>",
        "<div id='movies' class='grid'>"
    ]
    for tmdb_id, title, poster_url in movies:
        parts.append(f"<div class='card' onclick=\"openPlayer('movie','{tmdb_id}')\"><img class='poster' src='{poster_url}' alt='{title}'><div>{title}</div></div>")
    parts.append("</div><div id='series' class='grid' style='display:none'>")
    for tmdb_id, title, poster_url in series:
        parts.append(f"<div class='card' onclick=\"openPlayer('tv','{tmdb_id}')\"><img class='poster' src='{poster_url}' alt='{title}'><div>{title}</div></div>")
    parts.append("</div>")
    # overlay
    parts.append("""
<div id="overlay" onclick="closePlayer(event)">
  <span class="close" onclick="closePlayer(event)">&times;</span>
  <iframe id="playerFrame" src=""></iframe>
</div>
<script>
function showSection(id){
  document.getElementById('movies').style.display = (id==='movies'?'grid':'none');
  document.getElementById('series').style.display = (id==='series'?'grid':'none');
}
function openPlayer(type,id){
  document.getElementById('overlay').style.display='flex';
  document.getElementById('playerFrame').src=`https://vixsrc.to/${type}/${id}/?`;
}
function closePlayer(e){
  if(e.target.id==='overlay' || e.target.className==='close'){
    document.getElementById('overlay').style.display='none';
    document.getElementById('playerFrame').src='';
  }
}
</script>""")
    parts.append("</body></html>")
    return "\n".join(parts)

def main():
    api_key = get_api_key()
    movies = []
    series = []

    # film
    try:
        data = fetch_list(SRC_MOVIES)
        ids = extract_ids(data)
        for movie_id in ids:
            info = tmdb_get(api_key, "movie", movie_id)
            if info:
                title = info.get("title") or f"Film {movie_id}"
                poster_path = info.get("poster_path")
                poster_url = TMDB_IMAGE_BASE + poster_path if poster_path else ""
                movies.append((movie_id, title, poster_url))
    except Exception as e:
        print(f"Errore film: {e}", file=sys.stderr)

    # serie
    try:
        data = fetch_list(SRC_SERIES)
        ids = extract_ids(data)
        for tv_id in ids:
            info = tmdb_get(api_key, "tv", tv_id)
            if info:
                title = info.get("name") or f"Serie {tv_id}"
                poster_path = info.get("poster_path")
                poster_url = TMDB_IMAGE_BASE + poster_path if poster_path else ""
                series.append((tv_id, title, poster_url))
    except Exception as e:
        print(f"Errore serie: {e}", file=sys.stderr)

    html = build_html(movies, series)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generato {OUTPUT_HTML} con {len(movies)} film e {len(series)} serie")

if __name__ == "__main__":
    main()
