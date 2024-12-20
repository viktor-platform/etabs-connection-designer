import viktor as vkt

NODE_RADIUS = 40

def render_model(
    sections: dict,
    lines: dict,
    nodes: dict,
    frame_by_group: dict,
    color_function: callable,
    sections_group=[],
):
    rendered_sphere = set()
    sections_group = []  # Stores all 3d entities
    for section_name, section_vals in sections.items():
        for frame_id in section_vals["frame_ids"]:
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

            material = color_function(frame_by_group, frame_id)
            section_k = vkt.RectangularExtrusion(200, 200, line_k, identifier=str(frame_id), material=material)
            sections_group.append(section_k)
    return sections_group


def colors_by_group(frame_by_group: dict, frame_id: int):
    maybe_color = frame_by_group.get(frame_id)
    if maybe_color:
        if isinstance(maybe_color["material"], tuple):
            r,g,b = maybe_color["material"]
            material = vkt.Material(color = vkt.Color(r=r, g=g, b=b))
        else:
            material = maybe_color["material"]
    else:
        material = vkt.Material(color=vkt.Color(r=40, g=40, b=40))
    return material


def get_material_color(group_name, groups_conn_props):
    """
    Determine the material color based on the group name and connection properties.
    """
    if group_name in groups_conn_props:
        return vkt.Material(color=groups_conn_props[group_name]["color"])
    else:
        # Default color if the group is not found in the connection properties
        return vkt.Material(color=vkt.Color(r=40, g=40, b=40))


def plotly_model(lines: dict, nodes: dict, color_dict: dict):
    import plotly.graph_objects as go
    import plotly.io as pio

    # Set default image parameters for saving
    pio.kaleido.scope.default_format = "png"
    pio.kaleido.scope.default_width = 800
    pio.kaleido.scope.default_height = 600

    # Initialize lists to store node coordinates and identifiers
    x_nodes = []
    y_nodes = []
    z_nodes = []
    node_ids = []
    rendered_nodes = set()

    # Collect node coordinates
    for line_id, line_data in lines.items():
        node_id_i = line_data["nodeI"]
        node_id_j = line_data["nodeJ"]

        # Add nodeI if not already added
        if node_id_i not in rendered_nodes:
            node_i = nodes[node_id_i]
            x_nodes.append(node_i["x"])
            y_nodes.append(node_i["y"])
            z_nodes.append(node_i["z"])
            node_ids.append(str(node_id_i))
            rendered_nodes.add(node_id_i)

        # Add nodeJ if not already added
        if node_id_j not in rendered_nodes:
            node_j = nodes[node_id_j]
            x_nodes.append(node_j["x"])
            y_nodes.append(node_j["y"])
            z_nodes.append(node_j["z"])
            node_ids.append(str(node_id_j))
            rendered_nodes.add(node_id_j)

    # Create scatter plot of nodes
    node_trace = go.Scatter3d(
        x=x_nodes,
        y=y_nodes,
        z=z_nodes,
        mode="markers",
        marker=dict(size=5, color="blue"),
        text=node_ids,
        hoverinfo="text",
        showlegend=False,
    )

    # Initialize a dictionary to group lines by color
    color_to_lines = {}

    for line_id, line_data in lines.items():
        node_id_i = line_data["nodeI"]
        node_id_j = line_data["nodeJ"]

        node_i = nodes[node_id_i]
        node_j = nodes[node_id_j]

        # Get color from color_dict
        color = color_dict.get(line_id, "black")  # Default to black if not specified

        if color not in color_to_lines:
            color_to_lines[color] = {"x": [], "y": [], "z": []}

        # Add coordinates for the line segment
        color_to_lines[color]["x"].extend([node_i["x"], node_j["x"], None])
        color_to_lines[color]["y"].extend([node_i["y"], node_j["y"], None])
        color_to_lines[color]["z"].extend([node_i["z"], node_j["z"], None])

    # Create line traces for each color
    line_traces = []
    for color, coords in color_to_lines.items():
        trace = go.Scatter3d(
            x=coords["x"],
            y=coords["y"],
            z=coords["z"],
            mode="lines",
            line=dict(width=2, color=color),
            hoverinfo="none",
            showlegend=False,
        )
        line_traces.append(trace)

    # Combine node and line traces
    data = [node_trace] + line_traces

    # Set up the layout of the plot
    layout = go.Layout(
        scene=dict(
            xaxis=dict(
                visible=False,
                showgrid=False,
                zeroline=False,
                showline=False,
                showticklabels=False,
            ),
            yaxis=dict(
                visible=False,
                showgrid=False,
                zeroline=False,
                showline=False,
                showticklabels=False,
            ),
            zaxis=dict(
                visible=False,
                showgrid=False,
                zeroline=False,
                showline=False,
                showticklabels=False,
            ),
            aspectmode="data",
            bgcolor="white",
        ),
        paper_bgcolor="white",
        margin=dict(r=0, l=0, b=0, t=0),
        showlegend=False,
    )

    # Create the figure and save it as a PNG image
    fig = go.Figure(data=data, layout=layout)
    fig.write_image("plot.png")


def get_color_for_ratio(ratio):
    if ratio < 1.0:
        return 0, 255, 0  # Green
    elif 1.0 <= ratio <= 1.1:
        return 255, 165, 0  # Orange
    else:
        return 255, 0, 0  # Red

def render_legend(sections_group: list):
    legend_cord_x = 0
    legend_cord_y = 0
    legend_cord_z = 30000  # Top of the legend
    legend_cord_z2 = 20000  # Bottom of the legend

    legend_height = legend_cord_z - legend_cord_z2
    num_sections = 3

    labels = []

    # Define colors and ratio ranges
    colors = [
        (0, 255, 0),  # Green
        (255, 165, 0),  # Orange
        (255, 0, 0)  # Red
    ]
    ratio_ranges = [
        "< 1.0",
        "1.0 - 1.1",
        "> 1.1"
    ]

    # Offset string for alignment
    offset_str = " " * 33

    # Create legend sections and labels
    for i in range(num_sections):
        color = vkt.Color(*colors[i])
        z_start = legend_cord_z2 + i * (legend_height / num_sections)
        z_end = z_start + (legend_height / num_sections)

        start_point = vkt.Point(legend_cord_x, legend_cord_y, z_start)
        end_point = vkt.Point(legend_cord_x, legend_cord_y, z_end)
        line = vkt.Line(start_point, end_point)

        section = vkt.RectangularExtrusion(700, 700, line, material=vkt.Material(color=color, opacity=0.8))
        sections_group.append(section)

        # Create label for this section
        z = (z_start + z_end) / 2
        text_point = vkt.Point(legend_cord_x, legend_cord_y, z)
        label_text = f"{offset_str}Ratio: {ratio_ranges[i]}"
        label = vkt.Label(text_point, label_text, size_factor=0.7, color=vkt.Color(0, 0, 0))
        labels.append(label)

    # Bottom label: 'Compliant'
    text_point_bottom = vkt.Point(legend_cord_x, legend_cord_y, legend_cord_z2)
    label_bottom = vkt.Label(text_point_bottom, f"{offset_str}Compliant", size_factor=0.7, color=vkt.Color(0, 0, 0))
    labels.append(label_bottom)

    # Top label: 'Non Compliant'
    text_point_top = vkt.Point(legend_cord_x, legend_cord_y, legend_cord_z)
    label_top = vkt.Label(text_point_top, f"{offset_str}Non Compliant", size_factor=0.7, color=vkt.Color(0, 0, 0))
    labels.append(label_top)

    return sections_group, labels