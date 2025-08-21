#!/usr/bin/env python3
# (Header e import come prima...)

def build_html(entries):
    html = f"""<!doctype html>
<html lang="it">
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width,initial-scale=1'>
  <title>Movies & Series</title>
  <style>
    body{{...}}
    h1{{...}}
    .controls{{...}}
    input,select{{...}}
    .grid{{display:grid; grid-template-columns:repeat(auto-fill,minmax(120px,1fr)); gap:8px;}}
    .card{{position:relative;cursor:pointer;}}
    .poster{{width:100%;border-radius:4px;display:block;}}
    
    /* Badge voto */
    .badge{{
      position:absolute; bottom:6px; left:6px;
      color:#fff;font-weight:bold;padding:4px 8px;font-size:12px;
      border-radius:12px;
      box-shadow:0 0 4px rgba(0,0,0,0.7);
    }}
    .badge.green {{ background:#4caf50; }}
    .badge.orange {{ background:#ff9800; }}
    .badge.red {{ background:#f44336; }}

    /* Overlay info card */
    #infoOverlay{{position:fixed;top:10%;left:50%;transform:translateX(-50%);
      width:80%;max-width:500px;background:#111;color:#fff;padding:16px;border-radius:8px;
      box-shadow:0 4px 12px rgba(0,0,0,0.7);z-index:1001;display:none;}}
    #infoOverlay img{{float:left;width:120px;margin-right:16px;border-radius:4px;}}
    #infoOverlay .title{{font-size:1.2rem;font-weight:bold;}}
    #infoOverlay .genres, #infoOverlay .year{{font-size:0.9rem;margin:4px 0;}}
    #infoOverlay .overview{{clear:both;margin-top:8px;font-size:0.9rem;line-height:1.4;}}
    #infoOverlay button{{margin:8px 4px;padding:8px 12px;font-size:0.9rem;cursor:pointer;border:none;border-radius:4px;}}
    #infoOverlay button.play{{background:#e50914;color:#fff;}}
    #infoOverlay button.close{{background:transparent;color:#fff;border:1px solid #fff;}}

    /* Player overlay piccolo già esistente... */
  </style>
</head>
<body>
  <h1>Movies & Series</h1>
  <!-- controls, grid, playerOverlay come prima -->
  <div id="infoOverlay">
    <img src="" alt="Poster">
    <div class="title"></div>
    <div class="year"></div>
    <div class="genres"></div>
    <div class="overview"></div>
    <span class="badge"></span>
    <div style="margin-top:12px;">
      <button class="play">Play ▶</button>
      <button class="close">Chiudi ×</button>
    </div>
  </div>
<script>
const allData = {entries};
const blockedRoots = ["https://jepsauveel.net/"];
function sanitizeUrl(url) {{
  for(const r of blockedRoots) if(url.startsWith(r)) return "";
  return url;
}}

... // Definizione delle variabili come grid, iframe, etc.

function colorClassByVote(v) {{
  if(v > 7) return "green";
  if(v >= 5) return "orange";
  return "red";
}}

function openPlayer(item) {{
  iframe.src = sanitizeUrl(item.link);
  /* attiva fullscreen */
}}

function openInfo(item) {{
  const overlay = document.getElementById('infoOverlay');
  overlay.querySelector('img').src = item.poster;
  overlay.querySelector('.title').textContent = item.title;
  // anno e generi
  overlay.querySelector('.badge').textContent = item.vote;
  overlay.querySelector('.badge').className = 'badge ' + colorClassByVote(item.vote);
  overlay.style.display = 'block';
  overlay.querySelector('.play').onclick = () => {{
    overlay.style.display = 'none';
    openPlayer(item);
  }};
}}

function renderCard(item) {{
  const card = document.createElement('div'); card.className='card';
  card.innerHTML = `<img class="poster" src="${{item.poster}}" alt="${{item.title}}"><span class="badge ${{colorClassByVote(item.vote)}}">${{item.vote}}</span>`;
  card.onclick = () => openInfo(item);
  grid.appendChild(card);
}}

... // render loop, populateGenres, etc., utilizzato renderCard invece di logica vestigia.

</script>
</body>
</html>"""
    return html
