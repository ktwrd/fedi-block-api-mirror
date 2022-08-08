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
        "source_code": "https://git.kiwifarms.net/mint/fedi-block-api",
    }

@app.get(base_url+"/api")
def blocked(domain: str = None, reason: str = None):
    if domain == None and reason == None:
        raise HTTPException(status_code=400, detail="No filter specified")
    conn = sqlite3.connect("blocks.db")
    c = conn.cursor()
    if domain != None:
        wildchar = "*." + ".".join(domain.split(".")[-domain.count("."):])
        punycode = domain.encode('idna').decode('utf-8')
        c.execute("select blocker, blocked, block_level, reason from blocks where blocked = ? or blocked = ? or blocked = ? or blocked = ? or blocked = ? or blocked = ?",
                  (domain, "*." + domain, wildchar, get_hash(domain), punycode, "*." + punycode))
    else:
        c.execute("select * from blocks where reason like ? and reason != ''", ("%"+reason+"%",))
    blocks = c.fetchall()
    conn.close()

    result = {}
    reasons = {}
    wildcards = {}
    if domain != None:
        for domain, blocked, block_level, reason in blocks:
            if block_level in result:
                result[block_level].append(domain)
            else:
                result[block_level] = [domain]
            if blocked == "*." + ".".join(blocked.split(".")[-blocked.count("."):]):
                wildcards.append(domain)
            if reason != "":
                if block_level in reasons:
                    reasons[block_level][domain] = reason
                else:
                    reasons[block_level] = {domain: reason}
        return {"blocks": result, "reasons": reasons, "wildcards": wildcards}

    for blocker, blocked, reason, block_level in blocks:
        if block_level in result:
            result[block_level].append({"blocker": blocker, "blocked": blocked, "reason": reason})
        else:
            result[block_level] = [{"blocker": blocker, "blocked": blocked, "reason": reason}]
    return {"blocks": result}

@app.get(base_url+"/")
def index(request: Request, domain: str = None, reason: str = None):
    if domain == "" or reason == "":
        return responses.RedirectResponse("/")
    info = None
    blocks = None
    if domain == None and reason == None:
        info = get(f"http://127.0.0.1:{port}{base_url}/info")
        if not info.ok:
            raise HTTPException(status_code=info.status_code, detail=info.text)
        info = info.json()
    elif domain != None:
        blocks = get(f"http://127.0.0.1:{port}{base_url}/api?domain={domain}")
    elif reason != None:
        blocks = get(f"http://127.0.0.1:{port}{base_url}/api?reason={reason}")
    if blocks != None:
        if not blocks.ok:
            raise HTTPException(status_code=blocks.status_code, detail=blocks.text)
        blocks = blocks.json()
    return templates.TemplateResponse("index.html", {"request": request, "domain": domain, "blocks": blocks, "wildcards": wildcards, "reason": reason, "info": info})

if __name__ == "__main__":
    uvicorn.run("api:app", host="127.0.0.1", port=port, log_level="info")
