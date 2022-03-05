from requests import get
from json import loads
from hashlib import sha256
import sqlite3

conn = sqlite3.connect("blocks.db")
c = conn.cursor()

with open("pleroma_instances.txt", "r") as f:
    while blocker := f.readline().strip():
        print(blocker)
        try:
            c.execute("delete from blocks where blocker = ?", (blocker,))
            json = loads(get(f"https://{blocker}/nodeinfo/2.1.json").text)
            for mrf in json["metadata"]["federation"]["mrf_simple"]:
                for blocked in json["metadata"]["federation"]["mrf_simple"][mrf]:
                    if blocked == "":
                        continue
                    c.execute("select case when ? in (select domain from instances) then 1 else 0 end", (blocked,))
                    if c.fetchone() == (0,):
                        c.execute("insert into instances select ?, ?", (blocked, sha256(bytes(blocked, "utf-8")).hexdigest()))
                    c.execute("insert into blocks select ?, ?, '', ?", (blocker, blocked, mrf))
            for blocked in json["metadata"]["federation"]["quarantined_instances"]:
                if blocked == "":
                    continue
                c.execute("select case when ? in (select domain from instances) then 1 else 0 end", (blocked,))
                if c.fetchone() == (0,):
                    c.execute("insert into instances select ?, ?", (blocked, sha256(bytes(blocked, "utf-8")).hexdigest()))
                c.execute("insert into blocks select ?, ?, '', 'quarantined_instances'", (blocker, blocked))
            conn.commit()
            for mrf in json["metadata"]["federation"]["mrf_simple_info"]:
                for blocked in json["metadata"]["federation"]["mrf_simple_info"][mrf]:
                    c.execute("update blocks set reason = ? where blocker = ? and blocked = ? and block_level = ?", (json["metadata"]["federation"]["mrf_simple_info"][mrf][blocked]["reason"], blocker, blocked, mrf))
            for blocked in json["metadata"]["federation"]["quarantined_instances_info"]["quarantined_instances"]:
                c.execute("update blocks set reason = ? where blocker = ? and blocked = ? and block_level = 'quarantined_instances'", (json["metadata"]["federation"]["quarantined_instances_info"]["quarantined_instances"][blocked]["reason"], blocker, blocked))
            conn.commit()
        except:
            pass

with open("mastodon_instances.txt", "r") as f:
    while blocker := f.readline().strip():
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
                            c.execute("insert into instances select ?, ?", (blocked["domain"], sha256(bytes(blocked["domain"], "utf-8")).hexdigest()))
                        c.execute("insert into blocks select ?, ?, ?, ?", (blocker, blocked["domain"], blocked["reason"], block_level))
            conn.commit()
        except:
            pass

conn.close()