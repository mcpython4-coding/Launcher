import os
import launcher.download
import globalstorage as G
import zipfile
import shutil
import sys
import subprocess


def extract_version(file, output, delete_previous=True):
    if os.path.exists(output) and delete_previous:
        print("deleting old output...")
        shutil.rmtree(output)
        os.makedirs(output)
    print("extracting data...")
    with zipfile.ZipFile(file) as f:
        for file in f.namelist():
            if not file.endswith("/"):
                o = output+"/"+"/".join(file.split("/")[1:])
                d = os.path.dirname(o)
                if not os.path.exists(d): os.makedirs(d)
                with f.open(file, mode="r") as ff, open(o, mode="wb") as fw:
                    fw.write(ff.read())
    print("finished!")


def modify(modifications, path):
    for moddata in modifications:
        if moddata["mode"] == "remove":
            shutil.rmtree(path+"/"+moddata["path"])
        elif moddata["mode"] == "copy":
            shutil.move(moddata["path"].format(v=path, home=G.local), moddata["to"].format(v=path, home=G.local))


def launch_version(name: str, redownload=False, reextract=False, args=[]):
    if name in launcher.download.DATA:
        if "link" in launcher.download.DATA[name]:
            name = launcher.download.DATA[name]["link"]
    launcher.download.download_index()
    home = G.local + "/versions/version_{}".format(name)
    if not os.path.exists(home+".zip".format(name)) or redownload:
        launcher.download.download_by_name(name)
    if not os.path.exists(home) or redownload or reextract:
        extract_version(home+".zip", home)
        if "modifications" in launcher.download.DATA[name]:
            modify(launcher.download.DATA[name]["modifications"], G.local+"/versions/version_{}".format(name))
    if os.path.exists(home+"/requirements.txt"):
        subprocess.call("py -{}.{} -m pip install -r {}".format(sys.version_info[0], sys.version_info[1],
                                                                home+"/requirements.txt"))
    sys.path.append(G.local+"/versions/version_{}".format(name))
    subprocess.call(["py", "-{}.{}".format(sys.version_info[0], sys.version_info[1]),
                     home+"/{}".format(launcher.download.DATA[name]["main"])]+
                    ["--addmoddir {}".format(G.local+"/mods")]+args)

