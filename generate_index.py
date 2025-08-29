#!/usr/bin/env python3
"""
generate_index.py
"""

import os
import requests
import json

# =========================
# CONFIG
# =========================
OUTPUT_HTML = "index.html"
HIST_FILE = "all_titles.json"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# Sorgenti Vix
SRC_URLS = {
    "movie": "https://vixcloud.co/filmlist.json",
    "tv": "https://vixcloud.co/serieslist.json"
}

# Vix link templates
VIX_LINK_MOVIE = "https://vixsrc.to/movie/{}"
VIX_LINK_TV = "https://vixsrc.to/tv/{}"

# =========================
# FUNZIONI
# =========================
def get_api_key():
    return os.environ.get("TMDB_API_KEY")

def fetch_list(url):
    try:
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Errore fetch list:", e)
        return []

def extract_ids(data):
    if isinstance(data, list):
        return [str(x) for x in data]
    return []

def tmdb_get(api_key, type_, tmdb_id):
    try:
        url = f"https://api.themoviedb.org/3/{'movie' if type_=='movie' else 'tv'}/{tmdb_id}"
        params = {"api_key": api_key, "language": "it-IT", "append_to_response": "credits"}
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Errore TMDB:", e)
        return None

def build_html(entries, latest_entries):
    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>Film & Serie</title>
