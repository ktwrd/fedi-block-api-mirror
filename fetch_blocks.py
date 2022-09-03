from requests import get
from requests import post
from hashlib import sha256
import sqlite3
from bs4 import BeautifulSoup
from json import dumps

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0"
}


def get_mastodon_blocks(domain: str) -> dict:
    blocks = {
        "Suspended servers": [],
        "Filtered media": [],
        "Limited servers": [],
        "Silenced servers": [],
    }

    translations = {
        "Silenced instances": "Silenced servers",
        "Suspended instances": "Suspended servers",
        "Gesperrte Server": "Suspended servers",
        "Gefilterte Medien": "Filtered media",
        "Stummgeschaltete Server": "Silenced servers",
        "停止済みのサーバー": "Suspended servers",
        "メディアを拒否しているサーバー": "Filtered media",
        "サイレンス済みのサーバー": "Silenced servers",
        "Serveurs suspendus": "Suspended servers",
        "Médias filtrés": "Filtered media",
        "Serveurs limités": "Silenced servers",
    }

    try:
        doc = BeautifulSoup(
            get(f"https://{domain}/about/more", headers=headers, timeout=5).text,
            "html.parser",
        )
    except:
        return {}

    for header in doc.find_all("h3"):
        header_text = header.text
        if header_text in translations:
            header_text = translations[header_text]
        if header_text in blocks:
            # replaced find_next_siblings with find_all_next to account for instances that e.g. hide lists in dropdown menu
            for line in header.find_all_next("table")[0].find_all("tr")[1:]:
                blocks[header_text].append(
                    {
                        "domain": line.find("span").text,
                        "hash": line.find("span")["title"][9:],
                        "reason": line.find_all("td")[1].text.strip(),
                    }
                )
    return {
        "reject": blocks["Suspended servers"],
        "media_removal": blocks["Filtered media"],
        "federated_timeline_removal": blocks["Limited servers"]
        + blocks["Silenced servers"],
    }

def get_friendica_blocks(domain: str) -> dict:
    blocks = []

    try:
        doc = BeautifulSoup(
            get(f"https://{domain}/friendica", headers=headers, timeout=5).text,
            "html.parser",
        )
    except:
        return {}

    blocklist = doc.find(id="about_blocklist")
    for line in blocklist.find("table").find_all("tr")[1:]:
            blocks.append(
                {
                    "domain": line.find_all("td")[0].text.strip(),
                    "reason": line.find_all("td")[1].text.strip()
                }
            )

    return {
        "reject": blocks
    }

def get_pisskey_blocks(domain: str) -> dict:
    blocks = {
        "suspended": [],
        "blocked": []
    }

    try:
        counter = 0
        step = 99
        while True:
            # iterating through all "suspended" (follow-only in its terminology) instances page-by-page, since that troonware doesn't support sending them all at once
            try:
                if counter == 0:
                    doc = post(f"https://{domain}/api/federation/instances", data=dumps({"sort":"+caughtAt","host":None,"suspended":True,"limit":step}), headers=headers, timeout=5).json()
                    if doc == []: raise
                else:
                    doc = post(f"https://{domain}/api/federation/instances", data=dumps({"sort":"+caughtAt","host":None,"suspended":True,"limit":step,"offset":counter-1}), headers=headers, timeout=5).json()
                    if doc == []: raise
                for instance in doc:
                    # just in case
                    if instance["isSuspended"]:
                        blocks["suspended"].append(
                            {
                                "domain": instance["host"],
                                # no reason field, nothing
                                "reason": ""
                            }
                        )
                counter = counter + step
            except:
                counter = 0
                break

        while True:
            # same shit, different asshole ("blocked" aka full suspend)
            try:
                if counter == 0:
                    doc = post(f"https://{domain}/api/federation/instances", data=dumps({"sort":"+caughtAt","host":None,"blocked":True,"limit":step}), headers=headers, timeout=5).json()
                    if doc == []: raise
                else:
                    doc = post(f"https://{domain}/api/federation/instances", data=dumps({"sort":"+caughtAt","host":None,"blocked":True,"limit":step,"offset":counter-1}), headers=headers, timeout=5).json()
                    if doc == []: raise
                for instance in doc:
                    if instance["isBlocked"]:
                        blocks["blocked"].append(
                            {
                                "domain": instance["host"],
                                "reason": ""
                            }
                        )
                counter = counter + step
            except:
                counter = 0
                break

        return {
            "reject": blocks["blocked"],
            "followers_only": blocks["suspended"]
        }

    except:
        return {}

def get_hash(domain: str) -> str:
    return sha256(domain.encode("utf-8")).hexdigest()


