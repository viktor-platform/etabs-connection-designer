import viktor as vkt
from app.core.render import get_color_for_ratio


def moment_end_plate_check(
    frame_con_capacity: dict, section_name: str, report_item: any, capacity: str, load: dict, axis: str
):
    """
    Arguments:
    - frame_con_capacity: Requires `section_name` and `capacity` for Shear, MomentTop, and MomentBottom.
    - section_name: Key for frame strength.
    - report_item: Used for output reporting.
    - capacity: Key for shear and moment strength.
    - load: Contains force/moment components (F1, F2, F3, M1, M2, M3).
    """
    report_item.section_name = section_name

    Shear = frame_con_capacity[section_name][capacity]["Shear"]

    MomentTop = frame_con_capacity[section_name][capacity]["MomentTop"]
    MomentBottom = frame_con_capacity[section_name][capacity]["MomentBottom"]
    global_M = 0
    global_S = 0
    global_capacity_ratio = 0 # ensure we report the max between to frame ends

    found_break = False
    for node, list_load in load.items():
        for load_item in list_load:
            gloab_load_dict = transform_global_to_local(load_item, axis)
            M3 = gloab_load_dict["M3"]
            V2 = gloab_load_dict["V2"]
            # Record loads
            if global_M < abs(M3):
                global_M = abs(M3)
                report_item.M = abs(M3)
            if global_S < abs(V2):
                global_S = abs(V2)
                report_item.Vn = Shear

            # Check compliance
            if M3 <= 0:
                if abs(V2) < Shear and abs(M3) < MomentBottom:
                    report_item.check = "MomentBottom"
                    report_item.Mn = MomentTop
                    capacity_ratio = max([abs(V2) / Shear, abs(M3) / MomentBottom])
                    if global_capacity_ratio < capacity_ratio:
                        global_capacity_ratio = capacity_ratio
                        report_item.capacity_ratio = capacity_ratio
                        color = get_color_for_ratio(report_item.capacity_ratio)
                else:
                    report_item.Mn = MomentBottom
                    report_item.check = "Not OK"
                    found_break = True
                    capacity_ratio = max([abs(V2) / Shear, abs(M3) / MomentBottom])
                    report_item.capacity_ratio = max([abs(V2) / Shear, abs(M3) / MomentBottom])
                    color = get_color_for_ratio(report_item.capacity_ratio)
                    break

            elif M3 > 0:
                if abs(V2) < Shear and abs(M3) < MomentTop:
                    capacity_ratio = max([abs(V2) / Shear, abs(M3) / MomentTop])
                    if global_capacity_ratio < capacity_ratio:
                        global_capacity_ratio = capacity_ratio
                        report_item.capacity_ratio = capacity_ratio
                        color = get_color_for_ratio(report_item.capacity_ratio)
                        report_item.check = "OK"
                        report_item.Mn = MomentTop

                else:
                    report_item.capacity_ratio = max([abs(V2) / Shear, abs(M3) / MomentTop])
                    color = get_color_for_ratio(report_item.capacity_ratio)
                    report_item.check = "Not OK"
                    report_item.Mn = MomentTop
                    found_break = True
                    break
        if found_break:
            break

    return color, report_item


def web_cope(frame_con_capacity: dict, section_name: str, report_item: any, capacity: str, load: dict):
    """
    Arguments:
    - frame_con_capacity: Requires `section_name` and `capacity` for Shear.
    - section_name: Key for frame strength.
    - report_item: Used for output reporting.
    - capacity: Key for shear and moment strength.
    - load: Contains force/moment components (F1, F2, F3, M1, M2, M3).
    """
    report_item.section_name = section_name
    global_shear = 0
    if frame_con_capacity[section_name].get(capacity):
        Shear = frame_con_capacity[section_name][capacity]["Shear"]

        found_break = False
        for node, list_load in load.items():
            for load_item in list_load:
                F3 = load_item["F3"]
                report_item.Vn = Shear
                report_item.V = abs(F3)

                if global_shear > abs(F3):
                    global_shear = abs(F3)
                    report_item.V = abs(F3)
                    report_item.capacity_ratio = abs(F3) / Shear

                if abs(F3) < Shear:
                    capacity_ratio = abs(F3) / Shear
                    report_item.capacity_ratio = capacity_ratio

                    color = get_color_for_ratio(report_item.capacity_ratio)
                    report_item.check = "OK"
                else:
                    capacity_ratio = abs(F3) / Shear
                    report_item.capacity_ratio = capacity_ratio
                    color = get_color_for_ratio(report_item.capacity_ratio)
                    report_item.check = "Not OK"
                    found_break = True  # Set the flag to True
                    break  # Break the inner loop
            if found_break:
                break
    else:
        color = vkt.Color(r=200, g=0, b=0)
        report_item.check = "Not OK"

    return color, report_item


