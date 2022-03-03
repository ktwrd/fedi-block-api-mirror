from requests import get

list = []

with open("instances.txt", "r") as f:
    list = f.readlines()

for line in list:
    print(line.replace("\n", ""))
    try:
        res = get("https://"+line.replace("\n", ""), timeout=5)
        if "pleroma" in res.text.lower():
            with open("pleroma_instances.txt", "a") as f:
                f.write(line)
        elif "mastodon" in res.text.lower():
            with open("mastodon_instances.txt", "a") as f:
                f.write(line)
        else:
            with open("other_instances.txt", "a") as f:
                f.write(line)
    except:
        print("error:", line)