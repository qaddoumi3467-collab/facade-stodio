"""Element designer: save windows and doors, and work out their drawing,
cut list and glass list from the catalog."""

from collections import Counter
from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import calculations, designer, models, schemas
from app.routers.catalog import SessionDep, _commit, _get_or_404

router = APIRouter(prefix="/api/elements")

# Which catalog roles each profile choice accepts. Mullion and transom
# profiles are often the same extrusion, so either fits both.
PROFILE_CHOICES = {
    "frame_profile_id": ("frame", {models.ProfileRole.frame}),
    "mullion_profile_id": (
        "mullion",
        {models.ProfileRole.mullion, models.ProfileRole.transom},
    ),
    "transom_profile_id": (
        "transom",
        {models.ProfileRole.transom, models.ProfileRole.mullion},
    ),
    "sash_profile_id": ("sash", {models.ProfileRole.sash}),
    "bead_profile_id": ("glazing_bead", {models.ProfileRole.glazing_bead}),
}


# Cut list order, as the workshop builds: outer frame first.
ROLE_ORDER = ["frame", "mullion", "transom", "sash", "glazing_bead"]


def _error(code: str, message: str) -> HTTPException:
    return HTTPException(422, {"code": code, "message": message})


def _field_glass_ids(node) -> set[int]:
    if isinstance(node, schemas.FieldNode):
        return {node.glass_id} if node.glass_id is not None else set()
    return set().union(*(_field_glass_ids(c) for c in node.children))


def _load(session: Session, data: schemas.ElementIn):
    """Check the element's catalog choices and return them: the system, the
    chosen profile for each role, and the glass types by id."""
    system = session.get(models.ProfileSystem, data.system_id)
    if system is None:
        raise _error("unknown_system", "Unknown system")

    profiles: dict[str, models.Profile] = {}
    for key, (role, allowed) in PROFILE_CHOICES.items():
        profile_id = getattr(data, key)
        if profile_id is None:
            continue
        profile = session.get(models.Profile, profile_id)
        if profile is None:
            raise _error("unknown_profile", f"Unknown profile for {role}")
        if profile.system_id != system.id:
            raise _error(
                "profile_wrong_system",
                f"Profile {profile.article_no} is not in system {system.code}",
            )
        if profile.role not in allowed:
            raise _error(
                "profile_wrong_role",
                f"Profile {profile.article_no} cannot be used as {role}",
            )
        profiles[role] = profile

    glass_ids = {data.glass_id} | _field_glass_ids(data.layout)
    glass = {
        g.id: g
        for g in session.scalars(
            select(models.GlassType).where(models.GlassType.id.in_(glass_ids))
        )
    }
    if len(glass) != len(glass_ids):
        raise _error("unknown_glass", "Unknown glass type")
    return system, profiles, glass


def _face(profiles: dict[str, models.Profile], role: str) -> Decimal | None:
    profile = profiles.get(role)
    return None if profile is None else profile.height_mm


