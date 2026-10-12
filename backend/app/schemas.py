import enum
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models import HardwareCategory, HardwareUnit, ProfileRole

Name = Field(min_length=1, max_length=200)
Code = Field(min_length=1, max_length=64)
PositiveMm = Field(gt=0, le=100_000)
Money = Field(default=None, ge=0)


class _Out(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int


# Profile systems

class ProfileSystemIn(BaseModel):
    code: str = Code
    name_en: str = Name
    name_ar: str = Name
    manufacturer: str | None = None
    description: str | None = None
    thermal_break: bool = False
    sash_overlap_mm: float = Field(default=0, ge=0, le=100)
    glass_bite_mm: float = Field(default=0, ge=0, le=100)


class ProfileSystemOut(ProfileSystemIn, _Out):
    pass


# Profiles

class ProfileIn(BaseModel):
    system_id: int
    article_no: str = Code
    name_en: str = Name
    name_ar: str = Name
    role: ProfileRole
    width_mm: float = PositiveMm
    height_mm: float = PositiveMm
    weight_kg_per_m: float = Field(gt=0, le=100)
    bar_length_mm: int = Field(default=6000, gt=0, le=20_000)
    price_per_m: float | None = Money


class ProfileOut(ProfileIn, _Out):
    pass


# Glass

class GlassTypeIn(BaseModel):
    code: str = Code
    name_en: str = Name
    name_ar: str = Name
    build_up: str | None = Field(default=None, max_length=100)
    total_thickness_mm: float = Field(gt=0, le=200)
    glass_thickness_mm: float = Field(gt=0, le=200)
    u_value: float | None = Field(default=None, ge=0)
    price_per_m2: float | None = Money

    @model_validator(mode="after")
    def _panes_fit(self):
        if self.glass_thickness_mm > self.total_thickness_mm:
            raise ValueError("glass_thickness_mm cannot exceed total_thickness_mm")
        return self


class GlassTypeOut(GlassTypeIn, _Out):
    pass


# Hardware

class HardwareItemIn(BaseModel):
    system_id: int | None = None
    article_no: str = Code
    name_en: str = Name
    name_ar: str = Name
    category: HardwareCategory
    unit: HardwareUnit = HardwareUnit.piece
    price_per_unit: float | None = Money


class HardwareItemOut(HardwareItemIn, _Out):
    pass


# Calculations

class ProfilePieceOut(BaseModel):
    length_mm: float
    weight_kg: float
    price: float | None


class GlassPaneOut(BaseModel):
    width_mm: float
    height_mm: float
    area_m2: float
    weight_kg: float
    price: float | None


# Element designer

class OpeningType(str, enum.Enum):
    fixed = "fixed"
    turn_left = "turn_left"  # hinged on the left
    turn_right = "turn_right"
    tilt_turn_left = "tilt_turn_left"
    tilt_turn_right = "tilt_turn_right"
    tilt = "tilt"  # hinged at the bottom
    sliding_left = "sliding_left"  # slides to the left
    sliding_right = "sliding_right"


class FieldNode(BaseModel):
    """One glazed opening. ``glass_id`` overrides the element's glass."""

    kind: Literal["field"] = "field"
    opening: OpeningType = OpeningType.fixed
    glass_id: int | None = None


class SplitNode(BaseModel):
    """Divides an area into parts. ``vertical`` uses mullions and gives
    columns from left to right; ``horizontal`` uses transoms and gives rows
    from top to bottom.

    ``sizes`` are centre-line sizes in mm, one per part: from the outer edge
    of the element (or the centre of a divider) to the centre of the next
    divider. A blank size shares what is left equally.
    """

    kind: Literal["split"] = "split"
    direction: Literal["vertical", "horizontal"]
    sizes: list[float | None]
    children: list["Node"] = Field(min_length=2, max_length=20)

    @model_validator(mode="after")
    def _one_size_per_part(self):
        if len(self.sizes) != len(self.children):
            raise ValueError("sizes must have one entry per part")
        return self


Node = Annotated[FieldNode | SplitNode, Field(discriminator="kind")]
SplitNode.model_rebuild()

MAX_LAYOUT_DEPTH = 8
MAX_FIELDS = 200


def _depth_and_fields(node: FieldNode | SplitNode) -> tuple[int, int]:
    if isinstance(node, FieldNode):
        return 1, 1
    results = [_depth_and_fields(c) for c in node.children]
    return 1 + max(d for d, _ in results), sum(f for _, f in results)


class ElementIn(BaseModel):
    position: str = Field(default="", max_length=64)
    name: str = Name
    quantity: int = Field(default=1, ge=1, le=10_000)
    system_id: int
    width_mm: float = Field(gt=0, le=20_000)
    height_mm: float = Field(gt=0, le=20_000)
    frame_profile_id: int
    mullion_profile_id: int | None = None
    transom_profile_id: int | None = None
    sash_profile_id: int | None = None
    bead_profile_id: int | None = None
    glass_id: int
    layout: Node = Field(default_factory=FieldNode)

    @model_validator(mode="after")
    def _layout_not_too_big(self):
        depth, fields = _depth_and_fields(self.layout)
        if depth > MAX_LAYOUT_DEPTH or fields > MAX_FIELDS:
            raise ValueError(
                f"layout is too big (at most {MAX_LAYOUT_DEPTH} levels "
                f"and {MAX_FIELDS} fields)"
            )
        return self


class ElementOut(ElementIn, _Out):
    created_at: datetime
    updated_at: datetime


class RectOut(BaseModel):
    """A rectangle in mm, measured from the top-left outer corner."""

    x: float
    y: float
    width: float
    height: float


class DividerOut(BaseModel):
    path: list[int]
    direction: Literal["vertical", "horizontal"]
    rect: RectOut
    length_mm: float


class FieldOut(BaseModel):
    path: list[int]
    opening: OpeningType
    glass_id: int
    clear: RectOut  # visible opening between frame and dividers
    sash: RectOut | None  # outer edge of the sash, for opening fields
    glass_width_mm: float
    glass_height_mm: float


class GeometryOut(BaseModel):
    width_mm: float
    height_mm: float
    frame_face_mm: float
    sash_face_mm: float | None
    dividers: list[DividerOut]
    fields: list[FieldOut]


class CutLineOut(BaseModel):
    """Identical pieces of one profile, per element."""

    profile_id: int
    article_no: str
    name_en: str
    name_ar: str
    role: str
    length_mm: float
    angle_start: int  # cut angle in degrees, 90 = square cut
    angle_end: int
    quantity: int
    weight_kg: float
    price: float | None


class GlassLineOut(BaseModel):
    """Identical glass panes, per element."""

    glass_id: int
    code: str
    name_en: str
    name_ar: str
    width_mm: float
    height_mm: float
    quantity: int
    area_m2: float
    weight_kg: float
    price: float | None


class TotalsOut(BaseModel):
    """Per element. ``price`` leaves out items with no price in the catalog;
    ``price_complete`` says whether every item had one."""

    profile_weight_kg: float
    glass_weight_kg: float
    glass_area_m2: float
    weight_kg: float
    price: float
    price_complete: bool


class ElementCalculationOut(BaseModel):
    geometry: GeometryOut
    profiles: list[CutLineOut]
    glass: list[GlassLineOut]
    totals: TotalsOut
