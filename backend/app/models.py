"""Catalog data: profile systems, profiles, glass and hardware.

All lengths and thicknesses are in millimetres. Every item carries an
English and an Arabic name.
"""

import enum
from decimal import Decimal

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ProfileRole(str, enum.Enum):
    frame = "frame"
    sash = "sash"
    mullion = "mullion"
    transom = "transom"
    glazing_bead = "glazing_bead"
    threshold = "threshold"
    coupling = "coupling"
    interlock = "interlock"
    adaptor = "adaptor"
    cleat = "cleat"
    flyscreen = "flyscreen"
    other = "other"


class HardwareCategory(str, enum.Enum):
    handle = "handle"
    hinge = "hinge"
    lock = "lock"
    gasket = "gasket"
    corner_cleat = "corner_cleat"
    roller = "roller"
    accessory = "accessory"
    other = "other"


class HardwareUnit(str, enum.Enum):
    piece = "piece"
    set = "set"
    metre = "metre"


def _enum(e: type[enum.Enum]) -> Enum:
    return Enum(e, native_enum=False, length=32, validate_strings=True)


class ProfileSystem(Base):
    """A product series, e.g. a thermally broken casement window system."""

    __tablename__ = "profile_systems"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name_en: Mapped[str] = mapped_column(String(200))
    name_ar: Mapped[str] = mapped_column(String(200))
    manufacturer: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    thermal_break: Mapped[bool] = mapped_column(default=False)
    # How far a sash overlaps the frame opening on each side.
    sash_overlap_mm: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=0, server_default="0"
    )
    # How far the glass edge goes in under the profile on each side, past
    # the visible opening.
    glass_bite_mm: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), default=0, server_default="0"
    )

    profiles: Mapped[list["Profile"]] = relationship(back_populates="system")


class Profile(Base):
    """An aluminium extrusion sold in bars."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    system_id: Mapped[int] = mapped_column(
        ForeignKey("profile_systems.id", ondelete="RESTRICT"), index=True
    )
    article_no: Mapped[str] = mapped_column(String(64), unique=True)
    name_en: Mapped[str] = mapped_column(String(200))
    name_ar: Mapped[str] = mapped_column(String(200))
    role: Mapped[ProfileRole] = mapped_column(_enum(ProfileRole))
    # width_mm is the depth of the profile through the wall; height_mm is
    # its visible face width, which the element designer uses.
    width_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    height_mm: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    weight_kg_per_m: Mapped[Decimal] = mapped_column(Numeric(8, 3))
    bar_length_mm: Mapped[int] = mapped_column(default=6000)
    price_per_m: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    system: Mapped[ProfileSystem] = relationship(back_populates="profiles")


class GlassType(Base):
    """A glass unit, e.g. double glazing 6-16-6."""

    __tablename__ = "glass_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True)
    name_en: Mapped[str] = mapped_column(String(200))
    name_ar: Mapped[str] = mapped_column(String(200))
    build_up: Mapped[str | None] = mapped_column(String(100))
    total_thickness_mm: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    # Sum of the glass panes only (no air gap), used for weight.
    glass_thickness_mm: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    u_value: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    price_per_m2: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))


class HardwareItem(Base):
    """Handles, hinges, locks, gaskets and other accessories."""

    __tablename__ = "hardware_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    system_id: Mapped[int | None] = mapped_column(
        ForeignKey("profile_systems.id", ondelete="SET NULL"), index=True
    )
    article_no: Mapped[str] = mapped_column(String(64), unique=True)
    name_en: Mapped[str] = mapped_column(String(200))
    name_ar: Mapped[str] = mapped_column(String(200))
    category: Mapped[HardwareCategory] = mapped_column(_enum(HardwareCategory))
    unit: Mapped[HardwareUnit] = mapped_column(
        _enum(HardwareUnit), default=HardwareUnit.piece
    )
    price_per_unit: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))


class Element(Base):
    """A window or door drawn in the element designer.

    ``layout`` is a tree of fields and splits (see ``app.schemas.Node``).
    Profile and glass choices point into the catalog.
    """

    __tablename__ = "elements"

    id: Mapped[int] = mapped_column(primary_key=True)
    position: Mapped[str] = mapped_column(String(64), default="")
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[int] = mapped_column(default=1)
    system_id: Mapped[int] = mapped_column(
        ForeignKey("profile_systems.id", ondelete="RESTRICT"), index=True
    )
    width_mm: Mapped[Decimal] = mapped_column(Numeric(8, 1))
    height_mm: Mapped[Decimal] = mapped_column(Numeric(8, 1))
    frame_profile_id: Mapped[int] = mapped_column(
        ForeignKey("profiles.id", ondelete="RESTRICT")
    )
    mullion_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="RESTRICT")
    )
    transom_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="RESTRICT")
    )
    sash_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="RESTRICT")
    )
    bead_profile_id: Mapped[int | None] = mapped_column(
        ForeignKey("profiles.id", ondelete="RESTRICT")
    )
    glass_id: Mapped[int] = mapped_column(
        ForeignKey("glass_types.id", ondelete="RESTRICT")
    )
    layout: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
