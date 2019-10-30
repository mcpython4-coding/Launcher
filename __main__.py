import globals as G
import launcher.download
import launcher.launch

launcher.download.download_index()


if __name__ == "__main__":
    launcher.launch.launch_version("active_latest")

