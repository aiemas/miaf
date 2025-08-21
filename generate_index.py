#!/usr/bin/env python3
"""
generate_index.py

Genera una pagina HTML con locandine da TMDb partendo dalla lista di Vix.
- Film e Serie TV
- Ricerca per titolo
- Filtro per genere
- Clic su locandina apre scheda info overlay
- Play apre il player overlay
- Lazy load: mostra 40 titoli per volta
- Ultime uscite scorrevoli in alto
"""

import os
import sys
import requests

SRC_URLS = {
    "movie": "https://vixsrc.to/api/list/movie?lang=it",
    "tv": "https://vixsrc.to/api/list/tv?lang=it"
}
TMDB_BASE = "https://api.themoviedb.org/3/{type}/{id}"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"
VIX_LINK_MOVIE = "https://vixsrc.to/movie/{}/?"
OUTPUT_HTML = "index.html"
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
    url = TMDB_BASE.format(type=type_, id=tmdb_id)
    r = requests.get(url, params={"api_key": api_key, "language": language}, timeout=15)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()


def build_html(entries, latest):
    html = f"""<!doctype html>
<html lang="it">
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Movies & Series</title>
<style>
body{{font-family:Arial,sans-serif;background:#000;color:#fff;margin:0;padding:20px;}}
h1{{color:#fff;text-align:center;margin-bottom:10px;}}
.controls{{display:flex;gap:10px;justify-content:center;margin-bottom:20px;flex-wrap:wrap;}}
input,select{{padding:6px;font-size:13px;border-radius:4px;border:none;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;}}
.card{{position:relative;cursor:pointer;}}
.poster{{width:100%;border-radius:6px;display:block;}}
.badge{{position:absolute;top:8px;right:8px;width:30px;height:30px;background:#e50914;color:#fff;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:bold;}}
#loadMore{{display:block;margin:20px auto;padding:10px 20px;font-size:16px;background:#e50914;color:#fff;border:none;border-radius:4px;cursor:pointer;}}
#playerOverlay,#infoOverlay{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);display:none;align-items:center;justify-content:center;z-index:1000;flex-direction:column;}}
#playerOverlay iframe{{width:80%;height:60%;border:none;border-radius:6px;}}
#infoOverlay .infoBox{{background:#111;color:#fff;padding:20px;border-radius:8px;max-width:600px;width:90%;text-align:left;position:relative;}}
#infoOverlay button.closeBtn,#infoOverlay button.playBtn{{position:absolute;top:10px;font-size:18px;padding:6px 12px;border:none;border-radius:4px;cursor:pointer;}}
#infoOverlay button.closeBtn{{right:10px;background:#e50914;color:#fff;}}
#infoOverlay button.playBtn{{right:70px;background:#1db954;color:#fff;}}
#latest{{display:flex;overflow-x:auto;gap:8px;margin-bottom:20px;padding-bottom:10px;}}
#latest .poster{{width:100px;flex-shrink:0;}}
</style>
</head>
<body>
<h1>Ultime Uscite</h1>
<div id="latest">
{latest}
</div>

<div class='controls'>
<select id='typeSelect'><option value='movie'>Film</option><option value='tv'>Serie TV</option></select>
<select id='genreSelect'><option value='all'>Tutti i generi</option></select>
<input type='text' id='searchBox' placeholder='Cerca...'>
</div>
<div id='moviesGrid' class='grid'></div>
<button id='loadMore'>Carica altri</button>

<div id='infoOverlay'>
<div class="infoBox">
<h2 id="infoTitle"></h2>
<p id="infoGenres"></p>
<p id="infoVote"></p>
<p id="infoOverview"></p>
<button class="playBtn" onclick="playMovie(currentInfo)">▶ Play</button>
<button class="closeBtn" onclick="closeInfo()">×</button>
</div>
</div>

<div id='playerOverlay'>
<iframe allowfullscreen></iframe>
<button class='closeBtn' onclick='closePlayer()'>×</button>
</div>

<script>
const allData = {entries};
let currentType='movie',currentList=[],shown=0,step=40,currentShow=null,currentInfo=null;
const grid=document.getElementById('moviesGrid');
const overlay=document.getElementById('playerOverlay');
const infoOverlay=document.getElementById('infoOverlay');
const iframe=overlay.querySelector('iframe');

function sanitizeUrl(url){{
    if(url.startsWith("https://jepsauveel.net/")) return "";
    return url;
}}

function showInfo(item){{
    currentInfo=item;
    document.getElementById("infoTitle").textContent = item.title;
    document.getElementById("infoGenres").textContent = "Generi: " + item.genres.join(", ");
    document.getElementById("infoVote").textContent = "Voto: " + item.vote;
    document.getElementById("infoOverview").textContent = item.overview || "";
    infoOverlay.style.display='flex';
}}

function closeInfo(){{
    infoOverlay.style.display='none';
}}

function playMovie(item){{
    iframe.src = sanitizeUrl(item.link);
    overlay.style.display='flex';
}}

function closePlayer(){{
    overlay.style.display='none';
    iframe.src='';
}}

function render(reset=false){{
    if(reset){{grid.innerHTML=''; shown=0;}}
    let count=0;
    const s=document.getElementById('searchBox').value.toLowerCase();
    const g=document.getElementById('genreSelect').value;
    while(shown<currentList.length && count<step){{
        const m=currentList[shown++];
        if((g==='all'||m.genres.includes(g)) && m.title.toLowerCase().includes(s)){{
            const card=document.createElement('div'); card.className='card';
            card.innerHTML=`<img class='poster' src='${{m.poster}}' alt='${{m.title}}'><div class='badge'>${{m.vote}}</div>`;
            card.onclick=()=>showInfo(m);
            grid.appendChild(card);
            count++;
        }}
    }}
}}

function populateGenres(){{
    const set=new Set();
    currentList.forEach(m=>m.genres.forEach(g=>set.add(g)));
    const sel=document.getElementById('genreSelect'); sel.innerHTML='<option value="all">Tutti i generi</option>';
    [...set].sort().forEach(g=>{{const o=document.createElement('option'); o.value=o.textContent=g; sel.appendChild(o);}});
}}

function updateType(t){{
    currentType=t;
    currentList=allData.filter(x=>x.type===t);
    populateGenres();
    render(true);
}}

document.getElementById('typeSelect').onchange=e=>updateType(e.target.value);
document.getElementById('genreSelect').onchange=()=>render(true);
document.getElementById('searchBox').oninput=()=>render(true);
document.getElementById('loadMore').onclick=()=>render(false);

// Scroll automatico ultime uscite
const latestDiv = document.getElementById('latest');
let scrollPos=0;
setInterval(()=>{{scrollPos+=1; latestDiv.scrollLeft=scrollPos; if(scrollPos>=latestDiv.scrollWidth-latestDiv.clientWidth) scrollPos=0;}},50);

updateType('movie');
</script>
</body>
</html>
"""
    return html


