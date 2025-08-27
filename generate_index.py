#!/usr/bin/env python3
"""
generate_index.py
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
    r = requests.get(
        url,
        params={"api_key": api_key, "language": language, "append_to_response": "credits"},
        timeout=15
    )
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
body{{{{font-family:Arial,sans-serif;background:#141414;color:#fff;margin:0;padding:20px;}}}}
h1{{{{color:#fff;text-align:center;margin-bottom:20px;}}}}
.controls{{{{display:flex;gap:10px;justify-content:center;margin-bottom:20px;}}}}
input,select{{{{padding:8px;font-size:14px;border-radius:4px;border:none;}}}}
.grid{{{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;}}}}
.card{{{{position:relative;cursor:pointer;transition: transform 0.2s;border-radius:12px;overflow:hidden;border:2px solid #444;background:#1f1f1f;}}}}
.card:hover{{{{transform:scale(1.05);border-color:#e50914;background:#2a2a2a;}}}}
.poster{{{{width:100%;border-radius:0;display:block;}}}}
.badge{{{{position:absolute;top:8px;right:8px;background:#e50914;color:#fff;padding:4px 6px;font-size:14px;font-weight:bold;border-radius:8px;text-align:center;}}}}
#loadMore{{{{display:block;margin:20px auto;padding:10px 20px;font-size:16px;background:#e50914;color:#fff;border:none;border-radius:8px;cursor:pointer;}}}}
#playerOverlay{{{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);display:none;align-items:center;justify-content:center;z-index:1000;flex-direction:column;}}}}
#playerOverlay iframe{{{{width:100%;height:100%;border:none;}}}}
#playerOverlay .overlayTitle{{{{position:absolute;top:20px;left:20px;font-size:20px;background:rgba(0,0,0,0.6);padding:6px 12px;border-radius:8px;}}}}
#infoCard{{{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(34,34,34,0.85);display:none;z-index:1001;backdrop-filter:blur(8px);color:#fff;padding:20px;overflow:auto;}}}}
#infoCard h2{{{{margin-top:0;color:#e50914;display:inline-block;}}}}
#infoCard button#playBtn{{{{margin-left:10px;padding:8px 12px;background:#e50914;border:none;color:#fff;border-radius:5px;cursor:pointer;vertical-align:middle;}}}}
#infoCard p{{{{margin:5px 0;}}}}
#infoCard select{{{{margin:5px 5px 5px 0;padding:6px;}}}}
#latest{{{{display:flex;overflow-x:auto;gap:10px;margin-bottom:20px;padding-bottom:10px;scroll-behavior: smooth;}}}}
#latest::-webkit-scrollbar {{{{display: none;}}}}
#latest {{{{-ms-overflow-style: none;scrollbar-width: none;}}}}
#latest .poster{{{{width:100px;flex-shrink:0;}}}}
.btn-play {{{{padding:5px 10px;background:orange;color:#fff;border:none;border-radius:5px;cursor:pointer;font-size:14px;}}}}
.btn-close {{{{padding:5px 10px;background:#e50914;color:#fff;border:none;border-radius:5px;cursor:pointer;font-size:14px;}}}}
#overlayTitle {
  position: absolute;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.6);
  color: #fff;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 16px;
  display: none;
  z-index: 1100;
}
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
  <span id="overlayTitle"></span>
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
const overlayTitle=document.getElementById('overlayTitle');
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
...
</script>
</body>
</html>
"""
    return html
    <script>
const allData = {entries};
const grid=document.getElementById('moviesGrid');
const overlay=document.getElementById('playerOverlay');
const iframe=overlay.querySelector('iframe');
const overlayTitle=document.getElementById('overlayTitle');
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

let currentPage=0;
const perPage=20;
let currentType='movie';
let currentGenre='all';
let currentSearch='';

