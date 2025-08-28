#!/usr/bin/env python3
"""
generate_index.py

Genera una pagina HTML con locandine da TMDb partendo dalla lista di Vix.
- Film e Serie TV (due tendine: Movies / Series)
- Ultime novità in alto (primi 10 della lista Vix)
- Ricerca per titolo
- Filtro per genere
- Clic su locandina apre scheda info con play
- Lazy load: mostra 40 titoli per volta
- Serie: tendine per stagione ed episodio
- Scroll automatico ultime novità
- Card fullscreen con sfondo locandina in trasparenza
- Play nasconde la card temporaneamente
- Card uniformi con colori più gradevoli
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
    return ids

def tmdb_get(api_key, type_, tmdb_id, language="it-IT"):
    url = TMDB_BASE.format(type=type_, id=tmdb_id)
    r = requests.get(url, params={"api_key": api_key, "language": language, "append_to_response": "credits"}, timeout=15)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return r.json()

def build_html(entries, latest_entries):
    html = f"""<!doctype html>
<html lang='it'>
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Movies & Series</title>
<style>
body{{font-family:Arial,sans-serif;background:#141414;color:#fff;margin:0;padding:20px;}}
h1{{color:#fff;text-align:center;margin-bottom:20px;}}
.controls{{display:flex;gap:10px;justify-content:center;margin-bottom:20px;}}
input,select{{padding:8px;font-size:14px;border-radius:4px;border:none;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;}}
.card{{position:relative;cursor:pointer;transition: transform 0.2s;border-radius:12px;overflow:hidden;border:2px solid #444;background:#1f1f1f;}}
.card:hover{{transform:scale(1.05);border-color:#e50914;background:#2a2a2a;}}
.poster{{width:100%;border-radius:0;display:block;}}
.badge{{position:absolute;top:8px;right:8px;background:#e50914;color:#fff;padding:4px 6px;font-size:14px;font-weight:bold;border-radius:8px;text-align:center;}}
#loadMore{{display:block;margin:20px auto;padding:10px 20px;font-size:16px;background:#e50914;color:#fff;border:none;border-radius:8px;cursor:pointer;}}
#playerOverlay{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);display:none;align-items:center;justify-content:center;z-index:1000;flex-direction:column;}}
#playerOverlay iframe{{width:100%;height:100%;border:none;}}
#infoCard{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(34,34,34,0.85);display:none;z-index:1001;backdrop-filter:blur(8px);color:#fff;padding:20px;overflow:auto;}}
#infoCard h2{{margin-top:0;color:#e50914;display:inline-block;}}
#infoCard button#playBtn{{margin-left:10px;padding:8px 12px;background:#e50914;border:none;color:#fff;border-radius:5px;cursor:pointer;vertical-align:middle;}}
#infoCard p{{margin:5px 0;}}
#infoCard select{{margin:5px 5px 5px 0;padding:6px;}}
#latest{{display:flex;overflow-x:auto;gap:10px;margin-bottom:20px;padding-bottom:10px;scroll-behavior: smooth;}}
#latest::-webkit-scrollbar {{display: none;}}
#latest {{-ms-overflow-style: none;scrollbar-width: none;}}
#latest .poster{{width:100px;flex-shrink:0;}}
.btn-play {{
  padding: 5px 10px;
  background: orange;
  color: #fff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}}
.btn-close {{
  padding: 5px 10px;
  background: #e50914;
  color: #fff;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}}
</style>
</head>
<body>
<h1>Ultime Novità</h1>
<div id='latest'>
{latest_entries}
</div>

<h1>Movies & Series</h1>
<div class='controls'>
<select id='typeSelect'><option value='movie'>Film</option><option value='tv'>Serie TV</option></select>
<select id='genreSelect'><option value='all'>Tutti i generi</option></select>
<input type='text' id='searchBox' placeholder='Cerca...'>
</div>
<div id='moviesGrid' class='grid'></div>
<button id='loadMore'>Carica altri</button>

<div id='playerOverlay'>
  <iframe allow="autoplay; fullscreen; encrypted-media" allowfullscreen></iframe>
</div>

<div id='infoCard'>
  <div style="position:relative;background:#222;border-radius:10px;padding:20px;max-width:800px;width:90%;">
    <h2 id="infoTitle"></h2>
    <div style="display:flex;align-items:center;gap:10px;margin:10px 0;">
      <button id="playBtn" class="btn-play">Play</button>
      <button id="closeCardBtn" class="btn-close">×</button>
    </div>
    <p id="infoGenres"></p>
    <p id="infoVote"></p>
    <p id="infoOverview"></p>
    <p id="infoYear"></p>
    <p id="infoDuration"></p>
    <p id="infoCast"></p>
    <select id="seasonSelect"></select>
    <select id="episodeSelect"></select>
  </div>
</div>

<script>
const allData = {entries};
const grid=document.getElementById('moviesGrid');
const overlay=document.getElementById('playerOverlay');
const iframe=overlay.querySelector('iframe');
const infoCard = document.getElementById('infoCard');
const infoTitle = document.getElementById('infoTitle');
const infoGenres = document.getElementById('infoGenres');
const infoVote = document.getElementById('infoVote');
const infoOverview = document.getElementById('infoOverview');
const playBtn = document.getElementById('playBtn');
const closeCardBtn = document.getElementById('closeCardBtn');
const latestDiv = document.getElementById('latest');
closeCardBtn.onclick = () => infoCard.style.display = 'none';
const seasonSelect = document.getElementById('seasonSelect');
const episodeSelect = document.getElementById('episodeSelect');
const infoYear = document.getElementById('infoYear');
const infoDuration = document.getElementById('infoDuration');
const infoCast = document.getElementById('infoCast');

function sanitizeUrl(url){{ 
   if(!url) return "";
    return url;
}}

function showLatest(){{ 
    let scrollPos = 0;
    function scroll() {{
        scrollPos += 1;
        if(scrollPos > latestDiv.scrollWidth - latestDiv.clientWidth) scrollPos = 0;
        latestDiv.scrollTo({{left: scrollPos, behavior: 'smooth'}});
    }}
    setInterval(scroll, 30);
}}

function openInfo(item){{ 
    infoCard.style.display='block';
    infoCard.style.backgroundImage = "none";
    infoCard.style.backgroundColor = "rgba(0,0,0,0.85)";
    infoTitle.textContent = item.title;
    infoGenres.textContent = "Generi: " + item.genres.join(", ");
    infoVote.textContent = "★ " + item.vote;
    infoOverview.textContent = item.overview || "";
    infoYear.textContent = item.year ? "Anno: " + item.year : "";
    infoDuration.textContent = item.duration ? "Durata: " + item.duration + " min" : "";
    infoCast.textContent = item.cast && item.cast.length ? "Cast: " + item.cast.slice(0,5).join(", ") : "";

    seasonSelect.style.display = 'none';
    episodeSelect.style.display = 'none';
    
    if(item.type==='tv'){{ 
        seasonSelect.style.display = 'inline';
        episodeSelect.style.display = 'inline';
        seasonSelect.innerHTML = "";
        for(let s=1;s<=item.seasons;s++){{ 
            let o = document.createElement('option');
            o.value = s;
            o.textContent = "Stagione " + s;
            seasonSelect.appendChild(o);
        }}
        seasonSelect.onchange = updateEpisodes;
        updateEpisodes();
    }}

    playBtn.onclick = ()=>openPlayer(item);

    function updateEpisodes(){{ 
        let season = parseInt(seasonSelect.value);
        let epCount = item.episodes[season] || 1;
        episodeSelect.innerHTML = "";
        for(let e=1;e<=epCount;e++){{ 
            let o = document.createElement('option');
            o.value = e;
            o.textContent = "Episodio " + e;
            episodeSelect.appendChild(o);
        }}
    }}
}}

function closeInfo(){{ 
    infoCard.style.display='none';
}}

function openPlayer(item){{ 
    infoCard.style.display = 'none';
    overlay.style.display='flex';
    let link = sanitizeUrl(item.link);
    if(item.type==='tv'){{ 
        let season = parseInt(seasonSelect.value) || 1;
        let episode = parseInt(episodeSelect.value) || 1;
        link = `https://vixsrc.to/tv/${{item.id}}/${{season}}/${{episode}}?lang=it&sottotitoli=off&autoplay=1`;
    }} else {{
        link = `https://vixsrc.to/movie/${{item.id}}/?lang=it&sottotitoli=off&autoplay=1`;
    }}
    iframe.src = link;

    if (overlay.requestFullscreen) {{
        overlay.requestFullscreen();
    }} else if (overlay.webkitRequestFullscreen) {{
        overlay.webkitRequestFullscreen();
    }} else if (overlay.msRequestFullscreen) {{
        overlay.msRequestFullscreen();
    }}

    overlay.dataset.prevCardVisible = 'true';
    try {{ history.pushState({{playerOpen:true}}, ""); }} catch(e) {{}}
}}

function closePlayer(fromPop) {{
    overlay.style.display='none';
    iframe.src='';

    if (document.fullscreenElement) {{
        document.exitFullscreen();
    }} else if (document.webkitFullscreenElement) {{
        document.webkitExitFullscreen();
    }} else if (document.msFullscreenElement) {{
        document.msExitFullscreen();
    }}

    if(overlay.dataset.prevCardVisible === 'true') {{
        infoCard.style.display = 'block';
    }}

    if (!fromPop && history.state && history.state.playerOpen) {{
        try {{ history.back(); }} catch(e) {{}}
    }}
}}

window.addEventListener("popstate", function(e){{ 
    if (overlay.style.display === 'flex') {{
        closePlayer(true);
    }}
}});

let currentType='movie', currentList=[], shown=0;
function render(reset=false){{ 
    if(reset){{ grid.innerHTML=''; shown=0; }}
    let count=0;
    let s = document.getElementById('searchBox').value.toLowerCase();
    let g = document.getElementById('genreSelect').value;
    while(shown<currentList.length && count<40){{ 
        let m = currentList[shown++];
        if((g==='all' || m.genres.includes(g)) && m.title.toLowerCase().includes(s)){{ 
            const card = document.createElement('div'); 
            card.className='card';
            card.innerHTML = `
                <img class='poster' src='${{m.poster}}' alt='${{m.title}}'>
                <div class='badge'>${{m.vote}}</div>
                <p style="margin:2px 0;font-size:12px;color:#ccc;">
                    ${{m.duration ? m.duration + ' min • ' : ''}}${{m.year ? m.year : ''}}
                </p>
            `;
            card.onclick = () => openInfo(m);
            grid.appendChild(card);
            count++;
        }}
    }}
}}

function populateGenres(){{ 
    const set=new Set();
    currentList.forEach(m=>m.genres.forEach(g=>set.add(g)));
    const sel=document.getElementById('genreSelect'); sel.innerHTML='<option value="all">Tutti i generi</option>';
    [...set].sort().forEach(g=>{{ const o=document.createElement('option'); o.value=o.textContent=g; sel.appendChild(o); }});
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

updateType('movie');
showLatest();
</script>
</body>
</html>
"""
    return html

def main():
    api_key = get_api_key()
    entries = []
    latest_entries = ""

    for type_, url in SRC_URLS.items():
        data = fetch_list(url)
        ids = extract_ids(data)

        for idx, tmdb_id in enumerate(ids):
            try:
                info = tmdb_get(api_key, type_, tmdb_id)
            except:
                info = None
            if not info:
                continue

            title = info.get("title") or info.get("name") or f"ID {tmdb_id}"
            poster = TMDB_IMAGE_BASE + info["poster_path"] if info.get("poster_path") else ""
            genres = [g["name"] for g in info.get("genres", [])]
            vote = info.get("vote_average", 0)
            overview = info.get("overview", "")
            link = VIX_LINK_MOVIE.format(tmdb_id) if type_=="movie" else ""
            seasons = info.get("number_of_seasons", 1) if type_=="tv" else 0
            episodes = {str(s["season_number"]): s.get("episode_count", 1) for s in info.get("seasons", []) if s.get("season_number")} if type_=="tv" else {}
            duration = info.get("runtime", 0) if type_=="movie" else 0
            year = (info.get("release_date") or info.get("first_air_date") or "")[:4]
            cast = [c["name"] for c in info.get("credits", {}).get("cast", [])] if info.get("credits") else []

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
                "episodes": episodes,
                "duration": duration or 0,
                "year": year or "",
                "cast": cast
            })

            if idx < 10:
                latest_entries += f"<img class='poster' src='{poster}' alt='{title}' title='{title}'>\n"

    html = build_html(entries, latest_entries)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generato {OUTPUT_HTML} con {len(entries)} elementi e ultime novità scrollabili")

if __name__ == "__main__":
    main()
