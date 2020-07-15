import os
import launcher.globalstorage as G
import launcher.Launcher
import sys
import shutil
import time


if __name__ == "__main__":
    launcher.Launcher.setup()
    instance = launcher.Launcher.Launcher()
    if "--launch-profile" in sys.argv:
        instance.launch_profile(launcher.Launcher.Profile(G.local+"/home/{}".format(
            sys.argv[sys.argv.index("--launch-profile")+1])), *sys.argv[sys.argv.index("--launch-profile")+2:])
    else:
        instance.load_index()
        while True:
            instance.ask_user()