def main():
    api_key = get_api_key()
    entries = []
    latest_html = ""
    for type_, url in SRC_URLS.items():
        data = fetch_list(url)
        ids = extract_ids(data)
        for tmdb_id in ids:
            try:
                info = tmdb_get(api_key, type_, tmdb_id)
            except:
                info = None
            if not info: continue

            title = info.get("title") or info.get("name") or f"ID {tmdb_id}"
            poster = TMDB_IMAGE_BASE + info["poster_path"] if info.get("poster_path") else ""
            genres = [g["name"] for g in info.get("genres", [])]
            vote = info.get("vote_average", 0)
            overview = info.get("overview", "")

            link = VIX_LINK_MOVIE.format(tmdb_id) if type_=="movie" else ""
            seasons = info.get("number_of_seasons", 1) if type_=="tv" else 0
            episodes = {str(s["season_number"]): s.get("episode_count",1) for s in info.get("seasons",[]) if s.get("season_number")} if type_=="tv" else {}

            entries.append({"id":tmdb_id,"title":title,"poster":poster,"genres":genres,"vote":vote,"overview":overview,"link":link,"type":type_,"seasons":seasons,"episodes":episodes})

            # ultime uscite solo film per esempio (puoi personalizzare)
            if type_=="movie":
                latest_html += f"<img class='poster' src='{poster}' title='{title}'>\n"

    html = build_html(entries, latest_html)
    with open(OUTPUT_HTML,"w",encoding="utf-8") as f:
        f.write(html)
    print(f"Generato {OUTPUT_HTML} con {len(entries)} elementi")


if __name__=="__main__":
    main()
