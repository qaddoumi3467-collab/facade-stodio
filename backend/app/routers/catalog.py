from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import calculations, models, schemas
from app.db import Base, get_session

SessionDep = Annotated[Session, Depends(get_session)]

router = APIRouter(prefix="/api")


def _get_or_404(session: Session, model: type[Base], item_id: int):
    item = session.get(model, item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return item


def _commit(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Duplicate code, or the item is still used by another record",
        ) from exc


def _check_system(session: Session, system_id: int | None) -> None:
    if system_id is not None and session.get(models.ProfileSystem, system_id) is None:
        raise HTTPException(422, "Unknown system_id")


def add_crud(
    path: str,
    model: type[Base],
    schema_in: type[BaseModel],
    schema_out: type[BaseModel],
    search_fields: tuple[str, ...],
    order_by: str,
) -> None:
    """Register list / get / create / update / delete routes for one table.

    ``GET {path}?q=...`` searches the given fields (English, Arabic, code), and
    ``?system_id=`` filters tables that belong to a profile system.
    """
    has_system = hasattr(model, "system_id")

    @router.get(path, response_model=list[schema_out], name=f"list_{path}")
    def list_items(
        session: SessionDep,
        q: str | None = None,
        system_id: int | None = Query(default=None),
    ):
        stmt = select(model).order_by(getattr(model, order_by))
        if q:
            pattern = f"%{q}%"
            stmt = stmt.where(
                or_(*(getattr(model, f).ilike(pattern) for f in search_fields))
            )
        if system_id is not None and has_system:
            stmt = stmt.where(model.system_id == system_id)
        return session.scalars(stmt).all()

    @router.get(f"{path}/{{item_id}}", response_model=schema_out, name=f"get_{path}")
    def get_item(item_id: int, session: SessionDep):
        return _get_or_404(session, model, item_id)

    @router.post(
        path,
        response_model=schema_out,
        status_code=status.HTTP_201_CREATED,
        name=f"create_{path}",
    )
    def create_item(data: schema_in, session: SessionDep):  # type: ignore[valid-type]
        if has_system:
            _check_system(session, data.system_id)
        item = model(**data.model_dump())
        session.add(item)
        _commit(session)
        return item

    @router.put(f"{path}/{{item_id}}", response_model=schema_out, name=f"update_{path}")
    def update_item(item_id: int, data: schema_in, session: SessionDep):  # type: ignore[valid-type]
        item = _get_or_404(session, model, item_id)
        if has_system:
            _check_system(session, data.system_id)
        for key, value in data.model_dump().items():
            setattr(item, key, value)
        _commit(session)
        return item

    @router.delete(
        f"{path}/{{item_id}}",
        status_code=status.HTTP_204_NO_CONTENT,
        name=f"delete_{path}",
    )
    def delete_item(item_id: int, session: SessionDep):
        session.delete(_get_or_404(session, model, item_id))
        _commit(session)


add_crud(
    "/systems",
    models.ProfileSystem,
    schemas.ProfileSystemIn,
    schemas.ProfileSystemOut,
    ("code", "name_en", "name_ar", "manufacturer"),
    "code",
)
add_crud(
    "/profiles",
    models.Profile,
    schemas.ProfileIn,
    schemas.ProfileOut,
    ("article_no", "name_en", "name_ar"),
    "article_no",
)
add_crud(
    "/glass",
    models.GlassType,
    schemas.GlassTypeIn,
    schemas.GlassTypeOut,
    ("code", "name_en", "name_ar", "build_up"),
    "code",
)
add_crud(
    "/hardware",
    models.HardwareItem,
    schemas.HardwareItemIn,
    schemas.HardwareItemOut,
    ("article_no", "name_en", "name_ar"),
    "article_no",
)


@router.get("/profiles/{item_id}/piece", response_model=schemas.ProfilePieceOut)
def profile_piece(
    item_id: int, session: SessionDep, length_mm: float = Query(gt=0, le=100_000)
):
    """Weight and price of one piece of this profile cut to ``length_mm``."""
    profile = _get_or_404(session, models.Profile, item_id)
    price = None
    if profile.price_per_m is not None:
        price = calculations.profile_price(profile.price_per_m, length_mm)
    return schemas.ProfilePieceOut(
        length_mm=length_mm,
        weight_kg=calculations.profile_weight_kg(profile.weight_kg_per_m, length_mm),
        price=price,
    )


@router.get("/glass/{item_id}/pane", response_model=schemas.GlassPaneOut)
def glass_pane(
    item_id: int,
    session: SessionDep,
    width_mm: float = Query(gt=0, le=100_000),
    height_mm: float = Query(gt=0, le=100_000),
):
    """Area, weight and price of one pane of this glass type."""
    glass = _get_or_404(session, models.GlassType, item_id)
    price = None
    if glass.price_per_m2 is not None:
        price = calculations.glass_price(glass.price_per_m2, width_mm, height_mm)
    return schemas.GlassPaneOut(
        width_mm=width_mm,
        height_mm=height_mm,
        area_m2=calculations.glass_area_m2(width_mm, height_mm),
        weight_kg=calculations.glass_weight_kg(
            glass.glass_thickness_mm, width_mm, height_mm
        ),
        price=price,
    )
