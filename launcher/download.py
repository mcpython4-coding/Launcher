import urllib.request
import globals as G
import json
import os

DATA = None


def download_index():
    response = urllib.request.urlopen("https://raw.githubusercontent.com/mcpython4-coding/Index/master/core.json")
    data = response.read()
    if os.path.exists(G.local+"/index/index.json"): os.remove(G.local+"/index/index.json")
    with open(G.local+"/index/index.json", mode="wb") as f: f.write(data)
    global DATA
    DATA = json.loads(data.decode("UTF-8"))


def download_by_name(name: str):
    if DATA is None:
        download_index()
    print("downloading version...")
    e = G.local+"/versions/version_{}.zip".format(name)
    if os.path.exists(e): os.remove(e)
    urllib.request.urlretrieve(DATA[name]["url"], e)
    print("finished!")

