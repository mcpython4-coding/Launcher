import launcher.globalstorage as G
import urllib.request
import zipfile
import json
import sys
import os
import subprocess
import shutil
import time


def create_or_skip(name: str):
    if not os.path.exists(name): os.makedirs(name)


def setup():
    create_or_skip(G.local + "/versions")
    create_or_skip(G.local + "/home")
    if "--delete-cache" in sys.argv:
        for folder in os.listdir(G.local + "/home"):
            if folder.startswith("cache"):
                shutil.rmtree(G.local + "/home/" + folder)
        sys.exit(-1)
    if "--delete-versions" in sys.argv:
        shutil.rmtree(G.local + "/versions")
        sys.exit(-1)
    if "--delete-all" in sys.argv:
        a = input("you are going to loose ALL your data, are your sure to continue? (y/n) ").lower().strip()
        if a == "y":
            print("you have 5 sec to interrupt the process, than all data will get lost")
            time.sleep(5)
        shutil.rmtree(G.local + "/home")
        shutil.rmtree(G.local + "/versions")
        sys.exit(-1)


def create_or_stay(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)


def download_file(url, dest):
    urllib.request.urlretrieve(url, dest)


INDEX_VERSION = "1.2.0"


def download_index(url="https://raw.githubusercontent.com/mcpython4-coding/Index/master/core.json"):
    download_file(url, G.local + "/versions/index.json")
    try:
        with open(G.local + "/versions/index.json") as f:
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


class Profile:
    @classmethod
    def new(cls, path: str, version_path_or_instance, name: str):
        if os.path.exists(path):
            print("profile exists! would you like to override it? (y/n)")
            a = input().lower()
            if a == "y":
                shutil.rmtree(path)
            else:
                sys.exit(-1)
        if type(version_path_or_instance) == str:
            version = Version.from_path(version_path_or_instance)
        else:
            version = version_path_or_instance

        profile_data = {"profile_name": name, "version_path": version.path, "dev": version.dev_env,
                        "console_args": []}

        version.download()

        create_or_stay(path)

        with open(path + "/profile.json", mode="w") as f:
            json.dump(profile_data, f)

        return cls(G.local+"/home/{}".format(name))

    @classmethod
    def user_selects(cls):
        profiles = os.listdir(G.local + "/home")
        print("the following profiles were found: ")
        [print("[{}]: {}".format(i + 1, e)) for i, e in enumerate(profiles)]
        a = input("select profile: ")
        try:
            return Profile(G.local+"/home/"+profiles[int(a) - 1]) if a not in profiles else Profile(G.local+"/home/"+a)
        except ValueError:
            print("invalid answer!")

    def __init__(self, path: str):
        if not os.path.exists(path + "/profile.json"):
            raise IOError("profile definition not found at '{}'!".format(path))

        with open(path + "/profile.json") as f:
            data = json.load(f)

        self.version: Version = Version.from_path(data["version_path"], dev_env=data["dev"])
        self.name = data["profile_name"]
        self.path: str = path
        self.runtime_args = data["console_args"] if "console_args" in data else []

    def __eq__(self, other):
        if type(self) == type(other):
            return self.path == other.path
        elif type(other) == str:
            return self.path == other
        else:
            raise NotImplementedError()

    def __hash__(self):
        return hash((self.path, self.version))

    def change_game_version(self, version):
        with open(self.path + "/profile.json") as f:
            data = json.load(f)
        data["version_path"] = version.path
        version.download()
        with open(self.path + "/profile.json", mode="w") as f:
            json.dump(data, f)

    def launch(self, *args):
        print("LOADING VERSION {} OF MCPYTHON 4".format(self.version.name))
        self.version.download()

        DATA = self.path + "/data"
        CACHE = self.path + "/cache"
        MODS = self.path + "/mods"
        SAVES = self.path + "/saves"

        create_or_stay(DATA)
        create_or_stay(CACHE)
        create_or_stay(MODS)
        create_or_stay(SAVES)

        flag = False
        if os.path.exists(G.local + "/config.json"):
            with open(G.local + "/config.json") as f:
                data = json.load(f)
            flag = "latest_version" in data and data["latest_version"] == self.version.name

        if not flag:
            # todo: store requirements somewhere else & link dynamically
            print("installing requirements...")
            subprocess.call(["py", "-{}.{}".format(sys.version_info[0], sys.version_info[1]),
                             self.version.path + "/installer.py"], stderr=sys.stderr,
                            stdout=sys.stdout)

        with open(G.local + "/config.json", mode="w") as f:
            json.dump({"latest_version": self.version.name}, f)

        args = list(args)

        if self.version.dev_env:
            args = ["--data-gen"] + args
        subprocess.call(["py", "-{}.{}".format(sys.version_info[0], sys.version_info[1]),
                         self.version.path + "/__main__.py", "--home-folder", DATA, "--build-folder", CACHE,
                         "--addmoddir", MODS, "--saves-directory", SAVES] + args + self.runtime_args)


