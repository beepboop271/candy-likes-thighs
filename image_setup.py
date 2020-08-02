# kept updated with files from https://github.com/Aceship/AN-EN-Tags
import glob
import json
from typing import Dict, List, Set

from PIL import Image

from TaggedImage import TaggedImage


DATA_PATH = "../../AN-EN-Tags"

EXCLUDE_LIST: Set[str] = set((
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
    translations = json.load(translation_file)
    for char in translations:
        translated[char["name_cn"]] = char["name_en"]

with open(
    f"{DATA_PATH}/json/gamedata/zh_CN/gamedata/excel/character_table.json",
    encoding="utf-8",
) as data_file:
    data = json.load(data_file)
    for char_id in data.keys():
        char_name = translated[data[char_id]["name"]]
        for file_path in glob.glob(f"{DATA_PATH}/img/characters/{char_id}*"):
            if file_path.rsplit("\\", 1)[1] not in EXCLUDE_LIST:
                im = Image.open(file_path)
                images.append(TaggedImage(im, char_name))

print(f"{len(images)} images loaded")
