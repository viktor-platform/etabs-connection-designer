import pandas as pd
import io

from app.models import Node, Group,Frame, Section


def extract_sheets(file_content):
    sheet_names = [
        "Objects and Elements - Joints",
        "Group Assignments",
        "Beam Object Connectivity",
        "Frame Assigns - Sect Prop",
        "Element Joint Forces - Frame",
        "Column Object Connectivity"
    ]

    dataframes = {}

    # Create a BytesIO object from the file content
    excel_data = io.BytesIO(file_content)

    # Use pandas.ExcelFile for efficient reading
    with pd.ExcelFile(excel_data) as excel_file:
        for sheet in sheet_names:
            dataframes[sheet] = pd.read_excel(excel_file, sheet_name=sheet, skiprows=1)

    return dataframes


def get_entities(file_content):
    nodes_dict = {}
    frame_dicts = {}
    group_dicts = {}
    section_dicts = {}
    sheets_data = extract_sheets(file_content)

    joints_df = sheets_data["Objects and Elements - Joints"]
    groups_df = sheets_data["Group Assignments"]
    beam_df = sheets_data["Beam Object Connectivity"]
    column_df = sheets_data["Column Object Connectivity"]
    frame_assigns_summary_df = sheets_data["Frame Assigns - Sect Prop"]
    # element_joint_forces_df = sheets_data["Element Joint Forces - Frame"]

    # Create Nodes
    joints_df_cleaned = joints_df.dropna(
        subset=["Object Name", "Global X", "Global Y", "Global Z","Object Type"]
    )
    for _, row in joints_df_cleaned.iterrows():
        if row["Object Type"] == "Joint":
            node_id = int(row["Object Name"])
            x = float(row["Global X"])
            y = float(row["Global Y"])
            z = float(row["Global Z"])
            node = Node(id=node_id, x=x, y=y, z=z)
            nodes_dict.update({node_id: node.model_dump()})
            # print(node)

    # Create groups
    groups_df_cleaned = groups_df.dropna(subset=["Group Name", "Object Unique Name"])
    group_names = groups_df_cleaned["Group Name"].unique()
    for group_name in group_names:
        group_df = groups_df_cleaned[groups_df_cleaned["Group Name"] == group_name]
        frame_ids = group_df["Object Unique Name"].astype(int).tolist()
        group = Group(name=group_name, frame_ids=frame_ids)
        group_dicts.update({group_name: group.model_dump()})

    # Create Frames
    column_df_cleaned = column_df.dropna(subset=["Unique Name", "UniquePtI", "UniquePtJ"])
    for _, row in column_df_cleaned.iterrows():
        if not isinstance(row["Unique Name"], str):  # avoid 'Global'
            frame_id = int(row["Unique Name"])
            nodeI = int(row["UniquePtI"])
            nodeJ = int(row["UniquePtJ"])
            frame = Frame(id=frame_id, nodeI=nodeI, nodeJ=nodeJ)
            frame_dicts.update({frame_id: frame.model_dump()})

    beam_df_cleaned = beam_df.dropna(subset=["Unique Name", "UniquePtI", "UniquePtJ"])
    for _, row in beam_df_cleaned.iterrows():
        if not isinstance(row["Unique Name"], str):  # avoid 'Global'
            frame_id = int(row["Unique Name"])
            nodeI = int(row["UniquePtI"])
            nodeJ = int(row["UniquePtJ"])
            frame = Frame(id=frame_id, nodeI=nodeI, nodeJ=nodeJ)
            frame_dicts.update({frame_id: frame.model_dump()})

    # Create sections
    frame_assigns_summary_df_cleaned = frame_assigns_summary_df.dropna(
        subset=["Section Property", "UniqueName"]
    )
    section_names = frame_assigns_summary_df_cleaned["Section Property"].unique()

    for section_name in section_names:
        section_df = frame_assigns_summary_df_cleaned[
            frame_assigns_summary_df_cleaned["Section Property"] == section_name
        ]
        frame_ids = section_df["UniqueName"].tolist()
        # frame_ids = [fid for fid in frame_ids if isinstance(fid,int)]
        section = Section(name=section_name, frame_ids=frame_ids)
        section_dicts.update({section_name: section.model_dump()})
    return nodes_dict, frame_dicts, group_dicts, section_dicts
