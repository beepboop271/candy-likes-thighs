import json

with open("../../../AN-EN-Tags/json/gamedata/zh_CN/gamedata/excel/character_table.json", encoding="utf-8") as f:
    chars = json.load(f)
with open("../../../AN-EN-Tags/json/tl-akhr.json", encoding="utf-8") as f:
    tl = json.load(f)

with open("image_setup.json", encoding="utf-8") as f:
    overrides = json.load(f)
with open("name_aliases.json", encoding="utf-8") as f:
    aliases = json.load(f)

tls = {}

for char in tl:
    cn_name = char["name_cn"]
    if cn_name in overrides["translationOverrides"]:
        tls[cn_name] = overrides["translationOverrides"][cn_name]
    else:
        tls[cn_name.lower()] = char["name_en"].lower()

data = {}

for char_id, char in chars.items():
    en_name = tls.get(char["name"].lower())
    if en_name is None or en_name in overrides["excludeCharacterList"]:
        continue

    data[char_id] = {
        "en_name": en_name,
        "aliases": aliases.get(en_name, []),
    }

with open("ak_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
