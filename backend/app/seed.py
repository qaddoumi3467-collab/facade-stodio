"""Load a small sample catalog so the app has something to show.

Run with ``python -m app.seed``. Items that already exist (same code or
article number) are skipped, so it is safe to run more than once. These are
example values for trying the app, not real manufacturer data.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Element, GlassType, HardwareItem, Profile, ProfileSystem

SYSTEMS = [
    dict(code="W70", name_en="Casement window 70 mm (thermal break)",
         name_ar="نافذة مفصلية ٧٠ مم (عازل حراري)", manufacturer="Sample",
         thermal_break=True, sash_overlap_mm=8, glass_bite_mm=10),
    dict(code="S120", name_en="Sliding system 120 mm", name_ar="نظام سحاب ١٢٠ مم",
         manufacturer="Sample", thermal_break=False, sash_overlap_mm=10,
         glass_bite_mm=8),
]

PROFILES = [
    dict(system="W70", article_no="W70-101", name_en="Outer frame 70",
         name_ar="حلق خارجي ٧٠", role="frame", width_mm=70, height_mm=55,
         weight_kg_per_m=1.245, price_per_m=9.80),
    dict(system="W70", article_no="W70-201", name_en="Sash 78",
         name_ar="ضلفة ٧٨", role="sash", width_mm=78, height_mm=67,
         weight_kg_per_m=1.412, price_per_m=11.20),
    dict(system="W70", article_no="W70-301", name_en="Mullion 70",
         name_ar="قاطع عمودي ٧٠", role="mullion", width_mm=70, height_mm=82,
         weight_kg_per_m=1.530, price_per_m=12.40),
    dict(system="W70", article_no="W70-501", name_en="Glazing bead 24",
         name_ar="كلبس زجاج ٢٤", role="glazing_bead", width_mm=24, height_mm=20,
         weight_kg_per_m=0.210, price_per_m=1.90),
    dict(system="S120", article_no="S120-101", name_en="Sliding frame 120",
         name_ar="حلق سحاب ١٢٠", role="frame", width_mm=120, height_mm=45,
         weight_kg_per_m=1.820, price_per_m=13.50),
    dict(system="S120", article_no="S120-201", name_en="Sliding sash 45",
         name_ar="ضلفة سحاب ٤٥", role="sash", width_mm=45, height_mm=80,
         weight_kg_per_m=1.150, price_per_m=8.70),
]

GLASS = [
    dict(code="SG6", name_en="Clear float 6 mm", name_ar="زجاج شفاف ٦ مم",
         build_up="6", total_thickness_mm=6, glass_thickness_mm=6,
         u_value=5.7, price_per_m2=18),
    dict(code="DG6166", name_en="Double glazing 6-16-6", name_ar="زجاج مزدوج ٦-١٦-٦",
         build_up="6-16-6", total_thickness_mm=28, glass_thickness_mm=12,
         u_value=2.7, price_per_m2=42),
    dict(code="DG4124LE", name_en="Double glazing 4-12-4 low-E",
         name_ar="زجاج مزدوج ٤-١٢-٤ عاكس حراري", build_up="4-12-4",
         total_thickness_mm=20, glass_thickness_mm=8, u_value=1.6, price_per_m2=55),
]

HARDWARE = [
    dict(system="W70", article_no="HW-H01", name_en="Window handle",
         name_ar="مقبض نافذة", category="handle", unit="piece", price_per_unit=6.5),
    dict(system="W70", article_no="HW-K01", name_en="Concealed hinge set",
         name_ar="طقم مفصلات مخفية", category="hinge", unit="set", price_per_unit=22),
    dict(system="S120", article_no="HW-R01", name_en="Sliding roller",
         name_ar="عجل سحاب", category="roller", unit="piece", price_per_unit=3.2),
    dict(system=None, article_no="HW-G01", name_en="EPDM glazing gasket",
         name_ar="جلدة زجاج EPDM", category="gasket", unit="metre", price_per_unit=0.45),
]

# A two-part window: fixed glass on the left, tilt-turn on the right.
ELEMENTS = [
    dict(position="W01", name="Living room window / نافذة الصالة", system="W70",
         width_mm=1800, height_mm=1500, frame="W70-101", mullion="W70-301",
         transom="W70-301", sash="W70-201", bead="W70-501", glass="DG6166",
         layout={"kind": "split", "direction": "vertical", "sizes": [900, None],
                 "children": [{"kind": "field", "opening": "fixed"},
                              {"kind": "field", "opening": "tilt_turn_right"}]}),
]


def seed(session: Session) -> None:
    systems = {s.code: s for s in session.scalars(select(ProfileSystem))}
    for data in SYSTEMS:
        if data["code"] not in systems:
            systems[data["code"]] = ProfileSystem(**data)
            session.add(systems[data["code"]])
    session.flush()

    existing = set(session.scalars(select(Profile.article_no)))
    for data in PROFILES:
        if data["article_no"] not in existing:
            data = dict(data)
            session.add(Profile(system_id=systems[data.pop("system")].id, **data))

    existing = set(session.scalars(select(GlassType.code)))
    for data in GLASS:
        if data["code"] not in existing:
            session.add(GlassType(**data))

    existing = set(session.scalars(select(HardwareItem.article_no)))
    for data in HARDWARE:
        if data["article_no"] not in existing:
            data = dict(data)
            code = data.pop("system")
            session.add(HardwareItem(system_id=systems[code].id if code else None, **data))
    session.flush()

    profiles = {p.article_no: p.id for p in session.scalars(select(Profile))}
    glass = {g.code: g.id for g in session.scalars(select(GlassType))}
    existing = set(session.scalars(select(Element.position)))
    for data in ELEMENTS:
        if data["position"] not in existing:
            data = dict(data)
            session.add(Element(
                system_id=systems[data.pop("system")].id,
                frame_profile_id=profiles[data.pop("frame")],
                mullion_profile_id=profiles[data.pop("mullion")],
                transom_profile_id=profiles[data.pop("transom")],
                sash_profile_id=profiles[data.pop("sash")],
                bead_profile_id=profiles[data.pop("bead")],
                glass_id=glass[data.pop("glass")],
                **data,
            ))

    session.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        seed(session)
    print("Sample catalog loaded.")
