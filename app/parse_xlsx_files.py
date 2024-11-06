import pandas as pd

def extract_sheets(file_path):
    sheet_names = ["Objects and Elements - Joints", "Group Assignments", 
                   "Objects and Elements - Frames", "Frame Assigns - Summary", 
                   "Element Joint Forces - Frame"]

    dataframes = {}

    for sheet in sheet_names:
        dataframes[sheet] = pd.read_excel(file_path, sheet_name=sheet, skiprows=1)
    
    return dataframes
