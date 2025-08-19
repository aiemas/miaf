#!/usr/bin/env python3
"""
generate_movies_page.py
- legge la lista da https://vixsrc.to/api/list/movie/?lang=It
- estrae tmdb_id
- usa l'API TMDb per ottenere titolo, poster, voto, genere
- genera un file HTML con:
    * locandina cliccabile (apre player)
    * badge del voto
    * dropdown per filtrare per genere
    * caricamento progressivo (100 alla volta)
"""

import os
import sys
import requests

SRC_URL = "https://vixsrc.to/api/list/movie/?lang=It"
SRC_URL = "https://vixsrc.to/api/list/tv/?lang=It"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{}"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"
VIX_LINK_TEMPLATE = "https://vixsrc.to/movie/{}/?"
OUTPUT_HTML = "movies_miniplayers.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; script/1.0)"}


def get_api_key():
    key = os.getenv("TMDB_API_KEY")
    if not key:
        print("Errore: imposta TMDB_API_KEY nelle variabili d'ambiente.", file=sys.stderr)
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
        if isinstance(item, dict):
            val = item.get("tmdb_id") or item.get("tmdbId") or item.get("id")
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


def build_html(entries, genres_set):
    parts = [
        "<!doctype html>",
        "<html lang='it'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
        "<title>Movies MiniPlayers</title>",
        "<style>",
        "body{font-family:Arial,Helvetica,sans-serif;margin:20px;background:#000;color:#fff}",
        ".grid{display:flex;flex-wrap:wrap;gap:10px;justify-content:center}",
        ".card{position:relative;cursor:pointer;}",
        ".poster{width:180px;height:auto;border-radius:4px;display:block}",
        ".badge{position:absolute;top:6px;right:6px;background:rgba(0,0,0,0.7);color:#fff;padding:2px 6px;border-radius:4px;font-size:12px;font-weight:bold}",
        ".controls{margin-bottom:20px;text-align:center}",
        "select,input,button{padding:6px 10px;margin:5px;font-size:14px;border-radius:4px;border:1px solid #444;background:#111;color:#fff}",
        "button{cursor:pointer;}",
        "</style></head><body>",
        "<h1 style='text-align:center'>Movies MiniPlayers</h1>",
        "<div class='controls'>",
        "<label for='genreSelect'>Genere:</label>",
        "<select id='genreSelect'><option value='all'>Tutti</option>"
    ]

    # Dropdown generi
    for g in sorted(genres_set):
        parts.append(f"<option value='{g}'>{g}</option>")
    parts.append("</select>")

    # Ricerca
    parts.append("<input type='text' id='searchBox' placeholder='Cerca film...'>")

    parts.append("</div><div class='grid' id='moviesGrid'></div>")
    parts.append("<div style='text-align:center'><button id='loadMoreBtn'>Carica altri</button></div>")

    # JS per filtro + ricerca + caricamento progressivo
    parts.append("""
<script>
const allMovies = %s;
let shown = 0;
const step = 100;

function renderMovies(reset=false){
  const grid = document.getElementById('moviesGrid');
  if(reset){ grid.innerHTML = ''; shown = 0; }
  let count = 0;
  const searchVal = document.getElementById('searchBox').value.toLowerCase();
  const genreVal = document.getElementById('genreSelect').value;
  while(shown < allMovies.length && count < step){
    const m = allMovies[shown];
    shown++;
    if((genreVal==='all' || m.genres.includes(genreVal)) &&
       (m.title.toLowerCase().includes(searchVal))){
      const card = document.createElement('div');
      card.className='card';
      card.innerHTML = `<img class='poster' src='${m.poster}' alt='${m.title}'>
                        <div class='badge'>${m.vote}</div>`;
      card.onclick = ()=> window.open(m.link,'_blank');
      grid.appendChild(card);
      count++;
    }
  }
}

document.getElementById('loadMoreBtn').onclick = ()=>renderMovies();
document.getElementById('searchBox').oninput = ()=>renderMovies(true);
document.getElementById('genreSelect').onchange = ()=>renderMovies(true);

renderMovies();
</script>
""" % (str([
        {"id": mid, "title": title or f"ID {mid}", "poster": poster, "vote": vote, "genres": genres, "link": link}
        for mid, title, poster, vote, genres, link in entries
    ])))

    parts.append("</body></html>")
    return "\n".join(parts)


def main():
    api_key = get_api_key()
    data = fetch_list()
    ids = extract_ids(data)
    if not ids:
        print("Nessun id trovato.")
        return

    entries = []
    genres_set = set()
    for movie_id in ids:
        try:
            info = tmdb_get_movie(api_key, movie_id)
        except Exception as e:
            print(f"Errore TMDb per {movie_id}: {e}", file=sys.stderr)
            continue
        if not info:
            continue
        title = info.get("title")
        poster_path = info.get("poster_path")
        poster_url = TMDB_IMAGE_BASE + poster_path if poster_path else None
        vote = info.get("vote_average", 0)
        genres = [g["name"] for g in info.get("genres", [])]
        for g in genres:
            genres_set.add(g)
        vix_link = VIX_LINK_TEMPLATE.format(movie_id)
        entries.append((movie_id, title, poster_url, vote, genres, vix_link))

    html = build_html(entries, genres_set)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generato {OUTPUT_HTML} con {len(entries)} film")

if __name__ == "__main__":
    main()
