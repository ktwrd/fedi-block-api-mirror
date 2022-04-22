import uvicorn
from fastapi import FastAPI, Request, HTTPException, responses
import sqlite3
from hashlib import sha256
from fastapi.templating import Jinja2Templates
from requests import get
from json import loads

with open("config.json") as f:
    config = loads(f.read())
    base_url = config["base_url"]
    port = config["port"]
app = FastAPI(docs_url=base_url+"/docs", redoc_url=base_url+"/redoc")
templates = Jinja2Templates(directory=".")

def get_hash(domain: str) -> str:
    return sha256(domain.encode("utf-8")).hexdigest()

@app.get(base_url+"/info")
def info():
    conn = sqlite3.connect("blocks.db")
    c = conn.cursor()
    c.execute("select (select count(domain) from instances), (select count(domain) from instances where software in ('pleroma', 'mastodon')), (select count(blocker) from blocks)")
    known, indexed, blocks = c.fetchone()
    c.close()
    return {
        "known_instances": known,
        "indexed_instances": indexed,
        "blocks_recorded": blocks,
        "source_code": "https://gitlab.com/EnjuAihara/fedi-block-api",
    }

@app.get(base_url+"/api")
def blocked(domain: str = None):
    if domain == None:
        raise HTTPException(status_code=400, detail="No domain specified")
    conn = sqlite3.connect("blocks.db")
    c = conn.cursor()
    wildchar = "*." + ".".join(domain.split(".")[-domain.count("."):])
    c.execute("select blocker, block_level, reason from blocks where blocked = ? or blocked = ? or blocked = ?", (domain, wildchar, get_hash(domain)))
    blocks = c.fetchall()
    conn.close()

    result = {}
    reasons = {}

    for domain, block_level, reason in blocks:
        if block_level in result:
            result[block_level].append(domain)
        else:
            result[block_level] = [domain]
            
        if reason != "":
            if block_level in reasons:
                reasons[block_level][domain] = reason
            else:
                reasons[block_level] = {domain: reason}

    return {"blocks": result, "reasons": reasons}

@app.get(base_url+"/")
def index(request: Request, domain: str = None):
    if domain == "":
        return responses.RedirectResponse("/")
    blocks = get(f"http://127.0.0.1:{port}{base_url}/api?domain={domain}")
    info = None
    if domain == None:
        info = get(f"http://127.0.0.1:{port}{base_url}/info")
        if not info.ok:
            raise HTTPException(status_code=info.status_code, detail=info.text)
        info = info.json()
    if not blocks.ok:
        raise HTTPException(status_code=blocks.status_code, detail=blocks.text)
    return templates.TemplateResponse("index.html", {"request": request, "domain": domain, "blocks": blocks.json(), "info": info})

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=port, log_level="info")
