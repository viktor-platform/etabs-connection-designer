import viktor as vkt
from textwrap import dedent
from app.parse_xlsx_files import get_entities

NODE_RADIUS = 40

def get_possible_columns(params, **kwargs):
    # TO DO: This is super slow, make it right. 
    if params.csv_file:
        xlsx_file = params.csv_file.file
        file_content = xlsx_file.getvalue_binary()
        nodes, lines, groups, sections = get_entities(file_content)
        return [group_name for group_name, group_vals in groups.items()]
    return ["First upload a .xlsx file"]


class Parametrization(vkt.Parametrization):
    main_text = vkt.Text(
        dedent("""
        # ETABS Connection Designer

        This app allows you to verify the compliance of shear, moment, and baseplate standard connections based on the internal loads of your load combinations.
        """)
    )
    upload_text = vkt.Text(
        dedent("""
        ## Upload your `.xlsx` file!

        Export your model's results in `.xlsx` format from ETABS, click on the file loader below, and upload the `.xlsx` file.
        """)
    )
    csv_file = vkt.FileField("Upload a .xlsx file!", flex=50)
    lines = vkt.LineBreak()

    assign_text = vkt.Text(
        dedent("""
        ## Assign design groups to connection type

        After loading the `.xlsx` file, the app will display the connection groups. You can select in the following array which connection type and color need to be associated with each group!
        """)
    )
    connections = vkt.DynamicArray("Connection Type")
    connections.groups = vkt.OptionField(
        "Avaliable Groups", options=get_possible_columns
    )
    connections.connection_type = vkt.OptionField(
        "Connection Type", options=["Shear-Tab", "Moment-Enplate", "Fixed-BasePlate"]
    )
    connections.color = vkt.ColorField("Color", default=vkt.Color(128, 128, 128))


class Controller(vkt.Controller):
    label = "Structure Controller"

    parametrization = Parametrization

    @vkt.GeometryView("3D model", duration_guess=10, x_axis_to_right=True)
    def generate_structure(self, params, **kwargs):
        xlsx_file = params.csv_file.file
        file_content = xlsx_file.getvalue_binary()
        nodes, lines, groups, sections = get_entities(file_content)
        # section_vals keys "name","frame_ids"
        rendered_sphere = set()
        sections_group = []  # Stores all 3d entities
        frame_by_group = {}
        # Assign colors
        groups_conn_props = {}
        for con_dict in params.connections:
            groups_conn_props.update(
                {
                    con_dict.groups: {
                        "color": con_dict.color,
                        "contype": con_dict.connection_type,
                    }
                }
            )
            print(groups_conn_props)

        for group_name, group_vals in groups.items():
            # material_color = generate_pastel_material()

            for frames_in_groups in group_vals["frame_ids"]:
                frame_by_group.update(
                    {
                        frames_in_groups: {
                            "material": vkt.Material(
                                color=groups_conn_props[group_name]["color"]
                            )
                        }
                    }
                )

        for section_name, section_vals in sections.items():
            for frame_id in section_vals["frame_ids"]:
                try:
                    node_id_i = lines[frame_id]["nodeI"]
                    node_id_j = lines[frame_id]["nodeJ"]

                    node_i = nodes[node_id_i]
                    node_j = nodes[node_id_j]

                    point_i = vkt.Point(node_i["x"], node_i["y"], node_i["z"])
                    point_j = vkt.Point(node_j["x"], node_j["y"], node_j["z"])

                    if node_id_i not in rendered_sphere:
                        sphere_k = vkt.Sphere(
                            point_i,
                            radius=NODE_RADIUS,
                            material=None,
                            identifier=str(node_id_i),
                        )
                        sections_group.append(sphere_k)
                        rendered_sphere.add(node_id_i)

                    if node_id_j not in rendered_sphere:
                        sphere_k = vkt.Sphere(
                            point_j,
                            radius=NODE_RADIUS,
                            material=None,
                            identifier=str(node_id_j),
                        )
                        sections_group.append(sphere_k)
                        rendered_sphere.add(node_id_j)

                    line_k = vkt.Line(point_i, point_j)

                    maybe_color = frame_by_group.get(frame_id)
                    if maybe_color:
                        material = maybe_color["material"]
                        # material = vkt.Material(color=vkt.Color(r=200, g=0, b=200))
                    else:
                        material = vkt.Material(vkt.Color(r=0, g=0, b=0))

                    section_k = vkt.RectangularExtrusion(
                        200, 200, line_k, identifier=str(frame_id), material=material
                    )
                    sections_group.append(section_k)
                except:
                    print("skip")    
        return vkt.GeometryResult(sections_group)
