import json
from pathlib import Path

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


def load_json(file_path: Path):
    with file_path.open() as jsonfile:
        data = json.load(jsonfile)
    return data


def gen_library():
    # Get the directory of the current script
    current_dir = Path(__file__).parent
    
    # Construct paths using Path
    bp_path = current_dir / "db" / "bp_capacities.json"
    mep_path = current_dir / "db" / "mep_capacities.json"
    wcp_path = current_dir / "db" / "web_cope_capacities.json"

    bp = load_json(bp_path)
    mep = load_json(mep_path)
    wcp = load_json(wcp_path)

    return {"Web Cleat": wcp, "Moment End Plate": mep, "Base Plate": bp}
