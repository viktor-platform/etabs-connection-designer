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
    if params.step_1.tab_1.csv_file:
        result = read_file(params.step_1.tab_1.csv_file)
        return result[0]
    return ["First upload a .xlsx file"]


def get_possible_load_combos(params, **kwargs):
    if params.step_1.tab_1.csv_file:
        return read_file(params.step_1.tab_1.csv_file)[1]
    return ["First upload a .xlsx file"]


def visible(params, **kwargs):
    if params.step_1.tab_1.mode == "Connection Design":
        return False
    return True


class Parametrization(vkt.Parametrization):
    step_1 = vkt.Step("", views=["generate_structure"])
    step_1.tab_1 = vkt.Tab('Inputs')
    step_1.tab_1.main_text = vkt.Text(
        dedent(
            """
            # ETABS Connection Designer
            This app allows you to verify the compliance of shear, moment, 
            and base plate standard connections based on the internal loads 
            of your load combinations.
            """
        )
    )
    step_1.tab_1.upload_text = vkt.Text(
        dedent(
            """
            ## Step 1: Upload Your `.xlsx` File
            Export your model's results in `.xlsx` format from ETABS,
            click on the file loader below, and upload the `.xlsx` file.
        """
        )
    )
    step_1.tab_1.csv_file = vkt.FileField(
        "**Upload a .xlsx file:**",
        flex=50,
    )
    step_1.tab_1.lines = vkt.LineBreak()
    step_1.tab_1.calc = vkt.Text(
        dedent(
            """
            ## Step 2: Define Calculation Mode
            You can either analyze the compliance of the connection by
            assigning a capacity, or let the app calculate the optimal
            capacity based on the selected load combination.
        """
        )
    )
    step_1.tab_1.mode = vkt.OptionField(
        "Select Calculation Mode",
        options=["Connection Check", "Connection Design"],
        default="Connection Check",
        variant="radio-inline",
    )
    step_1.tab_1.assign_text = vkt.Text(
        dedent(
            """
            ## Step 3: Assign Connection Types to Design Groups
            After loading the `.xlsx` file, the app will display the connection groups.
            You can select in the following array which connection type and color need to
            be associated with each group!
        """
        )
    )

    step_1.tab_1.connections = vkt.DynamicArray("Assign Groups")
    step_1.tab_1.connections.groups = vkt.OptionField("Available Groups", options=get_possible_columns)
    step_1.tab_1.connections.connection_type = vkt.OptionField(
        "Connection Type", options=["Web Cleat", "Moment End Plate", "Base Plate"]
    )
    step_1.tab_1.connections.color = vkt.ColorField("Color", default=vkt.Color(128, 128, 128))
    step_1.tab_1.connections.capacities = vkt.OptionField("Connection Capacity", options=connection_types, visible=visible)

    step_1.tab_2 = vkt.Tab('Connection Types')
    step_1.tab_2.title_mep = vkt.Text("### Moment End Plate")
    step_1.tab_2.img_mep = vkt.Image(
        path="moment_end_plate.png", align="center", caption="Figure 1: Moment End Plate", max_width=250
    )
    step_1.tab_2.title_wc = vkt.Text("### Web Cleat")
    step_1.tab_2.img_wc = vkt.Image(
        path="web_cleat.png", align="center", caption="Figure 2: Web Cleat", max_width=250
    )
    step_1.tab_2.title_bp = vkt.Text("### Base Plate")
    step_1.tab_2.img_bp = vkt.Image(
        path="base_plate.png", align="center", caption="Figure 3: Base Plate", max_width=250
    )
    # %%
    step_2 = vkt.Step("Connection Checks", views=["connection_check", "results_table_view"], width=30)
    step_2.text = vkt.Text(
        dedent(
            """
        # Run Calculations:
        Select a load combination to verify or design the connection based on the defined "Calculation Mode".
        The 3D view shows a model where compliant beams are green, and non-compliant beams are red.
        """
        )
    )
    step_2.load_combos = vkt.OptionField("Load Combinations", options=get_possible_load_combos)
    step_2.text2 = vkt.Text(
        dedent(
            """ 
        # Download Report:
        After the check, download a detailed report with inputs, load combinations, forces, and compliance status.
        The report, exported as a Word document, is useful for documentation, sharing, or record-keeping.
        """
        )
    )
    step_2.break_line = vkt.LineBreak()
    step_2.download_buttoms = vkt.DownloadButton("Generate Report", method="generate_report", longpoll=True)
