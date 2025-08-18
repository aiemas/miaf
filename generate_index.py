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
    url = f"https://vixsrc.to/{type_}/{tmdb_id}?primaryColor=B20710&autoplay=false&lang=it"
    return f"""
<div class="movie">
  <div class="title">{title}</div>
  <iframe src="{url}" allowfullscreen></iframe>
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
.movie { margin-bottom: 30px; }
.title { font-weight: bold; margin-bottom: 5px; font-size: 18px; }
iframe { width: 50%; height: 250px; border: none; }
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
function filterMovies() {
    var input = document.getElementById('search');
    var filter = input.value.toLowerCase();
    var movies = document.getElementById('movies-container').getElementsByClassName('movie');
    for (var i = 0; i < movies.length; i++) {
        var title = movies[i].getElementsByClassName('title')[0].innerText.toLowerCase();
        movies[i].style.display = title.includes(filter) ? '' : 'none';
    }
}
</script>

</body>
</html>
""")

print("index.html generato con successo!")
