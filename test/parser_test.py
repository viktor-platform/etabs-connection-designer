from app.parse_xlsx_files import extract_sheets
from app.models import Node, Group, AllGroups, Frame,Section,AllSections

file_path = "test/data/steel2_result.xlsx" 
sheets_data = extract_sheets(file_path)

joints_df = sheets_data["Objects and Elements - Joints"]
groups_df = sheets_data["Group Assignments"]
frames_df = sheets_data["Objects and Elements - Frames"]
frame_assigns_summary_df = sheets_data["Frame Assigns - Summary"]
element_joint_forces_df = sheets_data["Element Joint Forces - Frame"]

# Create Nodes
joints_df_cleaned = joints_df.dropna(subset=['Object Name', 'Global X', 'Global Y', 'Global Z'])
for _, row in joints_df_cleaned.iterrows():
    node_id = int(row['Object Name'])
    x = float(row['Global X'])
    y = float(row['Global Y'])
    z = float(row['Global Z'])
    node = Node(id=node_id, x=x, y=y, z=z)
    # print(node)

# Create groups
groups_df_cleaned = groups_df.dropna(subset=['Group Name', 'Object Unique Name'])
group_names = groups_df_cleaned['Group Name'].unique()
groups_list = []
for group_name in group_names:
    group_df = groups_df_cleaned[groups_df_cleaned['Group Name'] == group_name]
    frame_ids = group_df['Object Unique Name'].astype(int).tolist()
    group = Group(name=group_name, frame_ids=frame_ids)
    groups_list.append(group)
all_groups = AllGroups(groups=groups_list)


# Create Frames
frames_df_cleaned = frames_df.dropna(subset=['Element Name', 'Elm JtI', 'Elm JtJ'])
for _, row in frames_df_cleaned.iterrows():
    if not isinstance(row['Element Name'],str): # avoid 'Global'
        frame_id = int(row['Element Name'])
        nodeI = int(row['Elm JtI'])
        nodeJ = int(row['Elm JtJ'])
        frame = Frame(id=frame_id, nodeI=nodeI, nodeJ=nodeJ)
        print(frame)


# Create sections
frame_assigns_summary_df_cleaned = frame_assigns_summary_df.dropna(subset=['Design Section', 'UniqueName'])
section_names = frame_assigns_summary_df_cleaned['Design Section'].unique()
sections_list = []

for section_name in section_names:
    section_df = frame_assigns_summary_df_cleaned[frame_assigns_summary_df_cleaned['Design Section'] == section_name]
    frame_ids = section_df['UniqueName'].tolist()
    # frame_ids = [fid for fid in frame_ids if isinstance(fid,int)]
    section = Section(name=section_name, frame_ids=frame_ids)
    sections_list.append(section)

all_sections = AllSections(sections=sections_list)
print(all_sections) 