import json

connection_types = [
    "MEP 70%/35% (Moment/Shear)",
    "MEP 100%/50% (Moment/Shear)",
    "Base Plate 15%",
    "Base Plate 30%",
    "Base Plate 50%",
    "Base Plate 80%",
    "Web Cleat 30%",
    "Web Cleat 40%",
]


def load_json(file_path: str):
    with open(file_path) as jsonfile:
        data = json.load(jsonfile)
    return data


def gen_library():
    bp = load_json(r"app\library\db\bp_capacities.json")
    mep = load_json(r"app\library\db\mep_capacities.json")
    wcp = load_json(r"app\library\db\web_cope_capacities.json")

    return {"Web Cleat": wcp, "Moment End Plate": mep, "Base Plate": bp}