class Version:
    @classmethod
    def user_selects(cls):
        print("the following versions where found: ")
        v = list(LAUNCHER.index["builds"].keys())
        v.sort()
        for i, path in enumerate(LAUNCHER.local_config):
            print("[{}]: local dev environment at {}".format(i + 1, path))
        for i, version in enumerate(v):
            print("[{}]: {}".format(i + 1 + len(LAUNCHER.local_config), version))
        i = int(input("select version number: ")) - 1
        if i >= len(LAUNCHER.local_config):
            i -= len(LAUNCHER.local_config)
            version = v[i]
            builds = LAUNCHER.index["builds"][version]
            builds.sort()
            print("the following builds were found: ")
            for i, build in enumerate(builds):
                print("[{}] {}".format(i + 1, build))
            i = int(input("build number: ")) - 1
            name = builds[i]
            version = cls.new(G.local+"/versions/{}".format(name), name)
            return version
        else:
            return Version(LAUNCHER.local_config[i], dev_env=True)

    @classmethod
    def new(cls, path: str, name: str):
        if os.path.exists(path): return cls.from_path(path)
        version_data = {"build": name}
        create_or_stay(path)
        with open(path+"/version_launcher.json", mode="w") as f:
            json.dump(version_data, f)
        return cls.from_path(path)

    @classmethod
    def from_path(cls, path: str, dev_env=False):
        return cls(path, dev_env=dev_env)

    def __init__(self, path: str, dev_env=False):
        if not dev_env:
            if not os.path.exists(path+"/version_launcher.json"):
                raise IOError("version folder invalid!")
            with open(path+"/version_launcher.json") as f:
                data = json.load(f)
            self.name = data["build"]
        else:
            self.name = path
        self.path = path
        self.dev_env = dev_env

    def __eq__(self, other):
        if type(self) == type(other):
            return self.name == other.name
        elif type(other) == str:
            return self.name == other
        else:
            raise NotImplementedError()

    def __hash__(self):
        return hash((self.name, self.path, self.dev_env))

    def download(self):
        version_data = {"build": self.name}
        create_or_stay(self.path)
        with open(self.path + "/version_launcher.json", mode="w") as f:
            json.dump(version_data, f)
        if self.dev_env: return
        file = self.path + ".zip"
        if os.path.exists(file): return
        print("downloading...")
        if not os.path.exists(file):
            download_file("https://github.com/mcpython4-coding/Index/blob/master/builds/build_{}.zip?raw=true,".format(
                self.name), file)
        i = 1
        with zipfile.ZipFile(file) as f:
            names = f.namelist()
            total = len(names)
            for element in names:
                print("\rextracting {}/{}: {}".format(i, total, element), end="")
                r = os.path.join(self.path, element)
                create_or_stay(os.path.dirname(r))
                with open(r, mode="wb") as fw:
                    fw.write(f.read(element))
                i += 1
        print("\nfinished!")


class Launcher:
    def __init__(self):
        global LAUNCHER
        LAUNCHER = self

        create_or_stay(G.local + "/shared_mods")

        self.index = None

        self.local_versions = []
        self.profiles = []
        self.versions = []

        if os.path.exists(G.local + "/locals.json"):
            with open(G.local + "/locals.json") as f:
                data = json.load(f)

            self.local_config = data["core_dev"]

    def load_index(self):
        self.index = download_index()

    def launch_profile(self, profile: Profile, *args):
        profile.launch(*args)

    def ask_user(self):
        print("would you like to a) run an existing profile, b) create an new profile or c) edit profile"
              "of an profile?")
        a = input().lower().strip()
        if a == "a":
            self.launch_profile(Profile.user_selects())
        elif a == "b":
            name = input("profile name: ")
            profile = Profile.new(G.local + "/home/{}".format(name), Version.user_selects(), name)
            a = input("would you like to start the profile now? (y/n) ").lower().strip()
            if a == "y":
                self.launch_profile(profile)
        elif a == "c":
            profile = Profile.user_selects()
            if profile is None:
                print("you have to first create the profile before you can edit it")
                return
            while True:
                print("would you like to a) edit the version of the game based on b) re-download version "
                      "(any other to exit)")
                a = input().lower().strip()
                if a == "a":
                    version = Version.user_selects()
                    profile.change_game_version(version)
                    print("updated profile!")
                elif a == "b":
                    if profile.version.dev_env:
                        print("dev-profiles can not be re-downloaded!")
                        continue
                    print("removing old data...")
                    shutil.rmtree(profile.version.path)
                    os.remove(profile.version.path+".zip")
                    print("finished!")
                    profile.version.download()
                else:
                    break
        else:
            print("invalid input '{}'!".format(a))


LAUNCHER: Launcher = None
