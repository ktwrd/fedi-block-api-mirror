from requests import get
from json import loads
from hashlib import sha256
import sqlite3

def get_type(domain: str) -> str:
    try:
        res = get("https://"+domain, timeout=5)
        if "pleroma" in res.text.lower():
            print("pleroma")
            return "pleroma"
        elif "mastodon" in res.text.lower():
            print("mastodon")
            return "mastodon"
        return ""
    except Exception as e:
        print("error:", e, domain)
        return ""

conn = sqlite3.connect("blocks.db")
c = conn.cursor()

c.execute("select domain, software from instances where software in ('pleroma', 'mastodon')")
for instance in c.fetchall():
    if instance[1] == "pleroma":
        blocker = instance[0]
        print(blocker)
        try:
            # Blocks
            c.execute("delete from blocks where blocker = ?", (blocker,))
            json = loads(get(f"https://{blocker}/nodeinfo/2.1.json").text)
            if "mrf_simple" in json["metadata"]["federation"]:
                for mrf in json["metadata"]["federation"]["mrf_simple"]:
                    for blocked in json["metadata"]["federation"]["mrf_simple"][mrf]:
                        if blocked == "":
                            continue
                        c.execute("select case when ? in (select domain from instances) then 1 else 0 end", (blocked,))
                        if c.fetchone() == (0,):
                            c.execute("insert into instances select ?, ?, ?", (blocked, sha256(bytes(blocked, "utf-8")).hexdigest(), get_type(blocked)))
                        c.execute("insert into blocks select ?, ?, '', ?", (blocker, blocked, mrf))
            # Quarantined Instances
            if "quarantined_instances" in json["metadata"]["federation"]:
                for blocked in json["metadata"]["federation"]["quarantined_instances"]:
                    if blocked == "":
                        continue
                    c.execute("select case when ? in (select domain from instances) then 1 else 0 end", (blocked,))
                    if c.fetchone() == (0,):
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
    elif instance[1] == "mastodon":
        blocker = instance[0]
        print(blocker)
        try:
            c.execute("delete from blocks where blocker = ?", (blocker,))
            json = loads(get(f"http://127.0.0.1:8069/{blocker}").text)
            for block_level in ["reject", "media_removal", "federated_timeline_removal"]:
                for blocked in json[block_level]:
                    if blocked["domain"].count("*") > 1:
                        c.execute("insert into blocks select ?, ifnull((select domain from instances where hash = ?), ?), ?, ?", (blocker, blocked["hash"], blocked["hash"], blocked['reason'], block_level))
                    else:
                        c.execute("select case when ? in (select domain from instances) then 1 else 0 end", (blocked["domain"],))
                        if c.fetchone() == (0,):
                            c.execute("insert into instances select ?, ?, ?", (blocked["domain"], sha256(bytes(blocked["domain"], "utf-8")).hexdigest(), get_type(blocked["domain"])))
                        c.execute("insert into blocks select ?, ?, ?, ?", (blocker, blocked["domain"], blocked["reason"], block_level))
            conn.commit()
        except Exception as e:
            print("error:", e, blocker)

conn.close()