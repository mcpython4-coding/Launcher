import globalstorage as G
import launcher.download
import launcher.launch
import sys

launcher.download.download_index()


if __name__ == "__main__":
    # todo: make this sys.argv-based
    launcher.launch.launch_version("active_latest", args=sys.argv[1:])

