# kept updated with files from https://github.com/Aceship/AN-EN-Tags
import glob
import json
import os
from typing import Dict, List, Set, Tuple

from PIL import Image

from cannedthighs.TaggedImage import TaggedImage


DATA_PATH = "../../AN-EN-Tags"

EXCLUDE_LIST: Set[str] = set((
    "char_002_amiya_summer_1.png",
    "char_010_chen_summer.png",
    "char_107_liskam_nian#1.png",
    "char_235_jesica_nian#1.png",
    "char_284_spot_otaku#1.png",
))

TRANSLATION_OVERRIDE: Dict[str, str] = {
    "古米": "gummy",
    "真理": "istina",
    "早露": "rosa",
    "凛冬": "zima",
}

with open("name_aliases.json") as alias_file:
    MANUAL_ALIASES: Dict[str, Tuple[str, ...]] = json.load(alias_file)

images: List[TaggedImage] = []

translated: Dict[str, str] = {}

with open(
    f"{DATA_PATH}/json/tl-akhr.json",
    encoding="utf-8",
) as translation_file:
    translations = json.load(translation_file)
    for char in translations:
        # tl-akhr translates to the cyrillic, so override for the real english
        if char["name_cn"] in TRANSLATION_OVERRIDE:
            translated[char["name_cn"]] = TRANSLATION_OVERRIDE[char["name_cn"]]
        else:
            translated[char["name_cn"].lower()] = char["name_en"].lower()

with open(
    f"{DATA_PATH}/json/gamedata/zh_CN/gamedata/excel/character_table.json",
    encoding="utf-8",
) as data_file:
    data = json.load(data_file)
    for char_id in data.keys():
        try:
            cn_name = data[char_id]["name"].lower()
            en_name = translated[cn_name]
            try:
                aliases = MANUAL_ALIASES[en_name]
            except KeyError:
                # data files are automatically updated, while
                # alias file is not, so warn when the alias file
                # is out of date
                print(f"missing alias entry for {en_name}")
                aliases = ()
            for file_path in glob.glob(f"{DATA_PATH}/img/characters/{char_id}*"):
                if file_path.rsplit("\\", 1)[1] not in EXCLUDE_LIST:
                    im = Image.open(file_path)
                    images.append(TaggedImage(
                        im,
                        (en_name, cn_name, *aliases),
                    ))
        except KeyError:
            # if a KeyError is thrown, there wouldn't have been
            # any files returned by the glob, so do nothing
            pass

print(f"{len(images)} images parsed")

# non-lazy loading of images:
# pillow doesn't read the file until the image is actually used, which
# means the bot will slowly increase memory usage as more operators are
# shown. if you want to load all the images at the start, add a variable
# to the .env file called PRELOAD_IMAGES and set it to anything.
# note that it will take up about 2.8 gigs of ram to preload.
if os.getenv("PRELOAD_IMAGES") is not None:
    for img in images:
        img.image.load()

    print("all images loaded")
