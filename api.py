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
    c.execute("select blocker, block_level from blocks where blocked = ?", (domain,))
    blocks = c.fetchall()
    conn.close()

    result = {
        "reject": [],
        "media_removal": [],
        "federated_timeline_removal": [],
        "media_nsfw": [],
        "quarantined_instances": [],
        "report_removal": [],
        "followers_only": [],
        "accept": [],
        "avatar_removal": [],
        "banner_removal": [],
        "reject_deletes": [],
    }

    for domain, block_level in blocks:
        result[block_level].append(domain)

    return result

