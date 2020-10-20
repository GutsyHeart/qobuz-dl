import argparse
import json
import os
import re
import sys

from pick import pick

import qopy
from qo_utils import downloader
from qo_utils.search import Search


def getArgs():
    parser = argparse.ArgumentParser(prog="python3 main.py")
    parser.add_argument("-a", action="store_true", help="enable albums-only search")
    parser.add_argument(
        "-i", action="store_true", help="run Qobuz-DL on URL input mode"
    )
    parser.add_argument(
        "-q",
        metavar="int",
        default=6,
        help="quality (5, 6, 7, 27) [320, FLAC, 24b<=96, 24b>=96] (default: 6)",
    )
    parser.add_argument(
        "-l",
        metavar="int",
        default=10,
        help="limit of search results by type (default: 10)",
    )
    parser.add_argument(
        "-d",
        metavar="PATH",
        default="Qobuz Downloads",
        help="custom directory for downloads (default: current directory)",
    )
    return parser.parse_args()


def getSession():
    print("Logging...")
    with open("config.json") as f:
        config = json.load(f)
    return qopy.Client(config["email"], config["password"])


def musicDir(dir):
    fix = os.path.normpath(dir)
    if not os.path.isdir(fix):
        os.mkdir(fix)
    return fix


def get_id(url):
    return re.match(
        r"https?://(?:w{0,3}|play|open)\.qobuz\.com/(?:(?"
        ":album|track)/|[a-z]{2}-[a-z]{2}/album/-?\w+(?:-\w+)"
        "*-?/|user/library/favorites/)(\w+)",
        url,
    ).group(1)


def searchSelected(Qz, path, albums, ids, types, quality):
    q = ["5", "6", "7", "27"]
    quality = q[quality[1]]
    for alb, id_, type_ in zip(albums, ids, types):
        for al in alb:
            if type_[al[1]]:
                downloader.iterateIDs(Qz, id_[al[1]], path, quality, True)
            else:
                downloader.iterateIDs(Qz, id_[al[1]], path, quality, False)


def fromUrl(Qz, path, link, quality):
    if "/track/" in link:
        id = get_id(link)
        downloader.iterateIDs(Qz, id, path, quality, False)
    else:
        id = get_id(link)
        downloader.iterateIDs(Qz, id, path, quality, True)


def interactive(Qz, path, limit, tracks=True):
    while True:
        Albums, Types, IDs = [], [], []
        try:
            while True:
                query = input("\nEnter your search: [Ctrl + c to quit]\n- ")
                print("Searching...")
                start = Search(Qz, query, limit)
                start.getResults(tracks)
                Types.append([t["is_album"] for t in start.Total])
                IDs.append([i["id"] for i in start.Total])

                title = (
                    "Select [space] the item(s) you want to download "
                    "(one or more)\nPress Ctrl + c to quit\n"
                )
                Selected = pick(
                    [i["release_info"] for i in start.Total],
                    title,
                    multiselect=True,
                    min_selection_count=1,
                )
                Albums.append(Selected)

                y_n = pick(
                    ["Yes", "No"],
                    "Items were added to queue to " "be downloaded. Keep searching?",
                )
                if y_n[0][0] == "N":
                    break
            desc = (
                "Select [intro] the quality (the quality will be automat"
                "ically\ndowngraded if the selected is not found)"
            )
            Qualits = ["320", "Lossless", "Hi-res =< 96kHz", "Hi-Res > 96 kHz"]
            quality = pick(Qualits, desc)
            searchSelected(Qz, path, Albums, IDs, Types, quality)
        except KeyboardInterrupt:
            sys.exit("\nBye")


def inputMode(Qz, path, quality):
    while True:
        try:
            link = input("\nAlbum/track URL: [Ctrl + c to quit]\n- ")
            fromUrl(Qz, path, link, quality)
        except KeyboardInterrupt:
            sys.exit("\nBye")


def main():
    arguments = getArgs()
    directory = musicDir(arguments.d) + "/"
    Qz = getSession()
    if not arguments.i:
        if arguments.a:
            interactive(Qz, directory, arguments.l, False)
        else:
            interactive(Qz, directory, arguments.l, True)
    else:
        inputMode(Qz, directory, arguments.q)


if __name__ == "__main__":
    sys.exit(main())
