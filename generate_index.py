import requests
import json
import os

OUTPUT_FILE = "index.html"
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "INSERISCI_LA_TUA_API_KEY")

def fetch_tmdb_info(tmdb_id, type_="movie"):
    url = f"https://api.themoviedb.org/3/{type_}/{tmdb_id}"
    params = {"api_key": TMDB_API_KEY, "language": "it-IT", "append_to_response": "credits"}
    r = requests.get(url, params=params)
    if r.status_code == 200:
        return r.json()
    return {}

def generate_html(entries):
    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Movies & Series</title>
  <style>
    body {{ background:#111; color:#fff; font-family:Arial,sans-serif; margin:0; padding:0; }}
    h1 {{ text-align:center; padding:20px; }}
    .controls {{ display:flex; gap:10px; justify-content:center; margin-bottom:20px; }}
    select, input {{ padding:10px; border-radius:5px; border:none; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:15px; padding:15px; }}
    .card {{ background:#222; border-radius:10px; overflow:hidden; cursor:pointer; transition:transform 0.2s; position:relative; }}
    .card:hover {{ transform:scale(1.05); }}
    .card img {{ width:100%; display:block; }}
    .fav-btn {{ position:absolute; top:8px; right:8px; background:none; border:none; font-size:22px; cursor:pointer; color:#fff; }}
    .fav-btn.active {{ color:gold; }}
    #playerOverlay {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.9); z-index:1000; align-items:center; justify-content:center; }}
    #playerOverlay iframe {{ width:90%; height:80%; border:none; }}
    #infoCard {{ display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.85); z-index:999; justify-content:center; align-items:center; color:#fff; }}
    #infoCard h2 {{ margin-top:0; }}
    .btn-play {{ padding:10px 20px; background:#28a745; border:none; border-radius:5px; cursor:pointer; }}
    .btn-close {{ padding:10px 15px; background:#c00; border:none; border-radius:50%; cursor:pointer; font-size:18px; }}
  </style>
</head>
<body>
  <h1>Movies & Series</h1>
  <div class='controls'>
    <select id='typeSelect'><option value='movie'>Film</option><option value='tv'>Serie TV</option><option value='favorites'>Preferiti</option></select>
    <select id='genreSelect'><option value='all'>Tutti i generi</option></select>
    <input type='text' id='searchBox' placeholder='Cerca...'>
  </div>
  <div id='moviesGrid' class='grid'></div>
  <button id='loadMore'>Carica altri</button>

  <div id='playerOverlay'>
    <iframe allow="autoplay; fullscreen; encrypted-media" allowfullscreen></iframe>
  </div>

  <div id='infoCard'>
    <div style="background:#222; border-radius:10px; padding:20px; max-width:800px; width:90%;">
      <h2 id="infoTitle"></h2>
      <div style="display:flex;align-items:center;gap:10px;margin:10px 0;">
        <button id="playBtn" class="btn-play">Play</button>
        <button id="closeCardBtn" class="btn-close">×</button>
        <button id="favBtn" class="fav-btn">★</button>
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
    const allData = {json.dumps(entries)};
    let favorites = JSON.parse(localStorage.getItem("favorites") || "[]");

    function sanitizeUrl(url){{ 
      if(!url) return "";
      return url;
    }}

    function toggleFavorite(id){{ 
      if(favorites.includes(id)) {{
        favorites = favorites.filter(f => f !== id);
      }} else {{
        favorites.push(id);
      }}
      localStorage.setItem("favorites", JSON.stringify(favorites));
      renderGrid();
    }}

    function renderGrid(type="movie"){{ 
      const grid = document.getElementById("moviesGrid");
      grid.innerHTML = "";
      let filtered = [];
      if(type==="favorites") {{
        filtered = allData.filter(m => favorites.includes(m.id));
      }} else {{
        filtered = allData.filter(m => m.type===type);
      }}
      filtered.forEach(m => {{
        const card = document.createElement("div");
        card.className="card";
        card.innerHTML = `
          <img src="https://image.tmdb.org/t/p/w300${{m.poster}}" alt="${{m.title}}">
          <button class="fav-btn ${{favorites.includes(m.id) ? 'active' : ''}}" onclick="event.stopPropagation(); toggleFavorite(${{m.id}})">★</button>
        `;
        card.onclick = () => showInfo(m);
        grid.appendChild(card);
      }});
    }}

    function showInfo(m){{ 
      document.getElementById("infoTitle").innerText = m.title;
      document.getElementById("infoGenres").innerText = "Genere: " + (m.genres || "").toString();
      document.getElementById("infoVote").innerText = "Voto: " + (m.vote || "");
      document.getElementById("infoOverview").innerText = m.overview || "";
      document.getElementById("infoYear").innerText = "Anno: " + (m.year || "");
      document.getElementById("infoDuration").innerText = "Durata: " + (m.duration || "");
      document.getElementById("infoCast").innerText = "Cast: " + (m.cast || []).join(", ");
      document.getElementById("infoCard").style.display = "flex";
      document.getElementById("playBtn").onclick = () => playVideo(m.url);
      document.getElementById("favBtn").onclick = () => toggleFavorite(m.id);
      if(favorites.includes(m.id)) {{
        document.getElementById("favBtn").classList.add("active");
      }} else {{
        document.getElementById("favBtn").classList.remove("active");
      }}
    }}

    function playVideo(url){{ 
      document.querySelector("#playerOverlay iframe").src = sanitizeUrl(url);
      document.getElementById("playerOverlay").style.display="flex";
    }}

    document.getElementById("closeCardBtn").onclick = () => document.getElementById("infoCard").style.display="none";
    document.getElementById("playerOverlay").onclick = () => {{
      document.getElementById("playerOverlay").style.display="none";
      document.querySelector("#playerOverlay iframe").src="";
    }};

    document.getElementById("typeSelect").onchange = (e)=> renderGrid(e.target.value);

    renderGrid();
  </script>
</body>
</html>
"""
    return html

def main():
    entries = []
    sample_data = [
        {"id": 603, "type": "movie"},  # Matrix
        {"id": 1399, "type": "tv"}     # Game of Thrones
    ]

    for item in sample_data:
        tmdb_id = item["id"]
        type_ = item["type"]
        info = fetch_tmdb_info(tmdb_id, type_)
        if not info:
            continue
        title = info.get("title") or info.get("name")
        poster = info.get("poster_path")
        overview = info.get("overview")
        genres = [g["name"] for g in info.get("genres", [])]
        vote = info.get("vote_average")
        year = (info.get("release_date") or info.get("first_air_date") or "")[:4]
        duration = info.get("runtime") if type_=="movie" else None
        cast = [c["name"] for c in info.get("credits", {}).get("cast", [])] if info.get("credits") else []

        entries.append({
            "id": tmdb_id,
            "title": title,
            "poster": poster,
            "overview": overview,
            "genres": genres,
            "vote": vote,
            "year": year,
            "duration": duration,
            "cast": cast,
            "url": f"https://vidsrc.to/embed/{type_}/{tmdb_id}",
            "type": type_
        })

    html = generate_html(entries)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    main()
