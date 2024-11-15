import viktor as vkt
from viktor.result import DownloadResult
from viktor.external.word import render_word_file, WordFileTag

import app.compliance_check as compliance_check
from app.models import (
    OutputItem,
    ReportData,
    ComplianceSummaryList,
    ConnectionSummaryList,
)
from app.parse_xlsx_files import get_entities,get_section_by_id
from app.render import render_model, colors_by_group
from app.library.load_db import gen_library

from app.parametrization import Parametrization
from pathlib import Path

# Global Variables
report = ReportData()
comp_summary_list = ComplianceSummaryList()
con_summary_list = ConnectionSummaryList()

# Controller
class Controller(vkt.Controller):
    label = "Structure Controller"

    parametrization = Parametrization

    @vkt.GeometryView("3D model", duration_guess=10, x_axis_to_right=True)
    def generate_structure(self, params, **kwargs):
        xlsx_file = params.step_1.csv_file
        file_content = xlsx_file.file.getvalue_binary()
        nodes, lines, groups, sections, load_combos = get_entities(file_content)

        # nodes, lines, groups, sections, load_combos = read_file(xlsx_file)[2]
        frame_by_group = {}
        groups_conn_props = {}
        for con_dict in params.step_1.connections:
            groups_conn_props.update(
                {
                    con_dict.groups: {
                        "color": con_dict.color,
                        "contype": con_dict.connection_type,
                    }
                }
            )
        # this avoid double assination of members of courser order matters! need checking
        frame_color_set = set()
        for group_name, group_vals in groups.items():
            for frames_in_groups in group_vals["frame_ids"]:
                if frames_in_groups not in frame_color_set:
                    if groups_conn_props.get(group_name):
                        frame_by_group.update(
                            {
                                frames_in_groups: {
                                    "material": vkt.Material(
                                        color=groups_conn_props[group_name]["color"]
                                    )
                                }
                            }
                        )
                    else:
                        frame_by_group.update(
                            {
                                frames_in_groups: {
                                    "material": vkt.Material(
                                        color=vkt.Color(r=40, g=40, b=40)
                                    )
                                }
                            }
                        )

                    frame_color_set.add(frames_in_groups)

            sections_group = render_model(
                sections=sections,
                lines=lines,
                nodes=nodes,
                frame_by_group=frame_by_group,
                color_function=colors_by_group,
            )
        # plotly_model(lines,nodes,{})
        return vkt.GeometryResult(sections_group)

    @vkt.GeometryView("3D model", duration_guess=10, x_axis_to_right=True)
    def connection_check(self, params, **kwargs):
        # Clear output for a new report
        report.clear()
        comp_summary_list.clear()
        con_summary_list.clear()
        #
        xlsx_file = params.step_1.csv_file.file
        file_content = xlsx_file.getvalue_binary()
        nodes, lines, groups, sections, load_combos = get_entities(file_content)
        frame_by_group = {}
        groups_conn_props = {}
        # Params.step_1.connections -> Dynamic array with Group Name, contype, color
        # this part just converts from Munch to a dictioanry with the keys bein Group Name
        for con_dict in params.step_1.connections:
            conn_props = {
                "color": con_dict.color,
                "contype": con_dict.connection_type,
            }
            if params.step_1.mode == "Connection Check":
                conn_props["capacity"] = con_dict.capacities
            groups_conn_props[con_dict.groups] = conn_props
        # db -> dictionary with keys equal to conntype Web Cope, Moment End Plate, Baseplate.
        # The vals are dicts with the main key being section name e.g
        # {"100UC14":{"15":{"Axial": 304.3, "Shear":55.89}}}
        db = gen_library()
        selected_lc = params.step_2.load_combos
        output_items = []

        if params.step_1.mode == "Connection Check":
            for group_name, group_vals in groups.items():
                frame_color_set = set()
                for frames_in_groups in group_vals["frame_ids"]:
                    if frames_in_groups not in frame_color_set:
                        color = None

                        if groups_conn_props.get(group_name):
                            frame_color_set.add(frames_in_groups)
                            # This match the DynamicArray content with the conn. db
                            cont_type = groups_conn_props[group_name]["contype"]
                            capacity = groups_conn_props[group_name]["capacity"]
                            section_name = get_section_by_id(sections, frames_in_groups)
                            frame_con_capacity = db[cont_type]
                            load = load_combos[frames_in_groups][selected_lc]

                            # Record for report
                            report_item = OutputItem()
                            report_item.frame_id = frames_in_groups
                            report_item.group_name = group_name
                            report_item.conn_type = cont_type
                            report_item.load_combo = selected_lc
                            report_item.section_name = section_name

                            if cont_type == "Moment End Plate":
                                color, report_item = (
                                    compliance_check.moment_end_plate_check(
                                        frame_con_capacity,
                                        section_name,
                                        report_item,
                                        capacity,
                                        load,
                                    )
                                )

                            if cont_type == "Web Cope":
                                color, report_item = compliance_check.web_cope(
                                    frame_con_capacity,
                                    section_name,
                                    report_item,
                                    capacity,
                                    load,
                                )

                            if cont_type == "Base Plate":
                                color, report_item = compliance_check.base_plate(
                                    frame_con_capacity,
                                    section_name,
                                    report_item,
                                    capacity,
                                    load,
                                    nodes,
                                )

                            # Stores item result for reporting
                            output_items.append(report_item)

                            if color:
                                frame_by_group.update(
                                    {
                                        frames_in_groups: {
                                            "material": vkt.Material(color=color)
                                        }
                                    }
                                )

            sections_group = render_model(
                sections=sections,
                lines=lines,
                nodes=nodes,
                frame_by_group=frame_by_group,
                color_function=colors_by_group,
            )
            # Reporting
            report.table = output_items
            report.load_combo = selected_lc
            return vkt.GeometryResult(sections_group)

        if params.step_1.mode == "Connection Design":
            non_compliant_members = {}
            design_result = {}
            for group_name, group_vals in groups.items():
                if groups_conn_props.get(group_name):
                    non_compliant_members[group_name] = []
                    frame_id_list = group_vals["frame_ids"]
                    cont_type = groups_conn_props[group_name]["contype"]
                    frame_con_capacity = db[cont_type]

                    for frame_id in frame_id_list:
                        selected_con_index = 0
                        section_name = get_section_by_id(sections, frame_id)

                        load = load_combos[frame_id][selected_lc]
                        report_item = OutputItem()
                        report_item.frame_id = frame_id
                        report_item.group_name = group_name
                        report_item.conn_type = cont_type
                        report_item.load_combo = selected_lc
                        report_item.section_name = section_name

                        if cont_type == "Moment End Plate":
                            con_list = [
                                "MEP 70%/30% (Moment/Shear)",
                                "MEP 100%/50% (Moment/Shear)",
                            ]
                            design_result[group_name] = con_list[0]

                            for index, current_conin in enumerate(con_list):
                                capacity = current_conin
                                color, report_item = (
                                    compliance_check.moment_end_plate_check(
                                        frame_con_capacity,
                                        section_name,
                                        report_item,
                                        capacity,
                                        load,
                                    )
                                )
                                if report_item.check == "ok":
                                    if index > selected_con_index:
                                        selected_con_index = index
                                        design_result[group_name] = con_list[index]
                                    break

                        if cont_type == "Web Cope":
                            con_list = ["Web Cope 30%", "Web Cope 40%"]
                            design_result[group_name] = con_list[0]

                            for index, current_conin in enumerate(con_list):
                                capacity = current_conin

                                color, report_item = compliance_check.web_cope(
                                    frame_con_capacity,
                                    section_name,
                                    report_item,
                                    capacity,
                                    load,
                                )
                                if report_item.check == "ok":
                                    if index > selected_con_index:
                                        selected_con_index = index
                                        design_result[group_name] = con_list[index]
                                    break

                        if cont_type == "Base Plate":
                            con_list = [
                                "Base Plate 15%",
                                "Base Plate 30%",
                                "Base Plate 50%",
                                "Base Plate 80%",
                            ]
                            design_result[group_name] = con_list[0]

                            for index, current_conin in enumerate(con_list):
                                capacity = current_conin

                                color, report_item = compliance_check.base_plate(
                                    frame_con_capacity,
                                    section_name,
                                    report_item,
                                    capacity,
                                    load,
                                    nodes,
                                )
                                if report_item.check == "ok":
                                    if index > selected_con_index:
                                        selected_con_index = index
                                        design_result[group_name] = con_list[index]
                                    break

                        if report_item.check == "No ok":
                            non_compliant_members[group_name].append(frame_id)

                        output_items.append(report_item)
                        if color:
                            frame_by_group.update(
                                {frame_id: {"material": vkt.Material(color=color)}}
                            )

            sections_group = render_model(
                sections=sections,
                lines=lines,
                nodes=nodes,
                frame_by_group=frame_by_group,
                color_function=colors_by_group,
            )
            # Reporting
            report.table = output_items
            report.load_combo = selected_lc
            con_summary_list.parse_from_dict(design_result)
            comp_summary_list.parse_from_dict(non_compliant_members)
            return vkt.GeometryResult(sections_group)

    def generate_report(self, params, **kwargs):
        components = []

        template_path = Path(__file__).parent / "library" /"template"/ "report_template.docx"

        if params.step_1.mode == "Connection Design":
            for key, vals in con_summary_list.serialize().items():
                components.append(WordFileTag(key, vals))

            for key, vals in comp_summary_list.serialize().items():
                components.append(WordFileTag(key, vals))

            template_path = (
                Path(__file__).parent / "library" / "template"/"report_template_design.docx"
            )

        for key, vals in report.serialize().items():
            components.append(WordFileTag(key, vals))

        with open(template_path, "rb") as template:
            word_file = render_word_file(template, components)
        return DownloadResult(word_file, "Full Calculation Report.docx")


# %