<style>
body {{ margin:0;background:#000;color:#fff;font-family:Arial,sans-serif; }}
#controls {{ position:fixed;top:0;width:100%;background:#111;padding:5px;z-index:1000; }}
#grid {{ display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:8px;padding:60px 8px 8px 8px; }}
.card {{ position:relative;cursor:pointer; }}
.poster {{ width:100%;border-radius:8px; }}
.badge {{ position:absolute;top:5px;left:5px;background:red;color:#fff;font-size:12px;padding:2px 4px;border-radius:4px; }}
#infoCard {{ display:none;position:fixed;top:10%;left:5%;width:90%;height:80%;background:#222;padding:10px;overflow:auto;z-index:2000;border-radius:10px; }}
#overlay {{ display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:#000;z-index:3000;flex-direction:column; }}
#overlay iframe {{ flex:1;width:100%;border:none; }}
.favorite-btn {{ position:absolute;top:5px;right:5px;font-size:18px;cursor:pointer;color:#ccc; }}
.favorite-btn.active {{ color:gold; }}
#latestBar {{ display:flex;overflow-x:auto;gap:8px;padding:8px;background:#111; }}
#latestBar img {{ height:80px;border-radius:6px;cursor:pointer; }}
</style>
</head>
<body>
<div id="controls">
<select id="typeSelect">
<option value="movie">Film</option>
<option value="tv">Serie</option>
</select>
<select id="genreSelect" multiple size="1"></select>
<input type="text" id="searchBox" placeholder="Cerca...">
<button id="loadMore">Carica altri</button>
</div>

<div id="latestBar">{latest_entries}</div>

<div id="grid"></div>

<div id="infoCard"></div>

<div id="overlay"><iframe id="iframe" allowfullscreen></iframe></div>

<script>
let allData = {json.dumps(entries)};
let favorites = JSON.parse(localStorage.getItem('favorites')||"[]");
const grid=document.getElementById('grid');
const infoCard=document.getElementById('infoCard');
const overlay=document.getElementById('overlay');
const iframe=document.getElementById('iframe');
let seasonSelect, episodeSelect;
let currentItem=null;

function toggleFavorite(id){{
    if(favorites.includes(id)) favorites=favorites.filter(x=>x!==id);
    else favorites.push(id);
    localStorage.setItem('favorites',JSON.stringify(favorites));
    render(true);
}}

function showLatest(){{
    document.querySelectorAll('#latestBar img').forEach(img=>{{
        img.onclick=()=>{{
            let id=img.getAttribute('alt');
            let item=allData.find(x=>x.title===id);
            if(item) openInfo(item);
        }}
    }});
}}

function openInfo(item){{
    history.pushState({{page:"info"}},"");
    currentItem=item;
    infoCard.style.display='block';
    infoCard.innerHTML=`
        <h2>${{item.title}}</h2>
        <img src="${{item.poster}}" style="width:150px;float:left;margin-right:10px;">
        <p><b>Voto:</b> ${{item.vote}}</p>
        <p><b>Anno:</b> ${{item.year}}</p>
        <p><b>Durata:</b> ${{item.duration}} min</p>
        <p><b>Generi:</b> ${{item.genres.join(', ')}}</p>
        <p>${{item.overview}}</p>
        <p><b>Cast:</b> ${{item.cast.join(', ')}}</p>
        <button onclick="openPlayer(currentItem)">Guarda</button>
        <button onclick="closeInfo()">Chiudi</button>
        <span class="favorite-btn ${{favorites.includes(item.id)?'active':''}}" onclick="toggleFavorite(item.id)">★</span>
    `;
    if(item.type==='tv'){{
        seasonSelect=document.createElement('select');
        seasonSelect.onchange=()=>populateEpisodes(item);
        for(let s=1;s<=item.seasons;s++) seasonSelect.innerHTML+=`<option value="${{s}}">Stagione ${{s}}</option>`;
        infoCard.appendChild(seasonSelect);
        episodeSelect=document.createElement('select');
        infoCard.appendChild(episodeSelect);
        populateEpisodes(item);
    }}
}}

function closeInfo(){{
    infoCard.style.display='none';
}}

function populateEpisodes(item){{
    episodeSelect.innerHTML='';
    if(item.episodes && item.episodes[seasonSelect.value]){{
        let epCount=item.episodes[seasonSelect.value];
        for(let e=1;e<=epCount;e++) episodeSelect.innerHTML+=`<option value="${{e}}">Episodio ${{e}}</option>`;
    }}
}}

function openPlayer(item){{
    infoCard.style.display='none';
    overlay.style.display='flex';
    let link=item.link;
    if(item.type==='tv'){{
        let season=parseInt(seasonSelect.value)||1;
        let episode=parseInt(episodeSelect.value)||1;
        link=`https://vixsrc.to/tv/${{item.id}}/${{season}}/${{episode}}?lang=it&sottotitoli=off&autoplay=1`;
    }} else {{
        link=`https://vixsrc.to/movie/${{item.id}}/?lang=it&sottotitoli=off&autoplay=1`;
    }}
    iframe.src=link;
    if(overlay.requestFullscreen) overlay.requestFullscreen();
    else if(overlay.webkitRequestFullscreen) overlay.webkitRequestFullscreen();
    else if(overlay.msRequestFullscreen) overlay.msRequestFullscreen();
}}

function closePlayer(){{
    overlay.style.display='none';
    iframe.src='';
    if(document.fullscreenElement) document.exitFullscreen();
    else if(document.webkitFullscreenElement) document.webkitExitFullscreen();
    else if(document.msFullscreenElement) document.msExitFullscreen();
}}

window.addEventListener("popstate",function(e){{
    if(overlay.style.display==='flex'){{ 
        closePlayer(); 
        return; 
    }}
    if(infoCard.style.display==='block'){{ 
        closeInfo(); 
        return; 
    }}
}});

let currentType='movie', currentList=[], shown=0;

function render(reset=false){{
    if(reset){{ grid.innerHTML=''; shown=0; }}
    let count=0;
    let s=document.getElementById('searchBox').value.toLowerCase();
    let gSel=Array.from(document.getElementById('genreSelect').selectedOptions).map(o=>o.value);
    while(shown<currentList.length && count<40){{
        let m=currentList[shown++];
        let isFav=favorites.includes(m.id);
        let genreMatch=gSel.length===0||gSel.includes('all')||(gSel.includes('favorites')&&isFav)||gSel.every(g=>m.genres.includes(g));
        if(genreMatch && m.title.toLowerCase().includes(s)){{
            const card=document.createElement('div');
            card.className='card';
            card.innerHTML=`
                <img class='poster' src='${{m.poster}}' alt='${{m.title}}'>
                <div class='badge'>${{m.vote}}</div>
                <p style="margin:2px 0;font-size:12px;color:#ccc;">
                    ${{m.duration ? m.duration+' min • ' : ''}}${{m.year ? m.year : ''}}
                </p>
                <span class="favorite-btn ${{isFav?'active':''}}" style="pointer-events:none;">★</span>
            `;
            card.onclick=()=>openInfo(m);
            grid.appendChild(card);
            count++;
        }}
    }}
}}

function populateGenres(){{
    const set=new Set();
    currentList.forEach(m=>m.genres.forEach(g=>set.add(g)));
    const sel=document.getElementById('genreSelect');
    sel.innerHTML='<option value="all">Tutti i generi</option><option value="favorites">★ Preferiti</option>';
    [...set].sort().forEach(g=>sel.innerHTML+=`<option value="${{g}}">${{g}}</option>`);
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
</html>"""
    return html

def main():
    api_key=get_api_key()
    entries=[]
    latest_entries=""

    all_titles = {}
    if os.path.exists(HIST_FILE):
        try:
            with open(HIST_FILE,"r",encoding="utf-8") as f:
                all_titles=json.load(f)
        except:
            all_titles={}

    for type_,url in SRC_URLS.items():
        data=fetch_list(url)
        ids=extract_ids(data)
        for idx,tmdb_id in enumerate(ids):
            info=tmdb_get(api_key,type_,tmdb_id)
            if not info: continue
            title=info.get("title") or info.get("name") or f"ID {tmdb_id}"
            poster=TMDB_IMAGE_BASE+info["poster_path"] if info.get("poster_path") else ""
            genres=[g["name"] for g in info.get("genres",[])]
            vote=info.get("vote_average",0)
            overview=info.get("overview","")
            link=VIX_LINK_MOVIE.format(tmdb_id) if type_=="movie" else ""
            seasons=info.get("number_of_seasons",1) if type_=="tv" else 0
            episodes={{str(s["season_number"]):s.get("episode_count",1) for s in info.get("seasons",[]) if s.get("season_number")}} if type_=="tv" else {{}}
            duration=info.get("runtime",0) if type_=="movie" else 0
            year=(info.get("release_date") or info.get("first_air_date") or "")[:4]
            cast=[c["name"] for c in info.get("credits",{{}}).get("cast",[])] if info.get("credits") else []

            entry={{
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
            }}
            entries.append(entry)
            all_titles[tmdb_id]=entry

            if idx<10:
                latest_entries+=f"<img class='poster' src='{poster}' alt='{title}' title='{title}'>\\n"

    with open(HIST_FILE,"w",encoding="utf-8") as f:
        json.dump(all_titles,f,ensure_ascii=False,indent=2)

    html=build_html(entries,latest_entries)
    with open(OUTPUT_HTML,"w",encoding="utf-8") as f:
        f.write(html)
    print(f"Generato {OUTPUT_HTML} con {len(entries)} elementi. Storico salvato in {HIST_FILE}")

if __name__=="__main__":
    main()
