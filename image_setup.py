# kept updated with files from https://github.com/Aceship/AN-EN-Tags
import json
import glob
from typing import List, Dict

from PIL import Image

from TaggedImage import TaggedImage


DATA_PATH = "../../AN-EN-Tags"

EXCLUDE_LIST = set((
    "char_002_amiya_summer_1.png",
    "char_010_chen_summer.png",
    "char_107_liskam_nian#1.png",
    "char_235_jesica_nian#1.png",
    "char_284_spot_otaku#1.png",
))

images: List[TaggedImage] = []

translated: Dict[str, str] = {}

with open(
    f"{DATA_PATH}/json/tl-akhr.json",
    encoding="utf-8",
) as translation_file:
    translation = json.load(translation_file)
    for char in translation:
        translated[char["name_cn"]] = char["name_en"]

with open(
    f"{DATA_PATH}/json/gamedata/zh_CN/gamedata/excel/character_table.json",
    encoding="utf-8",
) as data_file:
    data = json.load(data_file)
    for key in data.keys():
        for path in glob.glob(f"{DATA_PATH}/img/characters/{key}*"):
            if path.rsplit("\\", 1)[1] not in EXCLUDE_LIST:
                im = Image.open(path)
                images.append(TaggedImage(im, translated[data[key]["name"]]))

print(f"{len(images)} images loaded")
