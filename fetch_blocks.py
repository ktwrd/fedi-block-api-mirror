from requests import get
from json import loads
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
                    c.execute("insert into blocks select ?, ?, '', ?", (blocker, blocked, mrf))
            for blocked in json["metadata"]["federation"]["quarantined_instances"]:
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
            for blocked in json["reject"]:
                if blocked["domain"].count("*") > 1:
                    c.execute("insert into blocks select ?, ifnull((select domain from instances where hash = ?), ?), ?, 'reject'", (blocker, blocked["hash"], blocked["hash"], blocked['reason']))
                else:
                    c.execute("insert into blocks select ?, ?, ?, 'reject'", (blocker, blocked["domain"], blocked["reason"]))
            for blocked in json["media_removal"]:
                if blocked["domain"].count("*") > 1:
                    c.execute("insert into blocks select ?, ifnull((select domain from instances where hash = ?), ?), ?, 'media_removal'", (blocker, blocked["hash"], blocked["hash"], blocked['reason']))
                else:
                    c.execute("insert into blocks select ?, ?, ?, 'media_removal'", (blocker, blocked["domain"], blocked["reason"]))
            for blocked in json["federated_timeline_removal"]:
                if blocked["domain"].count("*") > 1:
                    c.execute("insert into blocks select ?, ifnull((select domain from instances where hash = ?), ?), ?, 'federated_timeline_removal'", (blocker, blocked["hash"], blocked["hash"], blocked['reason']))
                else:
                    c.execute("insert into blocks select ?, ?, ?, 'federated_timeline_removal'", (blocker, blocked["domain"], blocked["reason"]))
            conn.commit()
        except:
            pass

conn.close()