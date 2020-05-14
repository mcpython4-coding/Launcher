import urllib.request
import globalstorage as G
import json
import os
import sys
import shutil

DATA = None

INDEX_VERSION = "1.1.0"


def download_index(url="https://raw.githubusercontent.com/mcpython4-coding/Index/master/core.json"):
    shutil.copy(G.local+"/index/index.json", G.local+"/index/index_backup.json")
    download_file(url, G.local+"/index/index.json")
    global DATA
    try:
        with open(G.local + "/index/index.json") as f:
            DATA = json.load(f)
    except json.decoder.JSONDecodeError:
        print("error during downloading index file. GIT system for your ip is overloaded, falling back to backup...")
        shutil.copy(G.local+"/index/index_backup.json", G.local+"/index/index.json")
        try:
            with open(G.local + "/index/index.json") as f:
                DATA = json.load(f)
        except json.decoder.JSONDecodeError:
            print("previous file was also invalid, exiting...")
            sys.exit(-1)
    if "INDEX VERSION" not in DATA or DATA["INDEX VERSION"] != INDEX_VERSION:
        if "OLD VERSION LINKS" in DATA and INDEX_VERSION in DATA["OLD VERSION LINKS"]:
            url = DATA["OLD VERSION LINKS"][INDEX_VERSION]
            download_index(url=url)
        else:
            raise ValueError("can't find readable index file for this version of the launcher")


def download_by_id(group: str, id: int):
    if DATA is None:
        download_index()
    print("downloading version...")
    e = G.local+"/versions/version_{}_{}.zip".format(group, id)
    if os.path.exists(e): os.remove(e)
    urllib.request.urlretrieve(DATA["versions"][group][id]["url"], e)
    print("finished!")


def download_file(url, dest):
    urllib.request.urlretrieve(url, dest)

