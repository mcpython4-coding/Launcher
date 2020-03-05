import urllib.request
import globalstorage as G
import json
import os

DATA = None

INDEX_VERSION = "1.0.1"


def download_index(url="https://raw.githubusercontent.com/mcpython4-coding/Index/master/core.json"):
    response = urllib.request.urlopen(url)
    data = response.read()
    if os.path.exists(G.local+"/index/index.json"): os.remove(G.local+"/index/index.json")
    with open(G.local+"/index/index.json", mode="wb") as f: f.write(data)
    global DATA
    DATA = json.loads(data.decode("UTF-8"))
    if "INDEX VERSION" not in DATA or DATA["INDEX VERSION"] != INDEX_VERSION:
        if "OLD VERSION LINKS" in DATA and INDEX_VERSION in DATA["OLD VERSION LINKS"]:
            url = DATA["OLD VERSION LINKS"][INDEX_VERSION]
            download_index(url=url)
        else:
            raise ValueError("can't find readable index file for this version of the launcher")


def download_by_name(name: str):
    if DATA is None:
        download_index()
    print("downloading version...")
    e = G.local+"/versions/version_{}.zip".format(name)
    if os.path.exists(e): os.remove(e)
    urllib.request.urlretrieve(DATA[name]["url"], e)
    print("finished!")

