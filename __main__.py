import os
import launcher.globalstorage as G
import launcher.Launcher
import sys
import shutil
import time


if __name__ == "__main__":
    if not os.path.exists(G.local+"/home/versions"):
        os.makedirs(G.local+"/home/versions")
    if "--delete-cache" in sys.argv:
        for folder in os.listdir(G.local+"/home"):
            if folder.startswith("cache"):
                shutil.rmtree(G.local+"/home/"+folder)
        sys.exit(-1)
    if "--delete-versions" in sys.argv:
        shutil.rmtree(G.local + "/home/versions")
        sys.exit(-1)
    if "--delete-all" in sys.argv:
        a = input("you are going to loose ALL your data, are your sure to continue? (y/n) ").lower().strip()
        if a == "y":
            print("you have 5 sec to interrupt the process, than all data will get lost")
            time.sleep(5)
        shutil.rmtree(G.local+"/home")
        sys.exit(-1)
    instance = launcher.Launcher.Launcher()
    instance.ask_user()


