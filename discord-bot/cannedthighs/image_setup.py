# kept updated with files from https://github.com/Aceship/AN-EN-Tags
import glob
import json
import os
from typing import Dict, FrozenSet, List, Tuple

from PIL import Image

import cannedthighs
from cannedthighs.TaggedImage import TaggedImage


with open(
    cannedthighs.conf.image_setup_file,
    encoding="utf-8",
) as _setup_data_file:
    _setup_data = json.load(_setup_data_file)
    # characters that are in the json file of characters
    # but should not be included
    _EXCLUDE_CHAR_LIST: FrozenSet[str] = frozenset(_setup_data["excludeCharacterList"])
    # images that are in the character folder but are
    # only used in the story, not actual character images
    _EXCLUDE_IMG_LIST: FrozenSet[str] = frozenset(_setup_data["excludeImageList"])
    # names that are written with the cyrillic alphabet
    # which need to be converted to latin
    _TRANSLATION_OVERRIDES: Dict[str, str] = _setup_data["translationOverrides"]

with open(cannedthighs.conf.alias_file, encoding="utf-8") as _alias_file:
    _ALIASES: Dict[str, Tuple[str, ...]] = json.load(_alias_file)

_TRANSLATIONS: Dict[str, str] = {}

images: List[TaggedImage] = []


def _load_translations() -> None:
    with open(
        cannedthighs.conf.translation_file,
        encoding="utf-8",
    ) as translation_file:
        characters = json.load(translation_file)

    for char in characters:
        cn_name = char["name_cn"]
        # tl-akhr translates to the cyrillic,
        # so override to get latin alphabet
        if cn_name in _TRANSLATION_OVERRIDES:
            _TRANSLATIONS[cn_name] = _TRANSLATION_OVERRIDES[cn_name]
        else:
            # some chinese names are written in latin characters
            # e.g. Lancet-2, so lowercase it. lowercase the en
            # names too so that everything is stored lowercase
            _TRANSLATIONS[cn_name.lower()] = char["name_en"].lower()


def _load_character(char_id: str, cn_name: str) -> None:
    en_name = _TRANSLATIONS.get(cn_name)
    # there are some objects in the data file
    # which are not actual characters. these objects
    # will not have any corresponding images or
    # translation, so don't bother trying to load them.
    if en_name is None:
        return
    if en_name in _EXCLUDE_CHAR_LIST:
        return

    aliases = _ALIASES.get(en_name)
    if aliases is None:
        # data files are automatically updated, while
        # alias file is not, so warn when the alias file
        # is out of date
        print(f"missing alias entry for {en_name}")
        aliases = ()

    for img_path in glob.glob(f"{cannedthighs.conf.image_path}/{char_id}*"):
        if os.path.basename(img_path) not in _EXCLUDE_IMG_LIST:
            images.append(TaggedImage(
                Image.open(img_path),
                en_name, cn_name, *aliases,
            ))


def _load_images() -> None:
    with open(
        cannedthighs.conf.character_list_file,
        encoding="utf-8",
    ) as data_file:
        characters = json.load(data_file)

    for char_id, char in characters.items():
        _load_character(char_id, char["name"].lower())

    print(f"{len(images)} images parsed")

    if cannedthighs.conf.preload_images:
        for img in images:
            img.image.load()
        print("all images loaded")


_load_translations()
_load_images()
