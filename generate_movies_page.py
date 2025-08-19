#!/usr/bin/env python3
"""
generate_movies_page.py

Genera una pagina HTML con locandine da TMDb partendo dalla lista di Vix.
- Film e Serie TV (due tendine: Movies / Series)
- Ricerca per titolo
- Filtro per genere
- Clic su locandina apre player in modale fullscreen (iframe con allowfullscreen)
- Lazy load: mostra 40 titoli per volta
"""

import os, sys, requests

# --- Config ---
SRC_URLS = {
    "movie": "https://vixsrc.to/api/list/movie/?lang=It",
    "tv": "https://vixsrc.to/api/list/tv/?lang=It"
}
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/{type}/{id}"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"
VIX_LINK_TEMPLATE = "https://vixsrc.to/{type}/{}/?"
OUTPUT_HTML = "movies_miniplayers.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; script/1.0)"}


def get_api_key():
    key = os.getenv("TMDB_API_KEY")
    if not key:
        print("Errore: manca TMDB_API_KEY", file=sys.stderr)
        sys.exit(1)
    return key


def fetch_list(url):
    r = requests.get(url, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def extract_ids(data):
    ids = []
    items = data if isinstance(data, list) else data.get("results", [])
    for item in items:
        if not isinstance(item, dict):
            continue
        for key in ("tmdb_id", "tmdbId", "id"):
            if key in item and item[key]:
                ids.append(str(item[key]))
                break
    return sorted(set(ids), key=int)


def tmdb_get(api_key, type_, tmdb_id, language="it-IT"):
    url = TMDB_MOVIE_URL.format(type=type_, id=tmdb_id)
    r = requests.get(url, params={"api_key": api_key, "language": language}, timeout=15)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def build_html(entries):
    parts = [
        "<!doctype html>",
        "<html lang='it'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>Movies & Series</title>",
        "<style>",
        "body{font-family:Arial,sans-serif;background:#000;color:#fff;margin:0;padding:20px;}",
        "h1{color:#fff;text-align:center;margin-bottom:20px;}",
        ".controls{display:flex;gap:10px;justify-content:center;margin-bottom:20px;}",
        "input,select{padding:8px;font-size:14px;border-radius:4px;border:none;}",
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;}",
        ".card{position:relative;cursor:pointer;}",
        ".poster{width:100%;border-radius:6px;display:block;}",
        ".badge{position:absolute;bottom:8px;right:8px;background:rgba(0,0,0,0.7);color:#fff;",
        "padding:2px 6px;font-size:12px;border-radius:4px;}",
        "#loadMore{display:block;margin:20px auto;padding:10px 20px;font-size:16px;",
        "background:#e50914;color:#fff;border:none;border-radius:4px;cursor:pointer;}",
        "#playerOverlay{position:fixed;top:0;left:0;width:100%;height:100%;",
        "background:rgba(0,0,0,0.85);display:flex;align-items:center;justify-content:center;",
        "z-index:1000;}",
        "#playerOverlay iframe{width:80%;height:80%;border:none;}",
        "#playerOverlay button{position:absolute;top:20px;right:40px;font-size:30px;",
        "background:transparent;border:none;color:#fff;cursor:pointer;}",
        "</style></head><body>",
        "<h1>Movies & Series</h1>",
        "<div class='controls'>",
        "<select id='typeSelect'><option value='movie'>Film</option><option value='tv'>Serie TV</option></select>",
        "<select id='genreSelect'><option value='all'>Tutti i generi</option></select>",
        "<input type='text' id='searchBox' placeholder='Cerca...'>",
        "</div>",
        "<div id='moviesGrid' class='grid'></div>",
        "<button id='loadMore'>Carica altri</button>",
        "<div id='playerOverlay' style='display:none;'>",
        "<button onclick=\"document.getElementById('playerOverlay').style.display='none'\">×</button>",
        "<iframe allowfullscreen></iframe></div>",
        "<script>",
        f"const allData = {entries};",
        "let currentType='movie',currentList=[],shown=0,step=40;",
        "const grid=document.getElementById('moviesGrid');",
        "const overlay=document.getElementById('playerOverlay');",
        "const iframe=overlay.querySelector('iframe');",
        "function openPlayer(url){overlay.style.display='flex';iframe.src=url;}",
        "function closePlayer(){overlay.style.display='none';iframe.src='';}",
        "function render(reset=false){",
        " if(reset){grid.innerHTML='';shown=0;}",
        " let count=0;",
        " const s=document.getElementById('searchBox').value.toLowerCase();",
        " const g=document.getElementById('genreSelect').value;",
        " while(shown<currentList.length && count<step){",
        "  const m=currentList[shown++];",
        "  if((g==='all'||m.genres.includes(g))&&m.title.toLowerCase().includes(s)){",
        "   const card=document.createElement('div');card.className='card';",
        "   card.innerHTML=`<img class='poster' src='${m.poster}' alt='${m.title}'><div class='badge'>★ ${m.vote}</div>`;",
        "   card.onclick=()=>openPlayer(m.link);",
        "   grid.appendChild(card);count++;}}}",
        "function populateGenres(){const set=new Set();currentList.forEach(m=>m.genres.forEach(g=>set.add(g)));",
        " const sel=document.getElementById('genreSelect');sel.innerHTML='<option value=\"all\">Tutti i generi</option>';",
        " [...set].sort().forEach(g=>{const o=document.createElement('option');o.value=o.textContent=g;sel.appendChild(o);});}",
        "function updateType(t){currentType=t;currentList=allData.filter(x=>x.type===t);populateGenres();render(true);}",
        "document.getElementById('typeSelect').onchange=e=>updateType(e.target.value);",
        "document.getElementById('genreSelect').onchange=()=>render(true);",
        "document.getElementById('searchBox').oninput=()=>render(true);",
        "document.getElementById('loadMore').onclick=()=>render(false);",
        "updateType('movie');",
        "</script></body></html>"
    ]
    return "\n".join(parts)


def main():
    api_key = get_api_key()
    entries = []
    for type_, url in SRC_URLS.items():
        data = fetch_list(url)
        ids = extract_ids(data)
        for tmdb_id in ids:
            try:
                info = tmdb_get(api_key, type_, tmdb_id)
            except Exception as e:
                print(f"Errore TMDb {tmdb_id}: {e}", file=sys.stderr)
                info = None
            if not info: 
                continue
            title = info.get("title") or info.get("name") or f"ID {tmdb_id}"
            poster = TMDB_IMAGE_BASE + info["poster_path"] if info.get("poster_path") else ""
            genres = [g["name"] for g in info.get("genres", [])]
            vote = info.get("vote_average", 0)
            link = VIX_LINK_TEMPLATE.format(tmdb_id, type=type_)
            entries.append({
                "id": tmdb_id,
                "title": title,
                "poster": poster,
                "genres": genres,
                "vote": vote,
                "link": link,
                "type": type_
            })
    html = build_html(entries)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generato {OUTPUT_HTML} con {len(entries)} elementi")


if __name__ == "__main__":
    main()
