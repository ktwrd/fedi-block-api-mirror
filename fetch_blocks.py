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
            json = get(f"https://{blocker}/nodeinfo/2.1.json", headers=headers, timeout=5).json()
            if "mrf_simple" in json["metadata"]["federation"]:
                for mrf in json["metadata"]["federation"]["mrf_simple"]:
                    for blocked in json["metadata"]["federation"]["mrf_simple"][mrf]:
                        if blocked == "":
                            continue
                        c.execute("select domain from instances where domain = ?", (blocked,))
                        if c.fetchone() == None:
                            c.execute("insert into instances select ?, ?, ?", (blocked, sha256(bytes(blocked, "utf-8")).hexdigest(), get_type(blocked)))
                        c.execute("insert into blocks select ?, ?, '', ?", (blocker, blocked, mrf))
            # Quarantined Instances
            if "quarantined_instances" in json["metadata"]["federation"]:
                for blocked in json["metadata"]["federation"]["quarantined_instances"]:
                    if blocked == "":
                        continue
                    c.execute("select domain from instances where domain = ?", (blocked,))
                    if c.fetchone() == None:
                        c.execute("insert into instances select ?, ?, ?", (blocked, sha256(bytes(blocked, "utf-8")).hexdigest(), get_type(blocked)))
                    c.execute("insert into blocks select ?, ?, '', 'quarantined_instances'", (blocker, blocked))
            conn.commit()
            # Reasons
            if "mrf_simple_info" in json["metadata"]["federation"]:
                for mrf in json["metadata"]["federation"]["mrf_simple_info"]:
                    for blocked in json["metadata"]["federation"]["mrf_simple_info"][mrf]:
                        c.execute("update blocks set reason = ? where blocker = ? and blocked = ? and block_level = ?", (json["metadata"]["federation"]["mrf_simple_info"][mrf][blocked]["reason"], blocker, blocked, mrf))
            if "quarantined_instances_info" in json["metadata"]["federation"]:
                for blocked in json["metadata"]["federation"]["quarantined_instances_info"]["quarantined_instances"]:
                    c.execute("update blocks set reason = ? where blocker = ? and blocked = ? and block_level = 'quarantined_instances'", (json["metadata"]["federation"]["quarantined_instances_info"]["quarantined_instances"][blocked]["reason"], blocker, blocked))
            conn.commit()
        except Exception as e:
            print("error:", e, blocker)
    elif software == "mastodon":
        print(blocker)
        try:
            c.execute("delete from blocks where blocker = ?", (blocker,))
            json = get_mastodon_blocks(blocker)
            for block_level in json:
                for blocked in json[block_level]:
                    if blocked["domain"].count("*") > 1:
                        # instance is censored, check if domain of hash is known, if not, insert the hash
                        c.execute("insert into blocks select ?, ifnull((select domain from instances where hash = ?), ?), ?, ?", (blocker, blocked["hash"], blocked["hash"], blocked['reason'], block_level))
                    else:
                        # instance is not censored
                        c.execute("select domain from instances where domain = ?", (blocked["domain"],))
                        if c.fetchone() == None:
                            # if instance not known, add it
                            c.execute("insert into instances select ?, ?, ?", (blocked["domain"], sha256(bytes(blocked["domain"], "utf-8")).hexdigest(), get_type(blocked["domain"])))
                        c.execute("insert into blocks select ?, ?, ?, ?", (blocker, blocked["domain"], blocked["reason"], block_level))
            conn.commit()
        except Exception as e:
            print("error:", e, blocker)
conn.close()
