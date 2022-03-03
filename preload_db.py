import sqlite3
from hashlib import sha256

conn = sqlite3.connect("blocks_default.db")
c = conn.cursor()

with open("pleroma_instances.txt", "r") as f:
    while line := f.readline():
        print(line.rstrip(), sha256(bytes(line.rstrip(), "utf-8")).hexdigest())
        c.execute(f"insert into instances select \"{line.rstrip()}\", \"{sha256(bytes(line.rstrip(), 'utf-8')).hexdigest()}\"")
        conn.commit()

with open("mastodon_instances.txt", "r") as f:
    while line := f.readline():
        print(line.rstrip(), sha256(bytes(line.rstrip(), "utf-8")).hexdigest())
        c.execute(f"insert into instances select \"{line.rstrip()}\", \"{sha256(bytes(line.rstrip(), 'utf-8')).hexdigest()}\"")
        conn.commit()