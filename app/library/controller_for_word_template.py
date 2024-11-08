from io import BytesIO
from io import StringIO
from pathlib import Path
import datetime
import json
from munch import Munch
import numpy as np

import pandas as pd
import plotly.graph_objects as go

from viktor.core import ViktorController
from viktor.result import DownloadResult
from viktor.views import PlotlyResult, PlotlyView
from viktor.views import PDFView, PDFResult
from viktor.external.word import render_word_file, WordFileTag, WordFileImage
from viktor.utils import convert_word_to_pdf
from viktor.api_v1 import API

from .parametrization import ProjectParametrization

from icecream import ic
import os
from plotly.graph_objs import Figure

from .analysis.data_processing import set_span_ratio
from .analysis.plotting import missing_input_user_note, prepare_plot_data, camera_eye
from .analysis.processor import (
    set_all_code_data,
    execute_all_code,
    read_txt_file,
    get_load_combo_from_params,
    process_table,
)


class ProjectController(ViktorController):
    """Controller class which acts as interface for this entity type."""

    label = "Data"
    parametrization = ProjectParametrization(width=30)

    @PlotlyView("3D Results", duration_guess=1)
    def spacegass_deflection_analysis(self, params, **kwargs):
        """
        3D Results tab with the 3D visualisation of steel members passing/failing the deflection criteria.
        """
        # Visualize empty results with an error annotation to the user
        if params.tab_inputs.file_link is None or params.tab_inputs.load_combo_option is None:
            fig = missing_input_user_note()
            return PlotlyResult(fig.to_json())
        else:
            # Get all data from the set_all_code_data function
            file_lines = read_txt_file(params.tab_inputs.file_link)
            load_combo = get_load_combo_from_params(params, **kwargs)

            output = set_all_code_data(file_lines, load_combo)

            df_design_member_io = StringIO(output["df_design_member"])
            df_design_member = pd.read_json(df_design_member_io, orient="columns")

            point_dict = {
                float(k): v for k, v in output["point_dict"].items()
            }  # needs to be casted as float, memoize converts to string

            member_connectivity_io = StringIO(output["member_connectivity"])
            member_connectivity = pd.read_json(member_connectivity_io, orient="columns")

            # Span limit
            span_ratio_limit = int(set_span_ratio(params))

            # Plotting data
            member_plot_data = prepare_plot_data(
                point_dict, member_connectivity, df_design_member, span_ratio_limit, vertical_axis="Y", text_size=14
            )

            fig = go.Figure(data=member_plot_data)
            fig.update_layout(
                title=f"Deflection Criteria = Span / {span_ratio_limit}",
                scene=dict(
                    xaxis_title="X Coordinate [m]",
                    yaxis_title="Z Coordinate [m]",
                    zaxis_title="Y Coordinate [m]",
                    camera=dict(eye=camera_eye(point_dict)),  # Properly nest the camera settings within the scene
                ),
                scene_aspectmode="data",
                showlegend=True,
            )

            return PlotlyResult(fig.to_json())

    @PlotlyView("Beam Results Data", duration_guess=1)
    def dataframe_table_new(self, params, **kwargs):
        """
        Table data of steel members passing/failing the deflection criteria.
        """
        # Visualize empty results with an error annotation to the user
        if params.tab_inputs.file_link is None or params.tab_inputs.load_combo_option is None:
            fig = missing_input_user_note()
            return PlotlyResult(fig.to_json())
        else:
            # Get the dataframes from the set_all_code_data function
            file_lines = read_txt_file(params.tab_inputs.file_link)
            load_combo = get_load_combo_from_params(params, **kwargs)

            df_design_member_json = set_all_code_data(file_lines, load_combo)["df_design_member"]
            df_design_member_io = StringIO(df_design_member_json)
            df_design_member = pd.read_json(df_design_member_io, orient="columns")
            df_design_member.dropna(subset=["Start Disp [mm]"], inplace=True)

            # Convert columns to formatted strings
            convert_columns_to_string_list = [
                "Start Disp [mm]",
                "End Disp [mm]",
                "Max Disp [mm]",
                "Length [m]",
                "Mid Disp [mm]",
                "Relative Disp [mm]",
            ]
            for col in convert_columns_to_string_list:
                # Check if column exists in dataframe to avoid KeyErrors
                if col in df_design_member.columns:
                    df_design_member[col] = df_design_member[col].apply(lambda x: "{:.3f}".format(x))

            fill_colors = []  # Initialize an empty list to hold the fill color for each row
            span_ratio_limit = int(set_span_ratio(params))

            for index, row in df_design_member.iterrows():
                span_ratio = row["Span Ratio"]
                if isinstance(span_ratio, str):
                    fill_colors.append("lightgrey")
                else:
                    if span_ratio < span_ratio_limit:
                        fill_colors.append("red")
                    elif span_ratio_limit <= span_ratio < 1.1 * span_ratio_limit:
                        fill_colors.append("orange")
                    else:
                        fill_colors.append("lightgreen")

            fig = go.Figure(
                data=[
                    go.Table(
                        header=dict(
                            values=[col.upper() for col in df_design_member.columns],
                            fill_color="lightskyblue",
                            align="center",
                            font=dict(color="black", size=12),
                        ),
                        cells=dict(
                            values=[df_design_member[col].tolist() for col in df_design_member.columns],
                            fill_color=[fill_colors],
                            align="center",
                        ),
                    )
                ]
            )

            fig.update_layout(title=f"Beam Results Data Table - Span / {span_ratio_limit}")

            return PlotlyResult(fig.to_json())

    @staticmethod
    def _convert_to_excel(df, sheet_name1):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name=sheet_name1, index=False)
        output.seek(0)
        return output

    def download_design_df(self, params, **kwargs) -> DownloadResult:
        """
        Download button
        """
        file_lines = read_txt_file(params.tab_inputs.file_link)
        load_combo = get_load_combo_from_params(params, **kwargs)
        df_design_member_json = set_all_code_data(file_lines, load_combo)["df_design_member"]
        df_design_member_io = StringIO(df_design_member_json)
        df_design_member = pd.read_json(df_design_member_io, orient="columns")

        # Step 2: Create Excel
        result = self._convert_to_excel(df_design_member, sheet_name1="Design Member Data")
        file_name = "design_member_data.xlsx"
        return DownloadResult(file_name=file_name, file_content=result)

    def generate_word_document(self, params, **kwargs):
        """
        Generate Word document based on the report_template.docx

        The report includes:
        - all the inputs
        - design dataframe output
        - plotly image
        """
        # table
        file_lines = read_txt_file(params.tab_inputs.file_link)
        load_combo = get_load_combo_from_params(params, **kwargs)
        table_data = process_table(file_lines, load_combo)

        # Create emtpy components list to be filled later
        components = []

        # Retrieve author from an API
        viktor_api = API()
        current_user = viktor_api.get_current_user().full_name

        # Fill components list with data
        components.append(WordFileTag("author", current_user))
        components.append(WordFileTag("job_number", str("")))
        components.append(WordFileTag("output_file", str(params.tab_inputs.file_link.filename)))
        components.append(WordFileTag("load_combination", params.tab_inputs.load_combo_option))
        components.append(WordFileTag("span_ratio", int(set_span_ratio(params))))

        # Get the current date and time and convert to a desired format
        current_date_time = datetime.datetime.now()
        date_string = str(current_date_time.strftime("%d-%m-%Y, %H:%M"))
        components.append(WordFileTag("date_string", str(date_string)))  # Convert date to string format

        components.append(WordFileTag("table", table_data))

        # Place image
        png_data = self.create_figure(params)
        word_file_figure = WordFileImage(png_data, "plotly_figure", width=500)
        components.append(word_file_figure)

        # Get path to template and render word file
        template_path = Path(__file__).parent / "template" / "report_template.docx"
        with open(template_path, "rb") as template:
            word_file = render_word_file(template, components)

        return word_file

    @staticmethod
    def create_figure(params, **kwargs):
        """
        Create a png file from the Plotly data.
        """
        # Get all data from the set_all_code_data function
        file_lines = read_txt_file(params.tab_inputs.file_link)
        load_combo = get_load_combo_from_params(params, **kwargs)

        output = set_all_code_data(file_lines, load_combo)

        df_design_member_io = StringIO(output["df_design_member"])
        df_design_member = pd.read_json(df_design_member_io, orient="columns")

        point_dict = {
            float(k): v for k, v in output["point_dict"].items()
        }  # needs to be casted as float, memoize converts to string

        member_connectivity_io = StringIO(output["member_connectivity"])
        member_connectivity = pd.read_json(member_connectivity_io, orient="columns")

        # Span limit
        span_ratio_limit = int(set_span_ratio(params))

        # Plotting data
        member_plot_data = prepare_plot_data(
            point_dict, member_connectivity, df_design_member, span_ratio_limit, vertical_axis="Y", text_size=14
        )

        fig = go.Figure(data=member_plot_data)
        fig.update_layout(
            scene=dict(
                xaxis_title="X Coordinate [m]",
                yaxis_title="Z Coordinate [m]",
                zaxis_title="Y Coordinate [m]",
                camera=dict(
                    up=dict(x=0, y=0, z=1), eye=camera_eye(point_dict)
                ),  # Properly nest the camera settings within the scene
            ),
            scene_aspectmode="data",
            showlegend=False,
        )

        # save to bytes
        img = fig.to_image(format="png", width=1200)
        png_data = BytesIO(img)

        return png_data

    def download_word_file(self, params, **kwargs):
        """
        Download full Word report.

        Improvements: convert to a PDF.
        """
        word_file = self.generate_word_document(params, **kwargs)

        return DownloadResult(word_file, "Full Calculation Report.docx")

        # # Open the file in binary_mode
        # with word_file.open_binary() as binary:
        #     # Convert the binary stream of the Word document to PDF
        #     pdf = convert_word_to_pdf(binary)

        # return DownloadResult(pdf, "Full Report.pdf")