function renderItems(reset=false){{
  if(reset){{grid.innerHTML='';currentPage=0;}}
  let filtered=allData.filter(item=>
    item.type===currentType &&
    (currentGenre==='all'||(item.genres && item.genres.includes(currentGenre))) &&
    (item.title.toLowerCase().includes(currentSearch.toLowerCase()))
  );
  let slice=filtered.slice(0,(currentPage+1)*perPage);
  grid.innerHTML='';
  slice.forEach(item=>{{
    let div=document.createElement('div');
    div.className='card';
    div.innerHTML=`<img class='poster' src='${{sanitizeUrl(item.poster)}}' alt='poster'>
      <div class='badge'>${{item.vote}}</div>`;
    div.onclick=()=>showInfo(item);
    grid.appendChild(div);
  }});
  currentPage++;
}}

function showInfo(item){{
  infoTitle.textContent=item.title;
  infoGenres.textContent="Genere: "+(item.genres||"N/D");
  infoVote.textContent="Voto: "+(item.vote||"N/D");
  infoOverview.textContent=item.overview||"";
  infoYear.textContent="Anno: "+(item.year||"N/D");
  infoDuration.textContent="Durata: "+(item.duration||"N/D");
  infoCast.textContent="Cast: "+(item.cast||"N/D");
  seasonSelect.innerHTML='';
  episodeSelect.innerHTML='';
  if(item.type==='tv' && item.episodes){{
    for(let season in item.episodes){{
      let opt=document.createElement('option');
      opt.value=season;opt.text="Stagione "+season;
      seasonSelect.appendChild(opt);
    }}
    updateEpisodes(item,seasonSelect.value);
    seasonSelect.onchange=()=>updateEpisodes(item,seasonSelect.value);
  }}
  playBtn.onclick=()=>play(item);
  infoCard.style.display='block';
}}

function updateEpisodes(item,season){{
  episodeSelect.innerHTML='';
  let count=item.episodes[season];
  for(let i=1;i<=count;i++){{
    let opt=document.createElement('option');
    opt.value=i;opt.text="Episodio "+i;
    episodeSelect.appendChild(opt);
  }}
}}

function play(item){{
  infoCard.style.display='none';
  let link=item.type==='movie'?item.link:item.link+"S"+seasonSelect.value+"E"+episodeSelect.value;
  overlayTitle.textContent=item.title;
  iframe.src=link;
  const overlayTitle = document.getElementById("overlayTitle");
overlayTitle.textContent = item.title;
overlayTitle.style.display = "block";

// al tap sul player, toggle titolo
overlay.onclick = (e) => {
  if (e.target.tagName !== "IFRAME") {
    overlayTitle.style.display = 
      overlayTitle.style.display === "none" ? "block" : "none";
  }
};

  overlay.style.display='flex';
}}

overlay.onclick=function(e){{ if(e.target===overlay){{ overlay.style.display='none';iframe.src='';}} }};

document.getElementById('loadMore').onclick=()=>renderItems();
document.getElementById('typeSelect').onchange=function(){{currentType=this.value;renderItems(true);}};
document.getElementById('genreSelect').onchange=function(){{currentGenre=this.value;renderItems(true);}};
document.getElementById('searchBox').oninput=function(){{currentSearch=this.value;renderItems(true);}};

renderItems(true);
</script>
</body>
</html>
def main():
    with open("data.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = []
    for item in data:
        type_ = item.get("type", "movie")
        info = item.get("info", {})
        url = sanitize_url(item.get("url", ""))

        entries.append({
            "title": info.get("title", ""),
            "poster": sanitize_url(info.get("poster", "")),
            "overview": info.get("overview", ""),
            "year": info.get("year", ""),
            "duration": info.get("duration", ""),
            "cast": ", ".join(c.get("name", "") for c in info.get("cast", [])),
            "genres": ", ".join(info.get("genres", [])),
            "vote": info.get("vote", ""),
            "link": url,
            "type": type_,
            "episodes": {str(s.get("stagione")): s.get("episodi", 1) for s in info.get("stagioni", [])} if type_ == "tv" else {}
        })

    html = build_html(entries)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)


if __name__ == "__main__":
    main()
