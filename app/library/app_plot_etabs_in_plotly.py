from viktor import ViktorController
from viktor.parametrization import ViktorParametrization, FileField, Text, LineBreak

from viktor.views import PlotlyResult, PlotlyView
from viktor import ViktorController, File, ParamsFromFile
from viktor.errors import UserError, InputViolation

import plotly.graph_objects as go
import pandas as pd
from io import BytesIO
import numpy as np
from icecream import ic



class Parametrization(ViktorParametrization):
    introduction = Text(
    """
# 🏢 Etabs End Release App Checker 

This app allows you to check incorrect frame end releases in Etabs.  
"""
    )


    # input field
    file = FileField('**Step 1:** Upload a file', file_types=['.xlsx', '.xls'], max_size=10_000_000, flex=75)

    info1 = Text(
    """
The uploaded Excel file requires the following Excel tabs:
- Point Connectivity
- Beam Connectivity
- Column Connectivity
- Wall Connectivity
- Floor Connectivity
- Brace Connectivity
- Frame Assigns Summary
- Frame Assigns Releases
"""
    )

class Controller(ViktorController):
    label = 'My Entity Type'
    parametrization = Parametrization(width=35)

    @staticmethod
    def get_dataframe_from_excel(file, sheet_name):
        violations = []
        uploaded_file = BytesIO(file.file.getvalue_binary())

        if uploaded_file is None:
            violations.append(InputViolation("File input cannot be blank"))

        if violations:
            raise UserError("Cannot show the results", input_violations=violations)

        try:
            df = pd.read_excel(uploaded_file, sheet_name=sheet_name, header=1, skiprows=[2])
        except ValueError:
            print(f"Sheet {sheet_name} not found in {file}.")

        return df


    @PlotlyView('Frame End Releases', duration_guess=1)
    def etabs_end_releases_view(self, params, **kwargs):
        sheet_names = {
        'point_connectivity': 'Point Object Connectivity',
        'beam_connectivity': 'Beam Object Connectivity',
        'column_connectivity':'Column Object Connectivity',
        'wall_connectivity': 'Wall Object Connectivity',
        'floor_connectivity': 'Floor Object Connectivity',
        'brace_connectivity': 'Brace Object Connectivity',
        'frame_assigns_summary': 'Frame Assigns - Summary',
        'frame_assigns_releases':'Frame Assigns - Releases',
        }

        connectivity_dict = {}
        # Access the connectivity_dict from the instance variable

        # test = self.get_dataframe_from_excel(file=params.file, sheet_name=sheet_names['point_connectivity'])
        # ic(test)
        for connectivity_name, sheet_name in sheet_names.items():
            connectivity = self.get_dataframe_from_excel(file=params.file, sheet_name=sheet_name)
            connectivity_dict[connectivity_name] = connectivity

        # Extract the required data frames from connectivity_dict
        point_connectivity = connectivity_dict['point_connectivity']
        beam_connectivity = connectivity_dict['beam_connectivity']
        column_connectivity = connectivity_dict['column_connectivity']
        brace_connectivity = connectivity_dict['brace_connectivity']
        wall_connectivity = connectivity_dict['wall_connectivity']
        floor_connectivity = connectivity_dict['floor_connectivity']
        frame_assigns_summary = connectivity_dict['frame_assigns_summary']
        frame_assigns_releases = connectivity_dict['frame_assigns_releases']

        def process_connectivity_data(connectivity_df):
            processed_data = []
            for _, row in connectivity_df.iterrows():
                # Check for EndRelease in frame_assigns_summary
                frame_row = frame_assigns_summary[frame_assigns_summary['UniqueName'] == row['Unique Name']]
                end_release = 'Yes' if not frame_row.empty and frame_row.iloc[0]['Releases'] == 'Yes' else 'No'

                # Check for 'T' in frame_assigns_releases
                frame_release_row = frame_assigns_releases[frame_assigns_releases['UniqueName'] == row['Unique Name']]
                t_release = 'Yes' if not frame_release_row.empty and (frame_release_row.iloc[0]['TI'] == 'Yes' or frame_release_row.iloc[0]['TJ'] == 'Yes') else 'No'

                # Check for 'M' in frame_assigns_releases
                M2_release_I = 'Yes' if not frame_release_row.empty and (frame_release_row.iloc[0]['M2I'] == 'Yes' ) else 'No'
                M2_release_J = 'Yes' if not frame_release_row.empty and (frame_release_row.iloc[0]['M2J'] == 'Yes' ) else 'No'
                M3_release_I = 'Yes' if not frame_release_row.empty and (frame_release_row.iloc[0]['M3I'] == 'Yes' ) else 'No'
                M3_release_J = 'Yes' if not frame_release_row.empty and (frame_release_row.iloc[0]['M3J'] == 'Yes' ) else 'No'

                # For UniquePtI
                processed_data.append({
                    'JointName': row['UniquePtI'],
                    'Member': row['Unique Name'],
                    'ConnectivityPoint': 'I',
                    'EndRelease': end_release,
                    'T': t_release,
                    'M2': M2_release_I,
                    'M3': M3_release_I
                })
                # For UniquePtJ
                processed_data.append({
                    'JointName': row['UniquePtJ'],
                    'Member': row['Unique Name'],
                    'ConnectivityPoint': 'J',
                    'EndRelease': end_release,
                    'T': t_release,
                    'M2': M2_release_J,
                    'M3': M3_release_J
                })
            return processed_data


        def filter_end_release_no(group):
            if (group['EndRelease'] == 'No').any() or (group[['T', 'M2', 'M3']] != 'Yes').any().any():
                return None  # Return None to drop the group
            return group

        def filter_members():
            # Process each connectivity data
            beam_data = process_connectivity_data(beam_connectivity)
            column_data = process_connectivity_data(column_connectivity)
            brace_data = process_connectivity_data(brace_connectivity)

            # Combine all data into a single DataFrame
            combined_data = pd.DataFrame(beam_data + column_data + brace_data)
            # Ensure 'JointName' is of type string
            combined_data['JointName'] = combined_data['JointName'].astype(str)

            # Sort the DataFrame
            combined_data_sorted = combined_data.sort_values(by='JointName')

            # Group by JointName and filter out groups where any EndRelease is 'No'
            filtered_data = combined_data_sorted.groupby('JointName').apply(filter_end_release_no).reset_index(drop=True)

            return filtered_data


        # Creating a dictionary to map UniqueName to coordinates
        point_dict = point_connectivity.set_index('UniqueName')[['X', 'Y', 'Z']].to_dict(orient='index')

        # Function to get coordinates from UniqueName
        def get_coords(unique_name):
            return point_dict.get(unique_name, {'X': np.nan, 'Y': np.nan, 'Z': np.nan})


        # Get the filtered members
        filtered_members = filter_members()

        # Prepare data for Plotly 3D plot
        def prepare_plot_data(connectivity_df, filtered_members):
            plot_data = []
            for _, row in connectivity_df.iterrows():
                start_point = get_coords(row['UniquePtI'])
                end_point = get_coords(row['UniquePtJ'])

                # Skip plotting if coordinates are missing
                if np.isnan(start_point['X']) or np.isnan(end_point['X']):
                    continue

                is_filtered_member = row['Unique Name'] in filtered_members['Member'].values
                line_color = 'red' if is_filtered_member else 'darkgrey'

                if is_filtered_member:
                    member_row = filtered_members[filtered_members['Member'] == row['Unique Name']].iloc[0]
                    member_info = f"{row['Unique Name']} - T = {member_row['T']}, M2 = {member_row['M2']}, M3 = {member_row['M3']}"
                else:
                    member_info = ''

                trace = go.Scatter3d(
                    x=[start_point['X'], end_point['X']], 
                    y=[start_point['Y'], end_point['Y']], 
                    z=[start_point['Z'], end_point['Z']],
                    mode='lines',
                    line=dict(color=line_color, width=6),
                    showlegend=is_filtered_member,
                    name=member_info
                )
                plot_data.append(trace)
            return plot_data

        def prepare_wall_data(df, point_coords):
            wall_plot_data = []
            for index, row in df.iterrows():
                wall_pts = []
                for pt in ['UniquePt1', 'UniquePt2', 'UniquePt3', 'UniquePt4']:
                    pt_coord = point_coords[point_coords['UniqueName'] == row[pt]]
                    if not pt_coord.empty:
                        wall_pts.append([pt_coord.iloc[0]['X'], pt_coord.iloc[0]['Y'], pt_coord.iloc[0]['Z']])
                
                if len(wall_pts) == 4:
                    x, y, z = zip(*wall_pts)
                    wall_plot_data.append(go.Mesh3d(
                        x=x, y=y, z=z,
                        color='lightblue',
                        opacity=0.5,
                        alphahull=0,
                        i=[0, 0, 0, 1], j=[1, 2, 3, 2], k=[2, 3, 1, 3]
                    ))
            return wall_plot_data


        def prepare_floor_data(df, point_coords):
            floor_plot_data = []
            for index, row in df.iterrows():
                floor_pts = []
                # Note that 'Unique Name' has a space in its name
                for pt in ['UniquePt1', 'UniquePt2', 'UniquePt3', 'UniquePt4']:
                    pt_coord = point_coords[point_coords['UniqueName'] == row[pt]]
                    if not pt_coord.empty:
                        floor_pts.append([pt_coord.iloc[0]['X'], pt_coord.iloc[0]['Y'], pt_coord.iloc[0]['Z']])
                
                if len(floor_pts) == 4:
                    x, y, z = zip(*floor_pts)
                    floor_plot_data.append(go.Mesh3d(
                        x=x, y=y, z=z,
                        color='lightgrey',  # Choose an appropriate color for floors
                        opacity=0.15,
                        alphahull=0,
                        i=[0, 0, 0, 1], j=[1, 2, 3, 2], k=[2, 3, 1, 3]
                    ))
            return floor_plot_data


        # Prepare data for beams, columns, and walls
        beam_plot_data = prepare_plot_data(beam_connectivity, filtered_members)
        column_plot_data = prepare_plot_data(column_connectivity, filtered_members)
        brace_plot_data = prepare_plot_data(brace_connectivity, filtered_members)
        wall_plot_data = prepare_wall_data(wall_connectivity, point_connectivity)
        floor_plot_data = prepare_floor_data(floor_connectivity, point_connectivity)

        # Create the 3D plot with beams, columns, and walls
        fig = go.Figure(data=beam_plot_data + column_plot_data + brace_plot_data + wall_plot_data + floor_plot_data)

        # Updating layout for better visualization
        fig.update_layout(title="3D Structure - Incorrect Member End Releases",
                        scene=dict(xaxis_title='X Coordinate [m]',
                                    yaxis_title='Y Coordinate [m]',
                                    zaxis_title='Z Coordinate [m]'),
                        scene_aspectmode='data',
                        showlegend=True)


        return PlotlyResult(fig.to_json())
    