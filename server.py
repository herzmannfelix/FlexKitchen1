import os, tempfile, shutil, socket, ipaddress, json, secrets
from pathlib import Path
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from openai import OpenAI
import yt_dlp

app=FastAPI(title="KITCHENFLEX Video Recipe API")
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","*").split(","),allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["*"])
class VideoRequest(BaseModel):
    url: HttpUrl

def validate_url(url):
    p=urlparse(url)
    if p.scheme not in ("http","https") or not p.hostname: raise HTTPException(400,"Nur HTTP(S)-Links erlaubt.")
    h=p.hostname.lower()
    allowed=(h=="youtube.com" or h.endswith(".youtube.com") or h=="youtu.be" or h=="tiktok.com" or h.endswith(".tiktok.com") or h=="instagram.com" or h.endswith(".instagram.com") or h=="facebook.com" or h.endswith(".facebook.com") or h=="fb.watch")
    if not allowed: raise HTTPException(400,"Unterstützt werden YouTube, TikTok, Instagram und Facebook.")
    try:
        for item in socket.getaddrinfo(h,None):
            if not ipaddress.ip_address(item[4][0]).is_global: raise HTTPException(400,"Private Netzwerkadressen sind nicht erlaubt.")
    except socket.gaierror: raise HTTPException(400,"Videoplattform nicht erreichbar.")

SCHEMA={"type":"object","additionalProperties":False,"properties":{
"title":{"type":"string"},"category":{"type":"string","enum":["Fleisch","Pasta","Fisch","Vegetarisch","Dessert","Sonstiges"]},"summary":{"type":"string"},"prep_time":{"type":"string"},"cook_time":{"type":"string"},"total_time_minutes":{"type":"integer"},"servings":{"type":"integer"},"difficulty":{"type":"string","enum":["Einfach","Mittel","Anspruchsvoll","Nicht angegeben"]},
"ingredients":{"type":"array","items":{"type":"object","additionalProperties":False,"properties":{"name":{"type":"string"},"amount":{"type":"string"}},"required":["name","amount"]}},
"steps":{"type":"array","items":{"type":"string"}},"notes":{"type":"array","items":{"type":"string"}}},
"required":["title","category","summary","prep_time","cook_time","total_time_minutes","servings","difficulty","ingredients","steps","notes"]}

@app.get("/api/health")
def health(): return {"ok":True,"service":"KITCHENFLEX"}

@app.post("/api/import-video")
def import_video(body:VideoRequest, authorization: str | None = Header(default=None)):
    expected=os.getenv("KITCHENFLEX_ACCESS_TOKEN", "")
    supplied=(authorization or "").removeprefix("Bearer ").strip()
    if not expected or not secrets.compare_digest(supplied, expected):
        raise HTTPException(401,"Backend-Zugriff nicht autorisiert. Bitte Server-Token in KITCHENFLEX eintragen.")
    url=str(body.url); validate_url(url)
    if not os.getenv("OPENAI_API_KEY"): raise HTTPException(503,"OPENAI_API_KEY fehlt auf dem Server.")
    if not shutil.which("ffmpeg"): raise HTTPException(503,"FFmpeg fehlt auf dem Server.")
    try:
        with tempfile.TemporaryDirectory(prefix="kitchenflex_") as tmp:
            opts={"format":"bestaudio/best","outtmpl":str(Path(tmp)/"audio.%(ext)s"),"noplaylist":True,"quiet":True,"no_warnings":True,"socket_timeout":20,"retries":1,"max_filesize":150*1024*1024,"match_filter":yt_dlp.utils.match_filter_func("duration <= 900"),"postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"64"}]}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info=ydl.extract_info(url,download=True); title=info.get("title") or "Kochvideo"
                audio=Path(ydl.prepare_filename(info)).with_suffix(".mp3")
            if not audio.exists():
                candidates=list(Path(tmp).glob("*.mp3"))
                if not candidates: raise RuntimeError("Audiospur konnte nicht extrahiert werden.")
                audio=candidates[0]
            if audio.stat().st_size>24*1024*1024: raise RuntimeError("Audio zu groß; bitte ein kürzeres Video verwenden.")
            client=OpenAI()
            with audio.open("rb") as f:
                transcript=str(client.audio.transcriptions.create(model="gpt-transcribe",file=f,response_format="text",prompt="Deutsches Kochvideo. Erkenne Lebensmittel, Mengen, Temperaturen, Garzeiten und Kochbegriffe genau."))
            if len(transcript.strip())<30: raise RuntimeError("Kein ausreichender Sprachinhalt erkannt.")
            result=client.chat.completions.create(model=os.getenv("RECIPE_MODEL","gpt-4o-mini"),messages=[
            {"role":"system","content":"Du bist KITCHENFLEX. Extrahiere ein deutsches Rezept aus dem Transkript. Erfinde keine Mengen, Zeiten oder Temperaturen. Unbekanntes als Nicht angegeben kennzeichnen und in notes erwähnen. Fasse Wiederholungen zusammen und bewahre die Reihenfolge."},
            {"role":"user","content":f"Videotitel: {title}\\n\\nTranskript:\\n{transcript}"}],
            response_format={"type":"json_schema","json_schema":{"name":"kitchenflex_recipe","strict":True,"schema":SCHEMA}})
            recipe=json.loads(result.choices[0].message.content); recipe["source_title"]=title
            return {"recipe":recipe,"source":url}
    except HTTPException: raise
    except Exception as e: raise HTTPException(500,"Videoanalyse fehlgeschlagen: "+str(e)[:300])
