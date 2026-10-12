"""Catalog calculations. Inputs are in millimetres; results are rounded
half-up so the same input always gives the same printed number."""

from decimal import ROUND_HALF_UP, Decimal

# Float glass weighs 2.5 kg per square metre for every millimetre of thickness.
GLASS_KG_PER_M2_PER_MM = Decimal("2.5")

_KG = Decimal("0.001")
_M2 = Decimal("0.0001")
_MONEY = Decimal("0.01")


def _d(value: Decimal | int | float | str) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _positive(name: str, value: Decimal) -> Decimal:
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def profile_weight_kg(weight_kg_per_m, length_mm) -> Decimal:
    """Weight of one profile piece cut to ``length_mm``."""
    length = _positive("length_mm", _d(length_mm))
    return (_d(weight_kg_per_m) * length / 1000).quantize(_KG, ROUND_HALF_UP)


def profile_price(price_per_m, length_mm) -> Decimal:
    """Price of one profile piece cut to ``length_mm``."""
    length = _positive("length_mm", _d(length_mm))
    return (_d(price_per_m) * length / 1000).quantize(_MONEY, ROUND_HALF_UP)


def glass_area_m2(width_mm, height_mm) -> Decimal:
    width = _positive("width_mm", _d(width_mm))
    height = _positive("height_mm", _d(height_mm))
    return (width * height / 1_000_000).quantize(_M2, ROUND_HALF_UP)


def glass_weight_kg(glass_thickness_mm, width_mm, height_mm) -> Decimal:
    """Weight of a glass pane or unit. ``glass_thickness_mm`` is the sum of
    the glass panes only, without the air gap."""
    width = _positive("width_mm", _d(width_mm))
    height = _positive("height_mm", _d(height_mm))
    area = width * height / 1_000_000
    weight = area * _d(glass_thickness_mm) * GLASS_KG_PER_M2_PER_MM
    return weight.quantize(_KG, ROUND_HALF_UP)


def glass_price(price_per_m2, width_mm, height_mm) -> Decimal:
    area = glass_area_m2(width_mm, height_mm)
    return (_d(price_per_m2) * area).quantize(_MONEY, ROUND_HALF_UP)


def glass_thickness_from_build_up(build_up: str) -> Decimal:
    """Sum of glass panes in a build-up such as ``6-16-6`` or ``4-12-4-12-4``.

    Panes and gaps alternate, so the panes are the odd positions.
    """
    parts = [p.strip() for p in build_up.split("-")]
    if len(parts) % 2 == 0 or any(not p for p in parts):
        raise ValueError(f"build-up must alternate pane-gap-pane: {build_up!r}")
    try:
        values = [Decimal(p) for p in parts]
    except ArithmeticError as exc:
        raise ValueError(f"build-up has a non-number: {build_up!r}") from exc
    for v in values:
        _positive("each layer", v)
    return sum(values[0::2], Decimal(0))
