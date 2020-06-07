import launcher.globalstorage as G
import urllib.request
import zipfile
import json
import sys
import os
import subprocess


def create_or_stay(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def download_file(url, dest):
    urllib.request.urlretrieve(url, dest)


INDEX_VERSION = "1.2.0"


def download_index(url="https://raw.githubusercontent.com/mcpython4-coding/Index/master/core.json"):
    download_file(url, G.local+"/home/versions/index.json")
    try:
        with open(G.local+"/home/versions/index.json") as f:
            d = json.load(f)
    except json.decoder.JSONDecodeError:
        print("unable to decode json format")
        sys.exit(-1)
    if "INDEX VERSION" not in d or d["INDEX VERSION"] != INDEX_VERSION:
        if "OLD VERSION LINKS" in d and INDEX_VERSION in d["OLD VERSION LINKS"]:
            url = d["OLD VERSION LINKS"][INDEX_VERSION]
            download_index(url=url)
        else:
            raise ValueError("can't find readable index file for this version of the launcher (found: {}, needed: {})".
                             format(d["INDEX VERSION"], INDEX_VERSION))
    return d


class Launcher:
    def __init__(self):
        self.index = None

        self.load_index()

    def load_index(self):
        self.index = download_index()

    def download_version(self, version_name: str):
        print("downloading...")
        file = G.local+"/home/versions/{}.zip".format(version_name)
        folder = G.local+"/home/versions/{}".format(version_name)
        if os.path.exists(folder): return folder
        if not os.path.exists(file):
            download_file("https://github.com/mcpython4-coding/Index/blob/master/builds/build_{}.zip?raw=true,".format(
                version_name), file)
        i = 1
        with zipfile.ZipFile(file) as f:
            names = f.namelist()
            total = len(names)
            for element in names:
                print("\rextracting {}/{}: {}".format(i, total, element), end="")
                r = os.path.join(folder, element)
                create_or_stay(os.path.dirname(r))
                with open(r, mode="wb") as fw:
                    fw.write(f.read(element))
                i += 1
        print()
        return folder

    def launch_version(self, version_name: str, *args):
        print("LOADING VERSION {} OF MCPYTHON 4".format(version_name))
        folder = self.download_version(version_name)
        create_or_stay(G.local+"/home/data_{}".format(version_name))
        create_or_stay(G.local+"/home/cache_{}".format(version_name))
        create_or_stay(G.local+"/home/mods_{}".format(version_name))
        create_or_stay(G.local+"/home/saves")

        flag = False
        if os.path.exists(G.local+"/config.json"):
            with open(G.local+"/config.json") as f:
                data = json.load(f)
            flag = "latest_version" in data and data["latest_version"] == version_name

        if not flag:
            print("installing requirements...")
            subprocess.call(["py", "-{}.{}".format(sys.version_info[0], sys.version_info[1]),
                             folder+"/installer.py"], stderr=sys.stderr,
                            stdout=sys.stdout)

        with open(G.local+"/config.json", mode="w") as f:
            json.dump({"latest_version": version_name}, f)

        subprocess.call(["py", "-{}.{}".format(sys.version_info[0], sys.version_info[1]),
                         folder+"/__main__.py", "--home-folder", G.local+"/home/data_{}".format(version_name),
                         "--build-folder", G.local+"/home/cache_{}".format(version_name), "--addmoddir",
                         G.local+"/home/mods_{}".format(version_name), "--saves-directory",
                         G.local+"/home/saves"]+list(args))

    def ask_user(self):
        print("the following versions where found: ")
        v = list(self.index["builds"].keys())
        v.sort()
        for i, version in enumerate(v):
            print("[{}]: {}".format(i + 1, version))
        version = v[int(input("select version number: ")) - 1]
        builds = self.index["builds"][version]
        builds.sort()
        print("the following builds were found: ")
        for i, build in enumerate(builds):
            print("[{}] {}".format(i + 1, build))
        build_name = builds[int(input("build number: ")) - 1]
        self.launch_version(build_name)

