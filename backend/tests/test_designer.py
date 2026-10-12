from decimal import Decimal as D

import pytest

from app.designer import DesignError, Faces, Piece, Rect, design, resolve_sizes
from app.schemas import FieldNode, SplitNode

# Sample W70 system: frame face 55, mullion 82, sash 67, overlap 8, bite 10.
W70 = Faces(
    frame=D(55), mullion=D(82), transom=D(82), sash=D(67),
    sash_overlap=D(8), glass_bite=D(10),
)


def two_part(left="fixed", right="turn_right", sizes=(900, None)):
    return SplitNode(
        direction="vertical",
        sizes=list(sizes),
        children=[FieldNode(opening=left), FieldNode(opening=right)],
    )


def pieces(result, role):
    return sorted(((p.length, p.angle_start, p.angle_end) for p in result.pieces if p.role == role), reverse=True)


# Sizes

def test_blank_sizes_share_the_rest():
    assert resolve_sizes(1800, [900, None]) == [D(900), D(900)]
    assert resolve_sizes(1000, [None, None, None]) == [D("333.3"), D("333.3"), D("333.4")]
    assert resolve_sizes(1000, [200, None, 300, None]) == [D(200), D(250), D(300), D(250)]


def test_shares_always_add_up_to_the_total():
    for total in (1000, 1234.5, 999.9, 3001):
        for n in range(2, 8):
            assert sum(resolve_sizes(total, [None] * n)) == D(str(total))


@pytest.mark.parametrize(
    "total, sizes, code",
    [
        (1000, [500, 400], "sizes_mismatch"),
        (1000, [600, 400, None], "sizes_too_big"),
        (1000, [1200, None], "sizes_too_big"),
        (1000, [0, None], "size_not_positive"),
        (1000, [-5, None], "size_not_positive"),
    ],
)
def test_bad_sizes(total, sizes, code):
    with pytest.raises(DesignError) as err:
        resolve_sizes(total, sizes)
    assert err.value.code == code


# A single fixed field

def test_single_fixed_field():
    result = design(1200, 1000, FieldNode(), W70)
    assert pieces(result, "frame") == [(D(1200), 45, 45)] * 2 + [(D(1000), 45, 45)] * 2
    [field] = result.fields
    assert field.clear == Rect(D(55), D(55), D(1090), D(890))
    assert field.sash is None
    # Glass goes 10 mm under the frame on every side.
    assert (field.glass_width, field.glass_height) == (D(1110), D(910))
    assert result.dividers == []


# Two parts with a mullion, worked out by hand

def test_mullion_window():
    result = design(1800, 1500, two_part(), W70)

    # Mullion runs between the top and bottom frame faces, square cut.
    [mullion] = result.dividers
    assert mullion.length == D(1390)
    assert mullion.rect == Rect(D(859), D(55), D(82), D(1390))
    assert pieces(result, "mullion") == [(D(1390), 90, 90)]

    left, right = result.fields
    # 900 to the mullion centre, less the frame face and half the mullion.
    assert left.clear == Rect(D(55), D(55), D(804), D(1390))
    assert (left.glass_width, left.glass_height) == (D(824), D(1410))

    assert right.clear == Rect(D(941), D(55), D(804), D(1390))
    # Sash overlaps 8 mm each side; glass sits inside its 67 mm face.
    assert right.sash == Rect(D(933), D(47), D(820), D(1406))
    assert pieces(result, "sash") == [(D(1406), 45, 45)] * 2 + [(D(820), 45, 45)] * 2
    assert (right.glass_width, right.glass_height) == (D(706), D(1292))


def test_glazing_beads_follow_the_glass_opening():
    faces = Faces(**{**W70.__dict__, "bead": True})
    result = design(1800, 1500, two_part(), faces)
    # Fixed field: beads around the frame opening. Opening field: around the
    # inside of the sash.
    assert pieces(result, "glazing_bead") == sorted(
        [(D(1390), 45, 45)] * 2 + [(D(804), 45, 45)] * 2
        + [(D(1272), 45, 45)] * 2 + [(D(686), 45, 45)] * 2,
        reverse=True,
    )


def test_rows_and_columns():
    """A transom at 400 mm, with the bottom row split in three."""
    faces = Faces(frame=D(50), mullion=D(60), transom=D(60))
    layout = SplitNode(
        direction="horizontal",
        sizes=[400, None],
        children=[
            FieldNode(),
            SplitNode(direction="vertical", sizes=[None, None, None],
                      children=[FieldNode(), FieldNode(), FieldNode()]),
        ],
    )
    result = design(1000, 1500, layout, faces)

    transom, m1, m2 = sorted(result.dividers, key=lambda d: d.path)
    assert transom.direction == "horizontal"
    assert transom.rect == Rect(D(50), D(370), D(900), D(60))
    assert transom.length == D(900)
    # Mullions stand on the transom: 1450 - 430.
    assert m1.length == m2.length == D(1020)
    assert m1.rect.x == D("303.3")
    assert pieces(result, "transom") == [(D(900), 90, 90)]
    assert pieces(result, "mullion") == [(D(1020), 90, 90)] * 2

    top, c0, c1, c2 = result.fields
    assert top.path == (0,)
    assert top.clear == Rect(D(50), D(50), D(900), D(320))
    assert [c.path for c in (c0, c1, c2)] == [(1, 0), (1, 1), (1, 2)]
    assert [c.clear.width for c in (c0, c1, c2)] == [D("253.3"), D("273.3"), D("253.4")]
    assert all(c.clear.height == D(1020) for c in (c0, c1, c2))


def test_identical_pieces_are_equal():
    """The cut list groups pieces by value, so equal cuts must compare equal."""
    result = design(1800, 1500, two_part("turn_left", "turn_right", (None, None)), W70)
    sash = [p for p in result.pieces if p.role == "sash"]
    assert len(sash) == 8
    assert len(set(sash)) == 2
    assert Piece("sash", D(820), 45, 45) in sash


def test_lengths_are_rounded_to_a_tenth():
    result = design(1000.04, 1000.05, FieldNode(), W70)
    assert pieces(result, "frame") == [(D("1000.1"), 45, 45)] * 2 + [(D("1000.0"), 45, 45)] * 2


# Things that cannot be built

@pytest.mark.parametrize(
    "faces, layout, size, code",
    [
        (W70, FieldNode(), (100, 1000), "element_too_small"),
        (Faces(frame=D(55)), two_part("fixed", "fixed"), (1800, 1500), "mullion_missing"),
        (
            Faces(frame=D(55)),
            SplitNode(direction="horizontal", sizes=[None, None], children=[FieldNode(), FieldNode()]),
            (1800, 1500),
            "transom_missing",
        ),
        (Faces(frame=D(55), mullion=D(82)), two_part(), (1800, 1500), "sash_missing"),
        (W70, two_part(sizes=(90, None)), (1800, 1500), "field_too_small"),
        (W70, two_part(sizes=(None, 160)), (1800, 1500), "sash_too_small"),
    ],
)
def test_impossible_designs(faces, layout, size, code):
    with pytest.raises(DesignError) as err:
        design(*size, layout, faces)
    assert err.value.code == code
