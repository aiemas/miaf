import requests

# --- URL API ---
MOVIES_API = "https://vixsrc.to/api/list/movie/?lang=it"
TV_API = "https://vixsrc.to/api/list/tv/?lang=it"

# --- Funzione per generare blocchi HTML ---
def generate_block(item, type_):
    tmdb_id = item.get("tmdb_id")
    if not tmdb_id:
        return ""
    title = item.get("title", "Titolo non trovato")
    url = f"https://vixsrc.to/{type_}/{tmdb_id}/?primaryColor=B20710&autoplay=false&lang=it"
    poster_url = item.get("https://image.tmdb.org/", "/t/p/default_poster.jpg")  # Assicurati di avere un campo per la locandina

    return f"""
<div class="{type_}">
  <a href="{url}" target="_blank">
    <img src="{poster_url}" alt="{title}" style="width:100%; height:auto;">
    <div class="title">{title}</div>
  </a>
</div>
"""

# --- Fetch dati da API ---
def fetch_items(url):
    resp = requests.get(url)
    data = resp.json()
    return data  # <-- restituisce direttamente la lista

movies = fetch_items(MOVIES_API)
tv_series = fetch_items(TV_API)

# --- Genera index.html ---
with open("index.html", "w", encoding="utf-8") as f:
    f.write("""
<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<title>Film e Serie TV dal Database</title>
<style>
body { font-family: Arial; padding: 20px; }
#movies-container { display: flex; flex-wrap: wrap; justify-content: space-between; }
.movie, .tv { margin: 10px; width: calc(48% - 20px); }
.title { font-weight: bold; margin-bottom: 5px; font-size: 18px; }
input { width: 100%; padding: 10px; margin-bottom: 20px; font-size: 16px; }
</style>
</head>
<body>
<h1>Film e Serie TV dal Database</h1>

<input type="text" id="search" placeholder="Cerca per titolo..." onkeyup="filterMovies()">

<div id="movies-container">
""")

    # Blocchi film
    for movie in movies:
        f.write(generate_block(movie, "movie"))
    
    # Blocchi serie TV
    for tv in tv_series:
        f.write(generate_block(tv, "tv"))
    
    # Footer con script di ricerca
    f.write("""
</div>
<script>
// Funzione di filtro per cercare film e serie TV
function filterMovies() {
    const query = document.getElementById('search').value.toLowerCase();
    const movies = document.querySelectorAll('.movie, .tv');

    movies.forEach(movie => {
        const title = movie.querySelector('.title').textContent.toLowerCase();
        movie.style.display = title.includes(query) ? 'block' : 'none';
    });
}
</script>
</body>
</html>
""")
