from requests import get
from json import loads
import sqlite3

conn = sqlite3.connect("blocks.db")
c = conn.cursor()

with open("pleroma_instances.txt", "r") as f:
    while blocker := f.readline().strip():
        print(blocker)
        c.execute(f"delete from blocks where blocker = '{blocker}'")
        conn.commit()
        try:
            json = loads(get(f"https://{blocker}/nodeinfo/2.1.json").text)
            for mrf in json["metadata"]["federation"]["mrf_simple"]:
                for blocked in json["metadata"]["federation"]["mrf_simple"][mrf]:
                    c.execute(f"insert into blocks select '{blocker}', '{blocked}', '', '{mrf}'")
            for blocked in json["metadata"]["federation"]["quarantined_instances"]:
                c.execute(f"insert into blocks select '{blocker}', '{blocked}', '', 'quarantined_instances'")
            conn.commit()
        except:
            pass

conn.close()