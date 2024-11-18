import viktor as vkt


def moment_end_plate_check(frame_con_capacity: dict, section_name: str, report_item: any, capacity: str, load: dict):
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

    found_break = False
    for node, list_load in load.items():
        for load_item in list_load:
            M1 = load_item["M1"]
            F3 = load_item["F3"]
            # Record loads
            report_item.M = abs(M1)
            report_item.V = abs(F3)
            report_item.Vn = Shear
            # Check compliance
            if M1 <= 0:
                if abs(F3) < Shear and abs(M1) < MomentBottom:
                    color = vkt.Color(r=0, g=200, b=0)
                    report_item.check = "MomentBottom"
                    report_item.Mn = MomentTop

                else:
                    color = vkt.Color(r=200, g=0, b=0)
                    report_item.Mn = MomentBottom
                    report_item.check = "Not ok"
                    found_break = True
                    break
            elif M1 > 0:
                if abs(F3) < Shear and abs(M1) < MomentTop:
                    color = vkt.Color(r=0, g=200, b=0)
                    report_item.check = "ok"
                    report_item.Mn = MomentTop
                else:
                    color = vkt.Color(r=200, g=0, b=0)
                    report_item.check = "Not ok"
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
    if frame_con_capacity[section_name].get(capacity):
        Shear = frame_con_capacity[section_name][capacity]["Shear"]

        found_break = False
        for node, list_load in load.items():
            for load_item in list_load:
                F3 = load_item["F3"]
                report_item.V = abs(F3)
                report_item.Vn = Shear

                if abs(F3) < Shear:
                    color = vkt.Color(r=0, g=200, b=0)
                    report_item.check = "ok"
                else:
                    color = vkt.Color(r=200, g=0, b=0)
                    report_item.check = "Not ok"
                    found_break = True  # Set the flag to True
                    break  # Break the inner loop
            if found_break:
                break
    else:
        color = vkt.Color(r=200, g=0, b=0)
        report_item.check = "Not ok"

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

                    if abs(F3) < axial and ultimate_shear < shear:
                        color = vkt.Color(r=0, g=200, b=0)
                        report_item.check = "ok"
                    else:
                        color = vkt.Color(r=200, g=0, b=0)
                        report_item.check = "Not ok"

                        found_break = True
                        break

            if found_break:
                break
    else:
        color = vkt.Color(r=200, g=0, b=0)
        report_item.check = "Not ok"
    return color, report_item
