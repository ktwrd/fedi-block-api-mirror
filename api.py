from fastapi import FastAPI
import sqlite3

base_url = ""
app = FastAPI(docs_url=base_url+"/docs", redoc_url=base_url+"/redoc")

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

@app.get(base_url+"/domain/{domain}")
def blocked(domain: str):
    conn = sqlite3.connect("blocks.db")
    c = conn.cursor()
    wildchar = "*." + ".".join(domain.split(".")[-domain.count("."):])
    c.execute("select blocker, block_level, reason from blocks where blocked = ? or blocked = ?", (domain, wildchar))
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