def get_type(domain: str) -> str:
    try:
        res = get(f"https://{domain}/nodeinfo/2.1.json", headers=headers, timeout=5)
        if res.status_code == 404:
            res = get(f"https://{domain}/nodeinfo/2.0", headers=headers, timeout=5)
        if res.status_code == 404:
            res = get(f"https://{domain}/nodeinfo/2.0.json", headers=headers, timeout=5)
        if res.ok and "text/html" in res.headers["content-type"]:
            res = get(f"https://{domain}/nodeinfo/2.1", headers=headers, timeout=5)
        if res.ok:
            if res.json()["software"]["name"] == "akkoma":
                return "pleroma"
            elif res.json()["software"]["name"] == "rebased":
                return "pleroma"
            elif res.json()["software"]["name"] == "hometown":
                return "mastodon"
            elif res.json()["software"]["name"] == "ecko":
                return "mastodon"
            elif res.json()["software"]["name"] == "calckey":
                return "misskey"
            else:
                return res.json()["software"]["name"]
        elif res.status_code == 404:
            res = get(f"https://{domain}/api/v1/instance", headers=headers, timeout=5)
        if res.ok:
            return "mastodon"
    except:
        return None


conn = sqlite3.connect("blocks.db")
c = conn.cursor()

c.execute(
    "select domain, software from instances where software in ('pleroma', 'mastodon', 'friendica', 'misskey')"
)

for blocker, software in c.fetchall():
    if software == "pleroma":
        print(blocker)
        try:
            # Blocks
            federation = get(
                f"https://{blocker}/nodeinfo/2.1.json", headers=headers, timeout=5
            ).json()["metadata"]["federation"]
            if "mrf_simple" in federation:
                for block_level, blocks in (
                    {**federation["mrf_simple"],
                    **{"quarantined_instances": federation["quarantined_instances"]}}
                ).items():
                    for blocked in blocks:
                        if blocked == "":
                            continue
                        blocked == blocked.lower()
                        blocker == blocker.lower()
                        c.execute(
                            "select domain from instances where domain = ?", (blocked,)
                        )
                        if c.fetchone() == None:
                            c.execute(
                                "insert into instances select ?, ?, ?",
                                (blocked, get_hash(blocked), get_type(blocked)),
                            )
                        c.execute(
                            "select * from blocks where blocker = ? and blocked = ? and block_level = ?",
                            (blocker, blocked, block_level),
                        )
                        if c.fetchone() == None:
                            c.execute(
                                "insert into blocks select ?, ?, '', ?",
                                (blocker, blocked, block_level),
                            )
            conn.commit()
            # Reasons
            if "mrf_simple_info" in federation:
                for block_level, info in (
                    {**federation["mrf_simple_info"],
                    **(federation["quarantined_instances_info"]
                    if "quarantined_instances_info" in federation
                    else {})}
                ).items():
                    for blocked, reason in info.items():
                        blocker == blocker.lower()
                        blocked == blocked.lower()
                        c.execute(
                            "update blocks set reason = ? where blocker = ? and blocked = ? and block_level = ?",
                            (reason["reason"], blocker, blocked, block_level),
                        )
            conn.commit()
        except Exception as e:
            print("error:", e, blocker)
    elif software == "mastodon":
        print(blocker)
        try:
            json = get_mastodon_blocks(blocker)
            for block_level, blocks in json.items():
                for instance in blocks:
                    blocked, blocked_hash, reason = instance.values()
                    blocked == blocked.lower()
                    blocker == blocker.lower()
                    if blocked.count("*") <= 1:
                        c.execute(
                            "select hash from instances where hash = ?", (blocked_hash,)
                        )
                        if c.fetchone() == None:
                            c.execute(
                                "insert into instances select ?, ?, ?",
                                (blocked, get_hash(blocked), get_type(blocked)),
                            )
                    c.execute(
                        "select * from blocks where blocker = ? and blocked = ? and block_level = ?",
                        (blocker, blocked if blocked.count("*") <= 1 else blocked_hash, block_level),
                    )
                    if c.fetchone() == None:
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
    elif software == "friendica" or software == "misskey":
        print(blocker)
        try:
            if software == "friendica":
                json = get_friendica_blocks(blocker)
            elif software == "misskey":
                json = get_pisskey_blocks(blocker)
            for block_level, blocks in json.items():
                for instance in blocks:
                    blocked, reason = instance.values()
                    blocked == blocked.lower()
                    blocker == blocker.lower()
                    c.execute(
                        "select domain from instances where domain = ?", (blocked,)
                    )
                    if c.fetchone() == None:
                        c.execute(
                            "insert into instances select ?, ?, ?",
                            (blocked, get_hash(blocked), get_type(blocked)),
                        )
                    c.execute(
                        "select * from blocks where blocker = ? and blocked = ?",
                        (blocker, blocked),
                    )
                    if c.fetchone() == None:
                        c.execute(
                            "insert into blocks select ?, ?, ?, ?",
                            (
                                blocker,
                                blocked,
                                reason,
                                block_level,
                            ),
                        )
            conn.commit()
        except Exception as e:
            print("error:", e, blocker)
conn.close()
