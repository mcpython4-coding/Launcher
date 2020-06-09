import launcher.globalstorage as G
import urllib.request
import zipfile
import json
import sys
import os
import subprocess
import shutil


def create_or_stay(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def download_file(url, dest):
    urllib.request.urlretrieve(url, dest)


INDEX_VERSION = "1.2.0"


def download_index(url="https://raw.githubusercontent.com/mcpython4-coding/Index/master/core.json"):
    download_file(url, G.local+"/versions/index.json")
    try:
        with open(G.local+"/versions/index.json") as f:
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
        file = G.local+"/versions/{}.zip".format(version_name)
        folder = G.local+"/versions/{}".format(version_name)
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
        print("\nfinished!")
        return folder

    def launch_version(self, profile: str, version_name: str = None, *args):
        print("LOADING VERSION {} OF MCPYTHON 4".format(version_name))
        if version_name is None:
            with open(G.local+"/home/{}/profile.json".format(profile)) as f:
                version_name = json.load(f)["build"]
        folder = self.download_version(version_name)

        DATA = G.local+"/home/{}/data".format(profile)
        CACHE = G.local+"/home/{}/cache".format(profile)
        MODS = G.local+"/home/{}/mods".format(profile)
        SAVES = G.local+"/home/{}/saves".format(profile)

        create_or_stay(DATA)
        create_or_stay(CACHE)
        create_or_stay(MODS)
        create_or_stay(SAVES)

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
                         folder+"/__main__.py", "--home-folder", DATA, "--build-folder", CACHE, "--addmoddir", MODS,
                         "--saves-directory", SAVES]+list(args))

    @classmethod
    def select_profile(cls):
        profiles = os.listdir(G.local + "/home")
        print("the following profiles were found: ")
        [print("[{}]: {}".format(i + 1, e)) for i, e in enumerate(profiles)]
        a = input("select profile: ")
        return profiles[int(a)] if a not in profiles else a

    def ask_user(self):
        print("would you like to a) run an existing profile, b) create an new profile or c) edit the version"
              "of an profile?")
        a = input().lower().strip()
        if a == "a":
            self.launch_version(self.select_profile())
        elif a == "b":
            self.generate_new(input("name of the profile: "))
        elif a == "c":
            profile = self.select_profile()
            if not os.path.exists(G.local+"/home/"+profile):
                print("you have to first create the profile!")
                return
            build_name, version = self.ask_for_version()
            create_or_stay(G.local + "/home/" + profile)
            with open(G.local + "/home/" + profile + "/profile.json", mode="w") as f:
                json.dump({"profile": profile, "version": version, "build": build_name}, f)
            self.download_version(build_name)
            print("updated profile!")
        else:
            print("invalid input '{}'!".format(a))

    def generate_new(self, profile_name: str):
        if os.path.exists(G.local+"/home/"+profile_name):
            print("profile exists! would you like to override it? (y/n)")
            a = input().lower()
            if a == "y":
                shutil.rmtree(G.local+"/home/"+profile_name)
            else:
                sys.exit(-1)
        build_name, version = self.ask_for_version()
        create_or_stay(G.local+"/home/"+profile_name)
        with open(G.local+"/home/"+profile_name+"/profile.json", mode="w") as f:
            json.dump({"profile": profile_name, "version": version, "build": build_name}, f)
        self.download_version(build_name)

    def ask_for_version(self):
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
        return builds[int(input("build number: ")) - 1], version

