#!/usr/bin/env python3
"""
generate_index.py migliorato

- Locandine -> pagina dettaglio a schermo intero
- In alto player/trailer (50%), in basso info
- Serie: tendine stagione/episodio
- Player con titolo overlay a scomparsa
- Alla chiusura del player si riapre la scheda info
"""

import os, sys, requests

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
    return ids


def tmdb_get(api_key, type_, tmdb_id, language="it-IT"):
    url = TMDB_BASE.format(type=type_, id=tmdb_id)
    r = requests.get(url, params={"api_key": api_key, "language": language}, timeout=15)
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
.card{{position:relative;cursor:pointer;transition: transform 0.2s;}}
.card:hover{{transform:scale(1.05);}}
.poster{{width:100%;border-radius:8px;display:block;}}
.badge{{position:absolute;bottom:8px;right:8px;background:#e50914;color:#fff;padding:4px 6px;font-size:14px;font-weight:bold;border-radius:50%;text-align:center;}}
#loadMore{{display:block;margin:20px auto;padding:10px 20px;font-size:16px;background:#e50914;color:#fff;border:none;border-radius:4px;cursor:pointer;}}
/* Overlay player */
#playerOverlay{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.95);display:none;align-items:center;justify-content:center;z-index:2000;flex-direction:column;}}
#playerOverlay iframe{{width:80%;height:60%;border:none;}}
#playerOverlay button.closeBtn{{position:absolute;top:10px;right:10px;font-size:24px;background:#e50914;border:none;color:#fff;border-radius:50%;cursor:pointer;padding:0 10px;}}
#playerTitle{{position:absolute;top:10px;left:50%;transform:translateX(-50%);background:rgba(0,0,0,0.6);padding:6px 12px;border-radius:6px;font-size:16px;opacity:0;transition:opacity 1s;color:#fff;}}
/* Pagina info */
#detailPage{{position:fixed;top:0;left:0;width:100%;height:100%;background:#111;display:none;flex-direction:column;z-index:1500;overflow-y:auto;}}
#detailHeader{{height:50%;display:flex;align-items:center;justify-content:center;background:#000;}}
#detailHeader iframe{{width:100%;height:100%;border:none;}}
#detailContent{{padding:20px;}}
#detailContent h2{{margin-top:0;color:#e50914;}}
#detailContent p{{margin:5px 0;}}
#detailClose{{position:absolute;top:10px;right:10px;font-size:24px;background:#e50914;border:none;color:#fff;border-radius:50%;cursor:pointer;padding:0 10px;}}
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

<!-- Player overlay -->
<div id='playerOverlay'>
  <button class="closeBtn" onclick="closePlayer()">×</button>
  <div id="playerTitle"></div>
  <iframe allowfullscreen></iframe>
</div>

<!-- Pagina dettaglio -->
<div id="detailPage">
  <button id="detailClose" onclick="closeDetail()">×</button>
  <div id="detailHeader">
    <iframe id="detailTrailer"></iframe>
  </div>
  <div id="detailContent">
    <h2 id="detailTitle"></h2>
    <p id="detailInfo"></p>
    <p id="detailVote"></p>
    <p id="detailOverview"></p>
    <select id="seasonSelect"></select>
    <select id="episodeSelect"></select>
    <button id="playBtn">Play</button>
  </div>
</div>

<script>
const allData = {entries};

const grid=document.getElementById('moviesGrid');
const overlay=document.getElementById('playerOverlay');
const iframe=overlay.querySelector('iframe');
const playerTitle=document.getElementById('playerTitle');

const detail=document.getElementById('detailPage');
const detailTitle=document.getElementById('detailTitle');
const detailInfo=document.getElementById('detailInfo');
const detailVote=document.getElementById('detailVote');
const detailOverview=document.getElementById('detailOverview');
const detailTrailer=document.getElementById('detailTrailer');
const playBtn=document.getElementById('playBtn');
const seasonSelect=document.getElementById('seasonSelect');
const episodeSelect=document.getElementById('episodeSelect');

let currentItem=null;

function openDetail(item){{
    currentItem=item;
    detail.style.display='flex';
    detailTitle.textContent=item.title;
    detailInfo.textContent=(item.year||"") + (item.duration?" • "+item.duration+" min":"");
    detailVote.textContent="★ " + item.vote;
    detailOverview.textContent=item.overview;
    detailTrailer.src=item.trailer || "";

    seasonSelect.style.display='none';
    episodeSelect.style.display='none';
    if(item.type==='tv'){{
        seasonSelect.style.display='inline';
        episodeSelect.style.display='inline';
        seasonSelect.innerHTML="";
        for(let s=1;s<=item.seasons;s++){{
            let o=document.createElement('option');
            o.value=s; o.textContent="Stagione "+s;
            seasonSelect.appendChild(o);
        }}
        updateEpisodes();
        seasonSelect.onchange=updateEpisodes;
    }}
    playBtn.onclick=()=>openPlayer(item);
}}

function closeDetail(){{
    detail.style.display='none';
    detailTrailer.src="";
    currentItem=null;
}}

function updateEpisodes(){{
    let season=parseInt(seasonSelect.value);
    let epCount=currentItem.episodes[season]||1;
    episodeSelect.innerHTML="";
    for(let e=1;e<=epCount;e++){{
        let o=document.createElement('option');
        o.value=e; o.textContent="Episodio "+e;
        episodeSelect.appendChild(o);
    }}
}}

function openPlayer(item){{
    detail.style.display='none';
    overlay.style.display='flex';
    let link=item.link;
    if(item.type==='tv'){{
        let s=parseInt(seasonSelect.value)||1;
        let e=parseInt(episodeSelect.value)||1;
        link=`https://vixsrc.to/tv/${{item.id}}/${{s}}/${{e}}`;
    }}
    iframe.src=link;
    showTitle(item.title);
}}

function closePlayer(){{
    overlay.style.display='none';
    iframe.src="";
    if(currentItem) detail.style.display='flex'; // riapre scheda info
}}

function showTitle(txt){{
    playerTitle.textContent=txt;
    playerTitle.style.opacity=1;
    setTimeout(()=>playerTitle.style.opacity=0,3000);
}}

let currentType='movie',currentList=[],shown=0;
function render(reset=false){{
    if(reset){{ grid.innerHTML=''; shown=0; }}
    let count=0;
    let s=document.getElementById('searchBox').value.toLowerCase();
    let g=document.getElementById('genreSelect').value;
    while(shown<currentList.length && count<40){{
        let m=currentList[shown++];
        if((g==='all'||m.genres.includes(g)) && m.title.toLowerCase().includes(s)){{
            const card=document.createElement('div');
            card.className='card';
            card.innerHTML=`<img class='poster' src='${{m.poster}}'><div class='badge'>${{m.vote}}</div>`;
            card.onclick=()=>openDetail(m);
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
            seasons = info.get("number_of_seasons",1) if type_=="tv" else 0
            episodes = {str(s["season_number"]): s.get("episode_count",1) for s in info.get("seasons",[]) if s.get("season_number")} if type_=="tv" else {}
            duration = info.get("runtime",0) if type_=="movie" else 0
            year = (info.get("release_date") or info.get("first_air_date") or "")[:4]

            entries.append({{
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
                "trailer": ""  # placeholder, potremmo prendere trailer TMDb
            }})

            if idx < 10:  # ultime novità
                latest_entries += f"<img class='poster' src='{poster}' alt='{title}' title='{title}'>\\n"

    html = build_html(entries, latest_entries)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generato {OUTPUT_HTML} con {len(entries)} elementi e ultime novità scrollabili")


if __name__ == "__main__":
    main()
