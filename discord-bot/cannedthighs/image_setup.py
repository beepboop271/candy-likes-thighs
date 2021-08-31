# kept updated with files from https://github.com/Aceship/AN-EN-Tags
import glob
import json
import os
from typing import Dict, FrozenSet, List, Tuple

from PIL import Image

from cannedthighs.TaggedImage import TaggedImage


# avoid circular dependency between __init__ and this
# file by passing cannedthighs.conf as a param
def get_images(conf) -> List[TaggedImage]:
    # setup
    with open(
        conf.image_setup_file,
        encoding="utf-8",
    ) as _setup_data_file:
        _setup_data = json.load(_setup_data_file)
        # characters that are in the json file of characters
        # but should not be included
        EXCLUDE_CHAR_LIST: FrozenSet[str] = frozenset(_setup_data["excludeCharacterList"])
        # images that are in the character folder but are
        # only used in the story, not actual character images
        EXCLUDE_IMG_LIST: FrozenSet[str] = frozenset(_setup_data["excludeImageList"])
        # names that are written with the cyrillic alphabet
        # which need to be converted to latin
        TRANSLATION_OVERRIDES: Dict[str, str] = _setup_data["translationOverrides"]

    with open(conf.alias_file, encoding="utf-8") as _alias_file:
        ALIASES: Dict[str, Tuple[str, ...]] = json.load(_alias_file)

    # load translations
    TRANSLATIONS: Dict[str, str] = {}

    with open(
        conf.translation_file,
        encoding="utf-8",
    ) as translation_file:
        characters = json.load(translation_file)

    for char in characters:
        cn_name = char["name_cn"]
        # tl-akhr translates to the cyrillic,
        # so override to get latin alphabet
        if cn_name in TRANSLATION_OVERRIDES:
            TRANSLATIONS[cn_name] = TRANSLATION_OVERRIDES[cn_name]
        else:
            # some chinese names are written in latin characters
            # e.g. Lancet-2, so lowercase it. lowercase the en
            # names too so that everything is stored lowercase
            TRANSLATIONS[cn_name.lower()] = char["name_en"].lower()

    # load images
    images: List[TaggedImage] = []

    def _load_character(char_id: str, cn_name: str) -> bool:
        en_name = TRANSLATIONS.get(cn_name)
        # there are some objects in the data file
        # which are not actual characters. these objects
        # will not have any corresponding images or
        # translation, so don't bother trying to load them.
        if en_name is None:
            return False
        if en_name in EXCLUDE_CHAR_LIST:
            return False

        aliases = ALIASES.get(en_name)
        if aliases is None:
            # data files are automatically updated, while
            # alias file is not, so warn when the alias file
            # is out of date
            print(f"missing alias entry for {en_name}")
            aliases = ()

        num_loaded = 0
        for img_path in glob.glob(f"{conf.image_path}/{char_id}*"):
            if os.path.basename(img_path) not in EXCLUDE_IMG_LIST:
                images.append(TaggedImage(
                    Image.open(img_path),
                    en_name, cn_name, *aliases,
                ))
                num_loaded += 1
        return num_loaded > 0

    with open(
        conf.character_list_file,
        encoding="utf-8",
    ) as data_file:
        characters = json.load(data_file)

    loaded = set()
    for char_id, char in characters.items():
        if _load_character(char_id, char["name"].lower()):
            loaded.add(char_id)

    for img_path in glob.glob(f"{conf.image_path}/*"):
        name = os.path.basename(img_path)
        # char_1234_abcd_...
        # ^^^^^^^^^^^^^^
        if name[:name.index("_", name.index("_", 5)+1)] not in loaded:
            print(f"skipped {name}")

    print(f"{len(images)} images parsed")

    if conf.preload_images:
        for img in images:
            img.image.load()
        print("all images loaded")

    return images