def calculate(session: Session, data: schemas.ElementIn) -> schemas.ElementCalculationOut:
    system, profiles, glass = _load(session, data)
    faces = designer.Faces(
        frame=profiles["frame"].height_mm,
        mullion=_face(profiles, "mullion"),
        transom=_face(profiles, "transom"),
        sash=_face(profiles, "sash"),
        bead="glazing_bead" in profiles,
        sash_overlap=system.sash_overlap_mm,
        glass_bite=system.glass_bite_mm,
    )
    try:
        result = designer.design(data.width_mm, data.height_mm, data.layout, faces)
    except designer.DesignError as exc:
        raise _error(exc.code, exc.message) from exc

    profile_weight = glass_weight = area_total = price_total = Decimal(0)
    price_complete = True

    cut_lines = []
    pieces = Counter(result.pieces)
    for piece, qty in sorted(
        pieces.items(), key=lambda kv: (ROLE_ORDER.index(kv[0].role), -kv[0].length)
    ):
        profile = profiles[piece.role]
        weight = calculations.profile_weight_kg(profile.weight_kg_per_m, piece.length) * qty
        price = None
        if profile.price_per_m is None:
            price_complete = False
        else:
            price = calculations.profile_price(profile.price_per_m, piece.length) * qty
            price_total += price
        profile_weight += weight
        cut_lines.append(
            schemas.CutLineOut(
                profile_id=profile.id,
                article_no=profile.article_no,
                name_en=profile.name_en,
                name_ar=profile.name_ar,
                role=piece.role,
                length_mm=piece.length,
                angle_start=piece.angle_start,
                angle_end=piece.angle_end,
                quantity=qty,
                weight_kg=weight,
                price=price,
            )
        )

    fields_out = []
    panes: Counter = Counter()
    for f in result.fields:
        glass_id = f.glass_id if f.glass_id is not None else data.glass_id
        panes[(glass_id, f.glass_width, f.glass_height)] += 1
        fields_out.append(
            schemas.FieldOut(
                path=list(f.path),
                opening=f.opening,
                glass_id=glass_id,
                clear=_rect(f.clear),
                sash=_rect(f.sash) if f.sash else None,
                glass_width_mm=f.glass_width,
                glass_height_mm=f.glass_height,
            )
        )

    glass_lines = []
    for (glass_id, w, h), qty in sorted(
        panes.items(), key=lambda kv: (kv[0][0], -kv[0][1], -kv[0][2])
    ):
        g = glass[glass_id]
        area = calculations.glass_area_m2(w, h) * qty
        weight = calculations.glass_weight_kg(g.glass_thickness_mm, w, h) * qty
        price = None
        if g.price_per_m2 is None:
            price_complete = False
        else:
            price = calculations.glass_price(g.price_per_m2, w, h) * qty
            price_total += price
        area_total += area
        glass_weight += weight
        glass_lines.append(
            schemas.GlassLineOut(
                glass_id=g.id,
                code=g.code,
                name_en=g.name_en,
                name_ar=g.name_ar,
                width_mm=w,
                height_mm=h,
                quantity=qty,
                area_m2=area,
                weight_kg=weight,
                price=price,
            )
        )

    return schemas.ElementCalculationOut(
        geometry=schemas.GeometryOut(
            width_mm=result.width,
            height_mm=result.height,
            frame_face_mm=faces.frame,
            sash_face_mm=faces.sash,
            dividers=[
                schemas.DividerOut(
                    path=list(d.path),
                    direction=d.direction,
                    rect=_rect(d.rect),
                    length_mm=d.length,
                )
                for d in result.dividers
            ],
            fields=fields_out,
        ),
        profiles=cut_lines,
        glass=glass_lines,
        totals=schemas.TotalsOut(
            profile_weight_kg=profile_weight,
            glass_weight_kg=glass_weight,
            glass_area_m2=area_total,
            weight_kg=profile_weight + glass_weight,
            price=price_total,
            price_complete=price_complete,
        ),
    )


def _rect(r: designer.Rect) -> schemas.RectOut:
    return schemas.RectOut(x=r.x, y=r.y, width=r.width, height=r.height)


@router.post("/calculate", response_model=schemas.ElementCalculationOut)
def calculate_element(data: schemas.ElementIn, session: SessionDep):
    """Drawing, cut list and glass list for an element, without saving it."""
    return calculate(session, data)


@router.get("", response_model=list[schemas.ElementOut])
def list_elements(session: SessionDep):
    stmt = select(models.Element).order_by(models.Element.position, models.Element.id)
    return session.scalars(stmt).all()


@router.get("/{item_id}", response_model=schemas.ElementOut)
def get_element(item_id: int, session: SessionDep):
    return _get_or_404(session, models.Element, item_id)


@router.get("/{item_id}/calculation", response_model=schemas.ElementCalculationOut)
def element_calculation(item_id: int, session: SessionDep):
    element = _get_or_404(session, models.Element, item_id)
    return calculate(session, schemas.ElementIn.model_validate(element, from_attributes=True))


@router.post("", response_model=schemas.ElementOut, status_code=status.HTTP_201_CREATED)
def create_element(data: schemas.ElementIn, session: SessionDep):
    calculate(session, data)  # refuse drawings that cannot be built
    element = models.Element(**data.model_dump(mode="json"))
    session.add(element)
    _commit(session)
    session.refresh(element)
    return element


@router.put("/{item_id}", response_model=schemas.ElementOut)
def update_element(item_id: int, data: schemas.ElementIn, session: SessionDep):
    element = _get_or_404(session, models.Element, item_id)
    calculate(session, data)
    for key, value in data.model_dump(mode="json").items():
        setattr(element, key, value)
    _commit(session)
    session.refresh(element)
    return element


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_element(item_id: int, session: SessionDep):
    session.delete(_get_or_404(session, models.Element, item_id))
    _commit(session)