def base_plate(frame_con_capacity: dict, section_name: str, report_item: any, capacity: str, load: dict, nodes: dict):
    """
    Arguments:
    - frame_con_capacity: Requires `section_name` and `capacity` for Shear.
    - section_name: Key for frame strength.
    - report_item: Used for output reporting.
    - capacity: Key for shear and moment strength.
    - load: Contains force/moment components (F1, F2, F3, M1, M2, M3).
    - nodes: Contains node coordinates
    """
    report_item.section_name = section_name
    if frame_con_capacity[section_name].get(capacity):

        shear = frame_con_capacity[section_name][capacity]["Shear"]
        axial = frame_con_capacity[section_name][capacity]["Axial"]

        found_break = False  # Flag to indicate when to break the outer loop
        for node, list_load in load.items():
            for load_item in list_load:
                if nodes[node]["z"] == 0:
                    F1 = load_item["F1"]
                    F2 = load_item["F2"]
                    F3 = load_item["F3"]

                    ultimate_shear = max([abs(F1), abs(F2)])

                    report_item.P = abs(F3)
                    report_item.V = abs(ultimate_shear)
                    report_item.Pn = axial
                    report_item.Vn = shear

                    report_item.capacity_ratio = max([abs(F3) / axial, abs(ultimate_shear) / shear])
                    color = get_color_for_ratio(report_item.capacity_ratio)
                    if abs(F3) < axial and ultimate_shear < shear:
                        report_item.check = "OK"
                    else:
                        report_item.check = "Not OK"

                        found_break = True
                        break

            if found_break:
                break
    else:
        color = vkt.Color(r=200, g=0, b=0)
        report_item.check = "Not OK"
    return color, report_item


def get_alignment(lines: dict, nodes: dict, frame_id: int) -> str:
    node_id_i = lines[frame_id]["nodeI"]
    node_id_j = lines[frame_id]["nodeJ"]
    node_i = nodes[node_id_i]
    node_j = nodes[node_id_j]

    is_x_axis = (node_i["y"] == node_j["y"]) and (node_i["z"] == node_j["z"])
    is_y_axis = (node_i["x"] == node_j["x"]) and (node_i["z"] == node_j["z"])
    if is_x_axis:
        dir_axis = node_j["x"] - node_i["x"]
        if dir_axis > 0:
            return "+X"
        else:
            return "-X"
    elif is_y_axis:
        dir_axis = node_j["y"] - node_i["y"]
        if dir_axis > 0:
            return "+Y"
        else:
            return "-Y"


def transform_global_to_local(load_item, alignment):
    """
    Transforms global forces to local forces for beams aligned along the global X or Y axis.
    - load_item: Dictionary containing global forces and moments with keys 'F1', 'F2', 'F3', 'M1', 'M2', 'M3'.
    - alignment: String indicating beam alignment, either 'X' or 'Y'.
    Returns:
    - Dictionary containing local forces and moments: 'P', 'V2', 'V3', 'T', 'M2', 'M3'.
    """
    F1 = load_item["F1"]
    F2 = load_item["F2"]
    F3 = load_item["F3"]
    M1 = load_item["M1"]
    M2 = load_item["M2"]
    M3 = load_item["M3"]

    if alignment == "+Y":
        P = F2
        V2 = F3
        V3 = F1
        T = M3
        M2_local = M2
        M3_local = M1  # this sign needs checking
    elif alignment == "+X":
        P = F2
        V2 = F3
        V3 = -F1  # this sign needs checking
        T = M2
        M2_local = M1
        M3_local = M2  # this sign needs checking
    else:
        raise ValueError("Invalid alignment. Alignment must be 'X' or 'Y'.")

    return {"P": P, "V2": V2, "V3": V3, "T": T, "M2": M2_local, "M3": M3_local}
