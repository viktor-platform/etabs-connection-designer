from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Union


class Node(BaseModel):
    id: int
    x: float
    y: float
    z: float


class Group(BaseModel):
    name: str
    frame_ids: list[int]


class AllGroups(BaseModel):
    groups: list[Group]


class Frame(BaseModel):
    id: int
    nodeI: int
    nodeJ: int


class Section(BaseModel):
    name: str
    frame_ids: list[int]


class AllSections(BaseModel):
    sections: list[Section]


class OutputItem(BaseModel):
    frame_id: int | None = None
    group_name: str | None = None
    section_name: str | None = None
    load_combo: str | None = None
    conn_type: str | None = None
    V: float | None = None
    M: float | None = None
    P: float | None = None
    Vn: float | None = None
    Mn: float | None = None
    Pn: float | None = None
    check: str | None = None

    def serialize(self) -> dict[str, any]:
        # Replace None with "-" and round float values to 2 decimal places
        return {
            k: (round(v, 2) if isinstance(v, float) else v if v is not None else "-") for k, v in self.dict().items()
        }


class ReportData(BaseModel):
    load_combo: str | None = None
    date_string: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d"))
    author: str | None = "Viktor"
    table: list[OutputItem] = []

    def serialize(self) -> dict[str, any]:
        # Serialize all fields in ReportData, applying the custom serialization for table items
        return {
            "load_combo": self.load_combo if self.load_combo is not None else "-",
            "date_string": self.date_string if self.date_string is not None else "-",
            "author": self.author if self.author is not None else "-",
            "table": [item.serialize() for item in self.table],
        }

    def clear(self) -> None:
        # Reset all attributes to their initial values
        self.load_combo = None
        self.author = "Viktor"
        self.table = []


class ComplianceSummaryModel(BaseModel):
    group_name: str | None = None
    non_compliant_members: list[int] | str | None = Field(
        default=None, description="List of non-compliant members or '-' if empty"
    )
    compliance: str | None = Field(default=None, description="'Complies' if empty, 'Not Complies' otherwise")

    @field_validator("non_compliant_members", mode="before")
    def replace_empty_list(cls, value):
        if isinstance(value, list) and not value:
            return "-"
        return value

    @model_validator(mode="after")
    def set_compliance_status(cls, model):
        if model.non_compliant_members == "-":
            model.compliance = "Complies"
        else:
            model.compliance = "Not Complies"
        return model

    def serialize(self) -> dict[str, Union[str, list[int]]]:
        return {
            "group_name": self.group_name,
            "compliance": self.compliance,
            "non_comp_member": self.non_compliant_members,
        }


class ConnectionSummaryModel(BaseModel):
    group_name: str
    connection_type: str

    def serialize(self) -> dict[str, str]:
        return {"group_name": self.group_name, "con_type": self.connection_type}


class ComplianceSummaryList:
    def __init__(self):
        self.items: list[ComplianceSummaryModel] = []

    def parse_from_dict(self, data: dict[str, list[int]]) -> None:
        """Parse a dictionary into a list of ComplianceSummaryModel instances."""
        self.items = [
            ComplianceSummaryModel(group_name=group, non_compliant_members=members) for group, members in data.items()
        ]

    def serialize(self) -> dict[str, list[dict[str, Union[str, list[int]]]]]:
        """Serialize all items for Jinja template rendering with the key 'comp_summary'."""
        return {"comp_summary": [item.serialize() for item in self.items]}

    def clear(self) -> None:
        """Clear the list and reset each item to its default nullable state."""
        self.items = []


class ConnectionSummaryList:
    def __init__(self):
        self.items: list[ConnectionSummaryModel] = []

    def parse_from_dict(self, data: dict[str, str]) -> None:
        """Parse a dictionary into a list of ConnectionSummaryModel instances."""
        self.items = [ConnectionSummaryModel(group_name=group, connection_type=type_) for group, type_ in data.items()]

    def serialize(self) -> dict[str, list[dict[str, str]]]:
        """Serialize all items for Jinja template rendering with the key 'con_summary'."""
        return {"con_summary": [item.serialize() for item in self.items]}

    def clear(self) -> None:
        """Clear the list and reset each item to its default nullable state."""
        self.items = []


report_headers = [
    "Design Member",
    "Group Name",
    "Cross Section",
    "Load Combination",
    "Connection Type",
    "Shear Force (V) [kN]",
    "Moment (M) [kN·m]",
    "Axial Force (P) [kN]",
    "Shear Capacity (phiV) [kN]",
    "Moment Capacity (phiM) [kN·m]",
    "Axial Capacity (phiM) [kN·m]",
    "Check [ok/not ok]"
]