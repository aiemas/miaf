import requests
import os
import json

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

def fetch_info(tmdb_id, media_type="movie"):
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}?api_key={TMDB_API_KEY}&language=it-IT"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def build_html(entries, latest):
    html = """<!doctype html>
<html lang="it">
<head>
<meta charset='utf-8'>
<meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Movies & Series</title>
<style>
body{margin:0;font-family:Arial;background:#141414;color:#fff;}
header{padding:20px;font-size:24px;font-weight:bold;color:#e50914;}
section{padding:10px;}
#latestRow{display:flex;overflow-x:auto;gap:10px;scroll-behavior:smooth;}
#latestRow::-webkit-scrollbar{display:none;}
.latestCard{flex:0 0 auto;width:120px;}
.latestCard img{width:100%;border-radius:6px;}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:15px;padding:10px;}
.card{cursor:pointer;position:relative;}
.card img{width:100%;border-radius:6px;}
.vote{position:absolute;top:8px;left:8px;background:rgba(0,0,0,0.7);padding:3px 6px;border-radius:50%;font-size:12px;}
#infoCard{display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
background:#222;padding:20px;width:90%;max-width:500px;z-index:1000;border-radius:10px;overflow-y:auto;max-height:80%;}
#infoCard h2{margin-top:0;display:flex;align-items:center;justify-content:space-between;}
#infoCard button{margin-left:10px;}
.closeBtn{position:absolute;top:10px;right:10px;background:red;border:none;color:white;font-size:20px;cursor:pointer;border-radius:50%;}
#playerOverlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:2000;}
#playerOverlay iframe{width:80%;height:80%;position:absolute;top:10%;left:10%;border:none;}
</style>
</head>
<body>
<header>Movies & Series</header>

<section>
  <h2>Ultime uscite</h2>
  <div id="latestRow"></div>
</section>

<section>
  <h2>Tutti i contenuti</h2>
  <div id="moviesGrid" class="grid"></div>
</section>

<div id='infoCard'>
  <button class='closeBtn' onclick='closeInfo()'>×</button>
  <h2>
    <span id='infoTitle'></span>
    <button id='playBtn'>Play</button>
  </h2>
  <p id='infoGenres'></p>
  <p id='infoVote'></p>
  <p id='infoOverview'></p>
  <div id='seasonsContainer' style='margin-top:10px;'></div>
</div>

<div id='playerOverlay'>
  <button class='closeBtn' onclick='closePlayer()'>×</button>
  <iframe allowfullscreen></iframe>
</div>

<script>
const allData = {entries};
const latestData = {latest};

const grid=document.getElementById('moviesGrid');
const latestRow=document.getElementById('latestRow');
const infoCard=document.getElementById('infoCard');
const infoTitle=document.getElementById('infoTitle');
const infoGenres=document.getElementById('infoGenres');
const infoVote=document.getElementById('infoVote');
const infoOverview=document.getElementById('infoOverview');
const playBtn=document.getElementById('playBtn');
const playerOverlay=document.getElementById('playerOverlay');
const playerIframe=playerOverlay.querySelector('iframe');

function renderAll(){
  grid.innerHTML='';
  allData.forEach(item=>{
    const card=document.createElement('div');card.className='card';
    card.innerHTML=`<img src="${item.poster}" alt=""><div class='vote'>★ ${item.vote}</div>`;
    card.onclick=()=>openInfo(item);
    grid.appendChild(card);
  });
}

function renderLatest(){
  latestRow.innerHTML='';
  latestData.forEach(item=>{
    const card=document.createElement('div');card.className='latestCard';
    card.innerHTML=`<img src="${item.poster}" alt="">`;
    card.onclick=()=>openInfo(item);
    latestRow.appendChild(card);
  });
  autoScroll();
}

function autoScroll(){
  setInterval(()=>{
    latestRow.scrollBy({left:150,behavior:'smooth'});
    if(latestRow.scrollLeft+latestRow.clientWidth>=latestRow.scrollWidth){
      latestRow.scrollTo({left:0,behavior:'smooth'});
    }
  },3000);
}

function openInfo(item){
  infoCard.style.display='block';
  infoTitle.textContent=item.title;
  infoGenres.textContent="Generi: "+item.genres.join(", ");
  infoVote.textContent="★ "+item.vote;
  infoOverview.textContent=item.overview||"";

  if(item.type==='movie'){
    playBtn.style.display='inline-block';
    document.getElementById('seasonsContainer').innerHTML='';
    playBtn.onclick=()=>openPlayer(item);
  }else if(item.type==='tv'){
    playBtn.style.display='none';
    let container=document.getElementById('seasonsContainer');
    container.innerHTML='';
    if(item.episodes){
      let seasonSelect=document.createElement('select');
      let episodeSelect=document.createElement('select');
      seasonSelect.onchange=()=>{
        let season=seasonSelect.value;
        fillEpisodes(season,episodeSelect,item);
      };
      episodeSelect.onchange=()=>{
        let season=seasonSelect.value;
        let episode=episodeSelect.value;
        openPlayer(item,season,episode);
      };
      for(let s in item.episodes){
        let opt=document.createElement('option');
        opt.value=s;opt.textContent="Stagione "+s;
        seasonSelect.appendChild(opt);
      }
      container.appendChild(seasonSelect);
      container.appendChild(episodeSelect);
      seasonSelect.value=Object.keys(item.episodes)[0];
      fillEpisodes(seasonSelect.value,episodeSelect,item);
    }
  }
}

function fillEpisodes(season,episodeSelect,item){
  episodeSelect.innerHTML='';
  let count=item.episodes[season]||1;
  for(let e=1;e<=count;e++){
    let opt=document.createElement('option');
    opt.value=e;opt.textContent="Episodio "+e;
    episodeSelect.appendChild(opt);
  }
}

function closeInfo(){infoCard.style.display='none';}
function openPlayer(item,season=null,episode=null){
  let url=item.link;
  if(item.type==='tv'&&season&&episode){
    url=url+`?season=${season}&episode=${episode}`;
  }
  playerIframe.src=url;
  playerOverlay.style.display='block';
}
function closePlayer(){playerOverlay.style.display='none';playerIframe.src='';}

renderAll();
renderLatest();
</script>
</body>
</html>
"""
    return html.replace("{entries}", json.dumps(entries)).replace("{latest}", json.dumps(latest))

def main():
    with open("list.json","r",encoding="utf-8") as f:
        data=json.load(f)

    entries=[]
    latest=[]

    for i,item in enumerate(data):
        info=fetch_info(item["id"],item["type"])
        if not info: continue
        title=info.get("title") or info.get("name")
        poster=f"https://image.tmdb.org/t/p/w200{info.get('poster_path')}" if info.get("poster_path") else ""
        vote=info.get("vote_average",0)
        genres=[g["name"] for g in info.get("genres",[])]
        overview=info.get("overview","")
        link=item.get("link","")

        if item["type"]=="tv":
            episodes={str(s["season_number"]):s.get("episode_count",1) for s in info.get("seasons",[]) if s.get("season_number")}
        else:
            episodes=None

        entry={
            "id":item["id"],
            "type":item["type"],
            "title":title,
            "poster":poster,
            "vote":vote,
            "genres":genres,
            "overview":overview,
            "link":link,
            "episodes":episodes
        }
        entries.append(entry)
        if i<10:
            latest.append(entry)

    html=build_html(entries,latest)
    with open("index.html","w",encoding="utf-8") as f:
        f.write(html)

if __name__=="__main__":
    main()
