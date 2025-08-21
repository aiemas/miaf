#!/usr/bin/env python3
"""
generate_index.py

Genera una pagina HTML con locandine da TMDb partendo dalla lista di Vix.
- Film e Serie TV (due tendine: Movies / Series)
- Ricerca per titolo
- Filtro per genere
- Clic su locandina apre scheda con info in sovraimpressione
- Player incluso, fullscreen opzionale
- Lazy load: mostra 40 titoli per volta
- Sezione ultime uscite (primi 10)
"""

import os
import sys
import requests

# --- Config ---
SRC_URLS = {
    "movie": "https://vixsrc.to/api/list/movie?lang=it",
    "tv": "https://vixsrc.to/api/list/tv?lang=it"
}
TMDB_BASE = "https://api.themoviedb.org/3/{type}/{id}"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w300"
VIX_LINK_MOVIE = "https://vixsrc.to/movie/{}/?"
VIX_LINK_SERIE = "https://vixsrc.to/tv/{}/{}/{}"
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
body{{font-family:Arial,sans-serif;background:#141414;color:#fff;margin:0;padding:20px;}}
h1{{color:#e50914;text-align:center;margin-bottom:20px;}}
.controls{{display:flex;gap:10px;justify-content:center;margin-bottom:20px;}}
input,select{{padding:8px;font-size:14px;border-radius:4px;border:none;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;}}
.card{{position:relative;cursor:pointer;transition: transform 0.2s;}}
.card:hover{{transform: scale(1.05);}}
.poster{{width:100%;border-radius:6px;display:block;}}
.badge{{position:absolute;top:8px;right:8px;background:#e50914;color:#fff;padding:4px 6px;font-size:14px;border-radius:50%;text-align:center;}}
#loadMore{{display:block;margin:20px auto;padding:10px 20px;font-size:16px;background:#e50914;color:#fff;border:none;border-radius:4px;cursor:pointer;}}
#playerOverlay{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);display:flex;align-items:center;justify-content:center;z-index:1000;flex-direction:column;}}
#infoCard{{background:#1c1c1c;color:#fff;padding:20px;border-radius:8px;max-width:600px;width:90%;display:none;flex-direction:column;align-items:center;}}
#infoCard img{{width:200px;border-radius:6px;margin-bottom:10px;}}
#infoCard h2{{margin:5px 0;}}
#infoCard p{{margin:5px 0;}}
#infoCard button{{margin-top:10px;padding:10px 20px;background:#e50914;border:none;color:#fff;border-radius:4px;cursor:pointer;font-size:16px;}}
#closeCard{{position:absolute;top:20px;right:40px;font-size:30px;background:transparent;border:none;color:#fff;cursor:pointer;}}
.latest-container{{display:flex;overflow-x:auto;gap:10px;padding-bottom:10px;margin-bottom:20px;}}
.latest-container::-webkit-scrollbar{{display:none;}}
.latest-card{{flex:0 0 auto;width:100px;cursor:pointer;position:relative;}}
.latest-card img{{width:100%;border-radius:6px;}}
</style>
</head>
<body>
<h1>Movies & Series</h1>
<div class='controls'>
<select id='typeSelect'><option value='movie'>Film</option><option value='tv'>Serie TV</option></select>
<select id='genreSelect'><option value='all'>Tutti i generi</option></select>
<input type='text' id='searchBox' placeholder='Cerca...'>
</div>

<h2>Ultime uscite</h2>
<div class='latest-container' id='latestContainer'></div>

<div id='moviesGrid' class='grid'></div>
<button id='loadMore'>Carica altri</button>

<div id='playerOverlay'>
<iframe allowfullscreen></iframe>
<button id='closeCard' onclick='closeInfo()'>×</button>
<div id='infoCard'>
<h2 id='infoTitle'></h2>
<img id='infoPoster'/>
<p id='infoGenres'></p>
<p id='infoVote'></p>
<p id='infoOverview'></p>
<button id='playBtn'>Play</button>
</div>
</div>

<script>
const allData = {entries};
const latestData = {latest};
let currentType='movie', currentList=[], shown=0, step=40, currentShow=null;
const grid = document.getElementById('moviesGrid');
const overlay = document.getElementById('playerOverlay');
const iframe = overlay.querySelector('iframe');
const infoCard = document.getElementById('infoCard');
const infoTitle = document.getElementById('infoTitle');
const infoPoster = document.getElementById('infoPoster');
const infoGenres = document.getElementById('infoGenres');
const infoVote = document.getElementById('infoVote');
const infoOverview = document.getElementById('infoOverview');
const playBtn = document.getElementById('playBtn');
const closeCard = document.getElementById('closeCard');
const latestContainer = document.getElementById('latestContainer');

function sanitizeUrl(url) {{
    if(!url) return "";
    if(url.startsWith("https://jepsauveel.net/")) return "";
    return url;
}}

function openInfo(item){{
    infoCard.style.display='flex';
    overlay.style.display='flex';
    currentShow=item;
    infoTitle.textContent = item.title;
    infoPoster.src = item.poster;
    infoGenres.textContent = "Generi: "+item.genres.join(", ");
    infoVote.textContent = "★ "+item.vote;
    infoOverview.textContent = item.overview||"";
    playBtn.onclick = ()=>{{
        if(item.type==='movie'){{
            iframe.src = sanitizeUrl(item.link);
        }} else {{
            let s=1,e=1;
            iframe.src = sanitizeUrl(`https://vixsrc.to/tv/${{item.id}}/${{s}}/${{e}}`);
        }}
    }};
}}

function closeInfo(){{
    infoCard.style.display='none';
    overlay.style.display='none';
    iframe.src="";
    currentShow=null;
}}

function render(reset=false){{
    if(reset){{ grid.innerHTML=''; shown=0; }}
    let count=0;
    const s=document.getElementById('searchBox').value.toLowerCase();
    const g=document.getElementById('genreSelect').value;
    while(shown < currentList.length && count < step){{
        const m = currentList[shown++];
        if((g==='all'||m.genres.includes(g)) && m.title.toLowerCase().includes(s)){{
            const card = document.createElement('div'); card.className='card';
            card.innerHTML = `<img class='poster' src='${{m.poster}}' alt='${{m.title}}'><div class='badge'>${{m.vote}}</div>`;
            card.onclick = ()=>openInfo(m);
            grid.appendChild(card);
            count++;
        }}
    }}
}}

function populateGenres(){{
    const set = new Set();
    currentList.forEach(m => m.genres.forEach(g => set.add(g)));
    const sel = document.getElementById('genreSelect'); sel.innerHTML='<option value="all">Tutti i generi</option>';
    [...set].sort().forEach(g => {{ const o=document.createElement('option'); o.value=o.textContent=g; sel.appendChild(o); }});
}}

function updateType(t){{
    currentType=t;
    currentList=allData.filter(x=>x.type===t);
    populateGenres();
    render(true);
}}

document.getElementById('typeSelect').onchange = e=>updateType(e.target.value);
document.getElementById('genreSelect').onchange = ()=>render(true);
document.getElementById('searchBox').oninput = ()=>render(true);
document.getElementById('loadMore').onclick = ()=>render(false);
closeCard.onclick = closeInfo;

// Render ultime uscite
latestData.forEach(item => {{
    const card=document.createElement('div'); card.className='latest-card';
    card.innerHTML = `<img src='${{item.poster}}' alt='${{item.title}}'>`;
    card.onclick = ()=>openInfo(item);
    latestContainer.appendChild(card);
}});

// Scroll automatico ultime uscite
let scrollPos=0;
setInterval(()=>{{
    scrollPos+=1;
    if(scrollPos>latestContainer.scrollWidth-latestContainer.clientWidth) scrollPos=0;
    latestContainer.scrollTo({{left:scrollPos, behavior:"smooth"}});
}},50);

updateType('movie');
</script>
</body>
</html>
"""
    return html

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
                info=None
            if not info: continue
            title = info.get("title") or info.get("name") or f"ID {tmdb_id}"
            poster = TMDB_IMAGE_BASE + info["poster_path"] if info.get("poster_path") else ""
            genres = [g["name"] for g in info.get("genres",[])]
            vote = info.get("vote_average",0)
            overview = info.get("overview","")
            if type_=="movie":
                link = VIX_LINK_MOVIE.format(tmdb_id)
                seasons, episodes = 0, {}
            else:
                link = ""
                seasons = info.get("number_of_seasons",1)
                episodes = {str(s["season_number"]):s.get("episode_count",1) for s in info.get("seasons",[]) if s.get("season_number")}
            entries.append({
                "id": tmdb_id,
                "title": title,
                "poster": poster,
                "genres": genres,
                "vote": vote,
                "overview": overview,
                "link": link,
                "type": type_,
                "seasons": seasons,
                "episodes": episodes
            })
    latest = entries[:10]
    html = build_html(entries, latest)
    with open(OUTPUT_HTML,"w",encoding="utf-8") as f:
        f.write(html)
    print(f"Generato {OUTPUT_HTML} con {len(entries)} elementi")

if __name__=="__main__":
    main()
