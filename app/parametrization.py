import viktor as vkt
from app.library.load_db import connection_types
from app.core.parse_xlsx_files import get_groups, get_load_combos, get_entities
from textwrap import dedent


@vkt.memoize
def read_file(file) -> list:
    xlsx_file = file.file
    file_content = xlsx_file.getvalue_binary()
    groups = get_groups(file_content)
    combos = get_load_combos(file_content)
    all_stuff = get_entities(file_content)
    return [groups, combos, all_stuff]


def get_possible_columns(params, **kwargs):
    if params.step_1.csv_file:
        result = read_file(params.step_1.csv_file)
        return result[0]
    return ["First upload a .xlsx file"]


def get_possible_load_combos(params, **kwargs):
    if params.step_1.csv_file:
        return read_file(params.step_1.csv_file)[1]
    return ["First upload a .xlsx file"]


def visible(params, **kwargs):
    if params.step_1.mode == "Connection Design":
        return False
    return True


class Parametrization(vkt.Parametrization):
    step_1 = vkt.Step("", views=["generate_structure"])
    step_1.main_text = vkt.Text(
        dedent(
            """
            # ETABS Connection Designer
            This app allows you to verify the compliance of shear,moment, 
            and baseplate standard connections based on the internal loads 
            of your load combinations.
            """
        )
    )
    step_1.upload_text = vkt.Text(
        dedent(
            """
            ## Upload your `.xlsx` file!
            Export your model's results in `.xlsx` format from ETABS,
            click on the file loader below, and upload the `.xlsx` file.
        """
        )
    )
    step_1.csv_file = vkt.FileField(
        "Upload a .xlsx file!",
        flex=50,
    )
    step_1.lines = vkt.LineBreak()
    step_1.calc = vkt.Text(
        dedent(
            """
            ## Define Calculation Mode
            You can either analyze the compliance of the connection by
            assigning a capacity, or let the app calculate the optimal
            capacity based on the selected load combination.
        """
        )
    )
    step_1.mode = vkt.OptionField(
        "Select Calculation  Mode",
        options=["Connection Check", "Connection Design"],
        default="Connection Check",
        variant="radio-inline",
    )
    step_1.assign_text = vkt.Text(
        dedent(
            """
            ## Assign design groups to connection type
            After loading the `.xlsx` file, the app will display the connection groups.
            You can select in the following array which connection type and color need to
            be associated with each group!
        """
        )
    )

    step_1.connections = vkt.DynamicArray("Assign Groups")
    step_1.connections.groups = vkt.OptionField("Avaliable Groups", options=get_possible_columns)
    step_1.connections.connection_type = vkt.OptionField(
        "Connection Type", options=["Web Cleat", "Moment End Plate", "Base Plate"]
    )
    step_1.connections.color = vkt.ColorField("Color", default=vkt.Color(128, 128, 128))
    step_1.connections.capacities = vkt.OptionField("Connection Capacity", options=connection_types, visible=visible)
    # %%
    step_2 = vkt.Step("Connection Checks", views=["connection_check","results_table_view"], width=30)
    step_2.text = vkt.Text(
        dedent(
            """
        # Run Calculations!
        In this step, you can select a load combination. The app will use the inputs
        defined in the previous step to either verify the compliance of the connection or design the connection,
        depending on the "application mode" defined earlier.

        On the right-hand side (RHS) of this view, a 3D model with the following color scheme will be displayed.
        In this model, beams that comply with the selected capacities are colored green; beams that do not comply
        are colored red.
        """
        )
    )
    step_2.load_combos = vkt.OptionField("Load Combinations", options=get_possible_load_combos)
    step_2.text2 = vkt.Text(
        dedent(
            """ 
        # Download Report
        Once the compliance check has been completed, you can download a comprehensive report that provides the results
        for each member analyzed in the current session. 

        The report will include all relevant details, such as the input parameters, load combinations, connection types,
        member forces, and compliance status, allowing you to review the design in detail. This document is particularly
        useful for documentation purposes, sharing with colleagues, or maintaining project records.

        To generate the report, click the button below. The application will prepare and export a Word document summarizing
        the results for easy access and further use.
        """
        )
    )
    step_2.brak_line = vkt.LineBreak()
    step_2.download_buttoms = vkt.DownloadButton("Generate Report", method="generate_report", longpoll=True)
