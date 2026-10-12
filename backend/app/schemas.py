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
