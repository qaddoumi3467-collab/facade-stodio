"""Element designer geometry: where every frame, divider, sash and pane sits
and how long each profile piece is cut.

All sizes are in millimetres, measured from the top-left outer corner of the
element. The rules:

* Outer frame: four pieces mitred at 45°, top and bottom as long as the
  element width, left and right as long as its height.
* Mullions and transoms: square cut (90°), running between the faces of
  whatever holds them (the frame or another divider). A divider is centred
  on the line between two parts, so each side loses half its face width.
* Opening fields get a sash: its outer size is the visible opening plus the
  system's sash overlap on each side, four pieces mitred at 45°.
* Glass is the opening that holds it (the frame field for fixed glass, the
  inside of the sash otherwise) plus the system's glass bite on each side.
* Glazing beads, when chosen, run around that same opening, mitred at 45°.

Sliding fields are drawn and cut like other opening fields for now.
"""

from dataclasses import dataclass, field
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from app.schemas import FieldNode, OpeningType, SplitNode

_MM = Decimal("0.1")
_ZERO = Decimal(0)


class DesignError(ValueError):
    """The drawing cannot be built. ``code`` lets the screen translate it."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _d(value) -> Decimal:
    return value if isinstance(value, Decimal) else Decimal(str(value))


def mm(value: Decimal) -> Decimal:
    """Round to 0.1 mm, half up, for printing and cutting."""
    return value.quantize(_MM, ROUND_HALF_UP)


@dataclass(frozen=True)
class Rect:
    x: Decimal
    y: Decimal
    width: Decimal
    height: Decimal

    def inset(self, left: Decimal, top: Decimal, right: Decimal, bottom: Decimal) -> "Rect":
        return Rect(
            self.x + left,
            self.y + top,
            self.width - left - right,
            self.height - top - bottom,
        )

    def grow(self, by: Decimal) -> "Rect":
        return self.inset(-by, -by, -by, -by)

    def rounded(self) -> "Rect":
        return Rect(mm(self.x), mm(self.y), mm(self.width), mm(self.height))


@dataclass(frozen=True)
class Faces:
    """Visible face widths of the chosen profiles, plus the system's
    construction values. ``None`` means no profile of that kind was chosen."""

    frame: Decimal
    mullion: Decimal | None = None
    transom: Decimal | None = None
    sash: Decimal | None = None
    bead: bool = False
    sash_overlap: Decimal = _ZERO
    glass_bite: Decimal = _ZERO


@dataclass(frozen=True)
class Piece:
    role: str  # frame, mullion, transom, sash or glazing_bead
    length: Decimal
    angle_start: int
    angle_end: int


@dataclass(frozen=True)
class Divider:
    path: tuple[int, ...]  # the split this divider belongs to
    direction: str
    rect: Rect
    length: Decimal


@dataclass(frozen=True)
class Field:
    path: tuple[int, ...]
    opening: OpeningType
    glass_id: int | None  # the field's own choice; None means the element's
    clear: Rect
    sash: Rect | None
    glass_width: Decimal
    glass_height: Decimal


@dataclass
class Design:
    width: Decimal
    height: Decimal
    faces: Faces
    dividers: list[Divider] = field(default_factory=list)
    fields: list[Field] = field(default_factory=list)
    pieces: list[Piece] = field(default_factory=list)


def resolve_sizes(total, sizes) -> list[Decimal]:
    """Turn the sizes of a split's parts into numbers that add up to
    ``total``. Blank sizes share what the others leave, rounded down to
    0.1 mm, and the last blank part takes the remainder."""
    total = _d(total)
    given = [None if s is None else _d(s) for s in sizes]
    for s in given:
        if s is not None and s <= 0:
            raise DesignError("size_not_positive", "Every size must be more than 0 mm")
    used = sum((s for s in given if s is not None), _ZERO)
    blanks = sum(1 for s in given if s is None)
    if blanks == 0:
        if used != total:
            raise DesignError(
                "sizes_mismatch",
                f"Sizes add up to {used} mm but the space is {mm(total)} mm",
            )
        return given
    rest = total - used
    share = (rest / blanks).quantize(_MM, ROUND_DOWN)
    if share <= 0:
        raise DesignError(
            "sizes_too_big",
            f"Sizes add up to {used} mm, leaving no room in {mm(total)} mm",
        )
    out: list[Decimal] = []
    seen = 0
    for s in given:
        if s is not None:
            out.append(s)
            continue
        seen += 1
        out.append(share if seen < blanks else rest - share * (blanks - 1))
    return out


def _four_sides(role: str, rect: Rect) -> list[Piece]:
    """Four mitred pieces around a rectangle: top, bottom, left, right."""
    return [
        Piece(role, mm(rect.width), 45, 45),
        Piece(role, mm(rect.width), 45, 45),
        Piece(role, mm(rect.height), 45, 45),
        Piece(role, mm(rect.height), 45, 45),
    ]


def design(width, height, layout: FieldNode | SplitNode, faces: Faces) -> Design:
    width, height = _d(width), _d(height)
    if width <= 0 or height <= 0:
        raise DesignError("size_not_positive", "Width and height must be more than 0 mm")
    if faces.frame * 2 >= width or faces.frame * 2 >= height:
        raise DesignError("element_too_small", "The element is too small for its frame")

    result = Design(width, height, faces)
    outer = Rect(_ZERO, _ZERO, width, height)
    result.pieces += _four_sides("frame", outer)
    f = faces.frame
    _walk(result, layout, outer, (f, f, f, f), ())
    return result


def _walk(result: Design, node, axis: Rect, insets: tuple, path: tuple[int, ...]) -> None:
    clear = axis.inset(*insets)
    if clear.width <= 0 or clear.height <= 0:
        raise DesignError("field_too_small", "A field is too small for its profiles")
    if isinstance(node, FieldNode):
        _field(result, node, clear, path)
        return

    faces = result.faces
    vertical = node.direction == "vertical"
    role = "mullion" if vertical else "transom"
    face = faces.mullion if vertical else faces.transom
    if face is None:
        raise DesignError(f"{role}_missing", f"Choose a {role} profile")
    half = face / 2
    sizes = resolve_sizes(axis.width if vertical else axis.height, node.sizes)
    left, top, right, bottom = insets
    pos = axis.x if vertical else axis.y
    last = len(sizes) - 1
    for i, (size, child) in enumerate(zip(sizes, node.children)):
        if vertical:
            child_axis = Rect(pos, axis.y, size, axis.height)
            child_insets = (left if i == 0 else half, top, right if i == last else half, bottom)
        else:
            child_axis = Rect(axis.x, pos, axis.width, size)
            child_insets = (left, top if i == 0 else half, right, bottom if i == last else half)
        _walk(result, child, child_axis, child_insets, path + (i,))
        pos += size
        if i == last:
            continue
        if vertical:
            rect = Rect(pos - half, clear.y, face, clear.height)
            length = clear.height
        else:
            rect = Rect(clear.x, pos - half, clear.width, face)
            length = clear.width
        result.dividers.append(Divider(path, node.direction, rect.rounded(), mm(length)))
        result.pieces.append(Piece(role, mm(length), 90, 90))


def _field(result: Design, node: FieldNode, clear: Rect, path: tuple[int, ...]) -> None:
    faces = result.faces
    sash = None
    holder = clear
    if node.opening != OpeningType.fixed:
        if faces.sash is None:
            raise DesignError("sash_missing", "Choose a sash profile for opening fields")
        sash = clear.grow(faces.sash_overlap)
        holder = sash.grow(-faces.sash)
        if holder.width <= 0 or holder.height <= 0:
            raise DesignError("sash_too_small", "A field is too small for its sash")
        result.pieces += _four_sides("sash", sash)
    if faces.bead:
        result.pieces += _four_sides("glazing_bead", holder)
    glass = holder.grow(faces.glass_bite)
    result.fields.append(
        Field(
            path=path,
            opening=node.opening,
            glass_id=node.glass_id,
            clear=clear.rounded(),
            sash=sash.rounded() if sash else None,
            glass_width=mm(glass.width),
            glass_height=mm(glass.height),
        )
    )
