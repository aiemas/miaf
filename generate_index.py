import json
import os

def build_html(entries, latest_entries):
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>Film & Serie</title>
<style>
body{{font-family:Arial,sans-serif;background:#141414;color:#fff;margin:0;padding:20px;}}
h1{{color:#fff;text-align:center;margin-bottom:20px;}}
.controls{{display:flex;gap:10px;justify-content:center;margin-bottom:20px;flex-wrap:wrap;}}
input,select{{padding:8px;font-size:14px;border-radius:4px;border:none;}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:12px;}}
.card{{position:relative;cursor:pointer;transition: transform 0.2s;border-radius:8px;overflow:hidden;
      background:#1f1f1f;box-shadow:0 4px 8px rgba(0,0,0,0.5);}}
.card:hover{{transform:scale(1.05);}}
.poster{{width:100%;height:240px;object-fit:cover;display:block;}}
.badge{{position:absolute;top:6px;right:6px;background:#e50914;color:#fff;
        padding:3px 6px;font-size:13px;font-weight:bold;border-radius:6px;}}
#loadMore{{display:block;margin:20px auto;padding:10px 20px;font-size:16px;
          background:#e50914;color:#fff;border:none;border-radius:8px;cursor:pointer;}}
#playerOverlay{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);
               display:none;align-items:center;justify-content:center;z-index:1000;flex-direction:column;}}
#playerOverlay iframe{{width:100%;height:100%;border:none;}}
#infoCard{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(34,34,34,0.9);
          display:none;z-index:1001;backdrop-filter:blur(8px);color:#fff;padding:20px;overflow:auto;}}
#infoCardInner{{position:relative;
      background: linear-gradient(135deg, rgba(34,34,34,0.95), rgba(60,60,60,0.95));
      border-radius: 20px;
      padding: 25px;
      max-width:800px;
      margin:40px auto;
      box-shadow: 0 10px 30px rgba(0,0,0,0.7);
      transition: transform 0.3s ease, background 0.3s ease, opacity 0.3s ease;}}
#infoCard h2{{margin-top:0;color:#ff4c29;}}
.btn-play{{padding:8px 15px;background:#ff4c29;color:#fff;border:none;border-radius:8px;
          cursor:pointer;font-size:14px;transition:transform 0.2s ease,box-shadow 0.2s ease;}}
.btn-play:hover{{transform:translateY(-2px);box-shadow:0 4px 12px rgba(255,76,41,0.6);}}
.btn-close{{padding:8px 15px;background:#e50914;color:#fff;border:none;border-radius:8px;
           cursor:pointer;font-size:16px;font-weight:bold;transition:transform 0.2s ease,box-shadow 0.2s ease;}}
.btn-close:hover{{transform:translateY(-2px);box-shadow:0 4px 12px rgba(229,9,20,0.6);}}
#latest{{display:flex;overflow-x:auto;gap:10px;margin-bottom:20px;padding-bottom:10px;scroll-behavior:smooth;}}
#latest::-webkit-scrollbar {{display:none;}}
#latest .poster{{width:100px;flex-shrink:0;height:auto;}}
</style>
</head>
<body>

<h1>Ultime Novità</h1>
<div id='latest'>
{latest_entries}
</div>

<h1>Movies & Series</h1>
<div class='controls'>
  <select id='typeSelect'>
    <option value='movie'>Film</option>
    <option value='tv'>Serie TV</option>
  </select>
  <select id='genreSelect'>
    <option value='all'>Tutti i generi</option>
  </select>
  <input type='text' id='searchBox' placeholder='Cerca...'>
</div>

<div id='moviesGrid' class='grid'></div>
<button id='loadMore'>Carica altri</button>

<div id='playerOverlay'>
  <iframe allow="autoplay; fullscreen; encrypted-media" allowfullscreen></iframe>
</div>

<div id='infoCard'>
  <div id="infoCardInner">
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
const allData = {{entries}};
const grid=document.getElementById('moviesGrid');
const overlay=document.getElementById('playerOverlay');
const iframe=overlay.querySelector('iframe');
const infoCard=document.getElementById('infoCard');
const playBtn=document.getElementById('playBtn');
const closeCardBtn=document.getElementById('closeCardBtn');

let currentUrl="";
let loaded=0;
const perPage=30;

function sanitizeUrl(url){{
    if(!url) return "";
    if(url.startsWith("https://jepsauveel.net/")) return "";
    return url;
}}

function renderItems(){{
  grid.innerHTML="";
  const type=document.getElementById('typeSelect').value;
  const genre=document.getElementById('genreSelect').value;
  const search=document.getElementById('searchBox').value.toLowerCase();
  let filtered=allData.filter(e=>e.type===type);
  if(genre!=='all') filtered=filtered.filter(e=>e.genre_ids.includes(genre));
  if(search) filtered=filtered.filter(e=>e.title.toLowerCase().includes(search));
  const slice=filtered.slice(0,loaded+perPage);
  slice.forEach(e=>{{
    const div=document.createElement('div');
    div.className='card';
    div.innerHTML=`<img class='poster' src="${{e.poster}}" alt="">
                   <div class='badge'>${{e.vote}}</div>`;
    div.onclick=()=>showInfo(e);
    grid.appendChild(div);
  }});
  loaded+=perPage;
}}

function showInfo(e){{
  document.getElementById('infoTitle').textContent=e.title;
  document.getElementById('infoGenres').textContent="Genere: "+(e.genres||"");
  document.getElementById('infoVote').textContent="Voto: "+(e.vote||"");
  document.getElementById('infoOverview').textContent=e.overview||"";
  document.getElementById('infoYear').textContent="Anno: "+(e.year||"");
  document.getElementById('infoDuration').textContent="Durata: "+(e.duration||"");
  document.getElementById('infoCast').textContent="Cast: "+(e.cast||"");
  currentUrl=sanitizeUrl(e.url);
  infoCard.style.display="block";
}}

playBtn.onclick=()=>{{
  if(currentUrl) {{
    iframe.src=currentUrl;
    overlay.style.display="flex";
    infoCard.style.display="none";
  }}
}};
closeCardBtn.onclick=()=>{{infoCard.style.display="none";}};
overlay.onclick=()=>{{overlay.style.display="none";iframe.src="";}};

document.getElementById('loadMore').onclick=renderItems;
document.getElementById('typeSelect').onchange=()=>{{loaded=0;renderItems();}};
document.getElementById('genreSelect').onchange=()=>{{loaded=0;renderItems();}};
document.getElementById('searchBox').oninput=()=>{{loaded=0;renderItems();}};

renderItems();
</script>

</body>
</html>"""

def main():
    with open("data.json", "r", encoding="utf-8") as f:
        data=json.load(f)

    entries=json.dumps(data, ensure_ascii=False)
    latest_html="".join([f"<img class='poster' src='{e['poster']}' alt=''>" for e in data[:15]])

    html=build_html(entries, latest_html)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

if __name__=="__main__":
    main()
