from requests import get
from hashlib import sha256
import sqlite3
from bs4 import BeautifulSoup

headers = {
    "user-agent": "fedi-block-api (https://gitlab.com/EnjuAihara/fedi-block-api)"
}

def get_mastodon_blocks(domain: str) -> dict:
    blocks = {
        "Suspended servers": [],
        "Filtered media": [],
        "Limited servers": [],
        "Silenced servers": [],
    }

    try:
        doc = BeautifulSoup(
            get(f"https://{domain}/about/more", headers=headers, timeout=5).text,
            "html.parser",
        )
    except:
        return {}
        
    for header in doc.find_all("h3"):
        for line in header.find_next_siblings("table")[0].find_all("tr")[1:]:
            if header.text in blocks:
                blocks[header.text].append(
                    {
                        "domain": line.find("span").text,
                        "hash": line.find("span")["title"][9:],
                        "reason": line.find_all("td")[1].text.strip(),
                    }
                )
    return {
        "reject": blocks["Suspended servers"],
        "media_removal": blocks["Filtered media"],
        "federated_timeline_removal": blocks["Limited servers"] + blocks["Silenced servers"],
    }

def get_hash(domain: str) -> str:
    return sha256(domain.encode("utf-8")).hexdigest()

def get_type(domain: str) -> str:
    try:
        res = get(f"https://{domain}/nodeinfo/2.1.json", headers=headers, timeout=5)
        if res.status_code == 404:
            res = get(f"https://{domain}/nodeinfo/2.0.json", headers=headers, timeout=5)
        if res.ok:
            return res.json()["software"]["name"]
        elif res.status_code == 404:
            res = get(f"https://{domain}/api/v1/instance", headers=headers, timeout=5)
        if res.ok:
            return "mastodon"
    except:
        return None

conn = sqlite3.connect("blocks.db")
c = conn.cursor()

c.execute("select domain, software from instances where software in ('pleroma', 'mastodon')")

for blocker, software in c.fetchall():
    if software == "pleroma":
        print(blocker)
        try:
            # Blocks
            c.execute("delete from blocks where blocker = ?", (blocker,))
            federation = get(f"https://{blocker}/nodeinfo/2.1.json", headers=headers, timeout=5).json()["metadata"]["federation"]
            if "mrf_simple" in federation:
                for block_level, blocks in (federation["mrf_simple"] | {"quarantined_instances": federation["quarantined_instances"]}).items():
                    for blocked in blocks:
                        if blocked == "":
                            continue
                        c.execute("select domain from instances where domain = ?", (blocked,))
                        if c.fetchone() == None:
                            c.execute("insert into instances select ?, ?, ?", (blocked, get_hash(blocked), get_type(blocked)))
                        c.execute("insert into blocks select ?, ?, '', ?", (blocker, blocked, block_level))
            conn.commit()
            # Reasons
            if "mrf_simple_info" in federation:
                for block_level, info in (federation["mrf_simple_info"] | federation["quarantined_instances_info"] if "quarantined_instances_info" in federation else {}).items():
                    for blocked, reason in info.items():
                        c.execute("update blocks set reason = ? where blocker = ? and blocked = ? and block_level = ?", (reason["reason"], blocker, blocked, block_level))
            conn.commit()
        except Exception as e:
            print("error:", e, blocker)
    elif software == "mastodon":
        print(blocker)
        try:
            c.execute("delete from blocks where blocker = ?", (blocker,))
            json = get_mastodon_blocks(blocker)
            for block_level, blocks in json.items():
                for instance in blocks:
                    blocked, blocked_hash, reason = instance.values()
                    if blocked.count("*") <= 1:
                        c.execute("select hash from instances where hash = ?", (blocked_hash,))
                        if c.fetchone() == None:
                            c.execute(
                                "insert into instances select ?, ?, ?",
                                (blocked, get_hash(blocked), get_type(blocked)),
                            )
                    c.execute(
                        "insert into blocks select ?, ?, ?, ?",
                        (
                            blocker,
                            blocked if blocked.count("*") <= 1 else blocked_hash,
                            reason,
                            block_level,
                        ),
                    )
            conn.commit()
        except Exception as e:
            print("error:", e, blocker)
conn.close()
