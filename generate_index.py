import requests, os, sys

OUTPUT_HTML = "index.html"

Funzione per scaricare lista da Vix

def fetch_list(url): print(f"Scarico lista da: {url}") r = requests.get(url, timeout=30) r.raise_for_status() data = r.json() if isinstance(data, dict) and "result" in data: return data["result"] elif isinstance(data, list): return data else: return []

Funzione HTML builder

def build_html(entries, latest_entries): return f"""<!DOCTYPE html>

<html lang='it'>
<head>
<meta charset='UTF-8'>
<title>Catalogo Vix+TMDB</title>
<style>
 body {{ margin:0; font-family:sans-serif; background:#111; color:#fff; }}
 #homePage {{ padding:10px; }}
 .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(140px,1fr)); gap:10px; }}
 .card {{ background:#222; border-radius:8px; overflow:hidden; cursor:pointer; }}
 .card img {{ width:100%; display:block; }}
 .card .title {{ padding:5px; font-size:14px; text-align:center; }}
 #detailsPage {{ display:none; padding:20px; }}
 #detailsPage img {{ width:200px; float:left; margin-right:20px; }}
 #detailsPage h2 {{ margin-top:0; }}
 .actions button {{ margin:5px; padding:10px; border:none; border-radius:6px; cursor:pointer; }}
 #latest {{ white-space:nowrap; overflow-x:auto; padding:10px; background:#000; }}
 #latest .card {{ display:inline-block; width:120px; vertical-align:top; }}
</style>
</head>
<body>
 <div id='latest'>{latest_entries}</div>
 <div id='homePage'>
   <h1>Catalogo</h1>
   <div id='grid' class='grid'></div>
 </div>
 <div id='detailsPage'>
   <button onclick='backToHome()'>⟵ Indietro</button>
   <div id='detailContent'></div>
 </div>
<script>
const grid=document.getElementById('grid');
const latest=document.getElementById('latest');
const homePage=document.getElementById('homePage');
const detailsPage=document.getElementById('detailsPage');
const detailContent=document.getElementById('detailContent');let allItems={entries};

function renderGrid(items){{ grid.innerHTML=''; items.forEach(item=>{{ const div=document.createElement('div'); div.className='card'; div.innerHTML=<img src="${{item.poster}}" alt="${{item.title}}"><div class='title'>${{item.title}}</div>; div.onclick=()=>openDetails(item); grid.appendChild(div); }}); }}

function openDetails(item){{ homePage.style.display='none'; detailsPage.style.display='block'; detailContent.innerHTML= <img src="${{item.poster}}" alt="${{item.title}}"> <h2>${{item.title}}</h2> <p>${{item.overview||''}}</p> <div class='actions'> <button onclick='openPlayer(${{JSON.stringify(item).replace(/"/g,'&quot;')}})'>▶ Guarda</button> </div>; history.pushState({{page:"detail"}}, "", "?id="+item.id); }}

function backToHome(){{ detailsPage.style.display='none'; homePage.style.display='block'; history.pushState({{page:"home"}}, "", ""); }}

window.addEventListener("popstate",e=>{{ if(!e.state||e.state.page!=="detail") backToHome(); }});

function openPlayer(item){{ let link; if(item.type==='tv'){{ link=https://vixsrc.to/tv/${{item.id}}/1/1?lang=it&sottotitoli=off&autoplay=1; }} else {{ link=https://vixsrc.to/movie/${{item.id}}/?lang=it&sottotitoli=off&autoplay=1; }} window.open(link,'_blank'); }}

renderGrid(allItems); </script>

</body></html>"""def main(): entries=[] urls=[ "https://vixsrc.to/api/list/movie?lang=it", "https://vixsrc.to/api/list/tv?lang=it" ]

for url in urls:
    items=fetch_list(url)
    for it in items:
        entries.append({
            "id": it.get("id"),
            "title": it.get("title"),
            "poster": it.get("poster"),
            "overview": it.get("overview",""),
            "type": "movie" if "movie" in url else "tv"
        })
    print(f"Aggiunti {len(items)} elementi da {url}")

latest_entries=''.join([
    f"<div class='card'><img src='{e['poster']}' alt='{e['title']}'></div>"
    for e in entries[:10]
])

html=build_html(entries, latest_entries)
with open(OUTPUT_HTML,"w",encoding="utf-8") as f:
    f.write(html)
print(f"Generato {OUTPUT_HTML} con {len(entries)} elementi.")

if name=="main": main()
