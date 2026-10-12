import pytest
from sqlalchemy import select

from app import models
from app.seed import seed


@pytest.fixture
def cat(session):
    """The sample catalog, by code / article number."""
    seed(session)
    ids = {s.code: s.id for s in session.scalars(select(models.ProfileSystem))}
    ids |= {p.article_no: p.id for p in session.scalars(select(models.Profile))}
    ids |= {g.code: g.id for g in session.scalars(select(models.GlassType))}
    return ids


def element(cat, **overrides):
    """1800 x 1500 W70 window: fixed left, tilt-turn right, mullion at 900."""
    return {
        "position": "W02",
        "name": "نافذة غرفة النوم",
        "quantity": 2,
        "system_id": cat["W70"],
        "width_mm": 1800,
        "height_mm": 1500,
        "frame_profile_id": cat["W70-101"],
        "mullion_profile_id": cat["W70-301"],
        "sash_profile_id": cat["W70-201"],
        "glass_id": cat["DG6166"],
        "layout": {
            "kind": "split",
            "direction": "vertical",
            "sizes": [900, None],
            "children": [
                {"kind": "field", "opening": "fixed"},
                {"kind": "field", "opening": "tilt_turn_right"},
            ],
        },
        **overrides,
    }


def cut(body, role):
    return [
        (line["length_mm"], line["quantity"], line["weight_kg"], line["price"])
        for line in body["profiles"]
        if line["role"] == role
    ]


def test_calculate_cut_list_glass_and_totals(client, cat):
    r = client.post("/api/elements/calculate", json=element(cat))
    assert r.status_code == 200, r.text
    body = r.json()

    # Frame W70-101: 1.245 kg/m, 9.80 per m. Mitred 45/45.
    assert cut(body, "frame") == [(1800, 2, 4.482, 35.28), (1500, 2, 3.736, 29.4)]
    frame = body["profiles"][0]
    assert (frame["article_no"], frame["angle_start"], frame["angle_end"]) == ("W70-101", 45, 45)
    # Mullion W70-301: 1.53 kg/m, 12.40 per m, square cut.
    assert cut(body, "mullion") == [(1390, 1, 2.127, 17.24)]
    # Sash W70-201: 1.412 kg/m, 11.20 per m.
    assert cut(body, "sash") == [(1406, 2, 3.97, 31.5), (820, 2, 2.316, 18.36)]

    # DG6166: 12 mm of glass, 42 per m².
    assert [
        (g["width_mm"], g["height_mm"], g["quantity"], g["area_m2"], g["weight_kg"], g["price"])
        for g in body["glass"]
    ] == [(824, 1410, 1, 1.1618, 34.855, 48.8), (706, 1292, 1, 0.9122, 27.365, 38.31)]

    assert body["totals"] == {
        "profile_weight_kg": 16.631,
        "glass_weight_kg": 62.22,
        "glass_area_m2": 2.074,
        "weight_kg": 78.851,
        "price": 218.89,
        "price_complete": True,
    }

    geo = body["geometry"]
    assert (geo["width_mm"], geo["frame_face_mm"], geo["sash_face_mm"]) == (1800, 55, 67)
    assert [d["rect"] for d in geo["dividers"]] == [
        {"x": 859, "y": 55, "width": 82, "height": 1390}
    ]
    assert [(f["path"], f["opening"]) for f in geo["fields"]] == [
        ([0], "fixed"),
        ([1], "tilt_turn_right"),
    ]
    assert geo["fields"][1]["sash"] == {"x": 933, "y": 47, "width": 820, "height": 1406}


def test_cut_list_is_in_workshop_order(client, cat):
    data = element(cat, bead_profile_id=cat["W70-501"], transom_profile_id=cat["W70-301"])
    data["layout"]["children"][1] = {
        "kind": "split", "direction": "horizontal", "sizes": [None, None],
        "children": [{"kind": "field", "opening": "tilt"}, {"kind": "field"}],
    }
    body = client.post("/api/elements/calculate", json=data).json()
    roles = [line["role"] for line in body["profiles"]]
    assert list(dict.fromkeys(roles)) == ["frame", "mullion", "transom", "sash", "glazing_bead"]


def test_glass_override_per_field(client, cat):
    data = element(cat)
    data["layout"]["children"][0]["glass_id"] = cat["SG6"]
    body = client.post("/api/elements/calculate", json=data).json()
    assert sorted((g["code"], g["width_mm"]) for g in body["glass"]) == [
        ("DG6166", 706), ("SG6", 824)
    ]
    assert {f["glass_id"] for f in body["geometry"]["fields"]} == {cat["SG6"], cat["DG6166"]}


def test_glazing_beads_are_listed_when_chosen(client, cat):
    body = client.post(
        "/api/elements/calculate", json=element(cat, bead_profile_id=cat["W70-501"])
    ).json()
    assert [(line["length_mm"], line["quantity"]) for line in body["profiles"]
            if line["role"] == "glazing_bead"] == [(1390, 2), (1272, 2), (804, 2), (686, 2)]


def test_missing_price_is_flagged(client, cat, session):
    session.get(models.Profile, cat["W70-301"]).price_per_m = None
    session.flush()
    body = client.post("/api/elements/calculate", json=element(cat)).json()
    assert cut(body, "mullion")[0][3] is None
    assert body["totals"]["price"] == round(218.89 - 17.24, 2)
    assert body["totals"]["price_complete"] is False


@pytest.mark.parametrize(
    "overrides, code",
    [
        ({"system_id": 999999}, "unknown_system"),
        ({"frame_profile_id": "S120-101"}, "profile_wrong_system"),
        ({"frame_profile_id": "W70-201"}, "profile_wrong_role"),
        ({"mullion_profile_id": None}, "mullion_missing"),
        ({"sash_profile_id": None}, "sash_missing"),
        ({"glass_id": 999999}, "unknown_glass"),
        ({"width_mm": 90}, "element_too_small"),
    ],
)
def test_bad_elements_are_refused_with_a_code(client, cat, overrides, code):
    overrides = {k: cat.get(v, v) if isinstance(v, str) else v for k, v in overrides.items()}
    for url in ("/api/elements/calculate", "/api/elements"):
        r = client.post(url, json=element(cat, **overrides))
        assert r.status_code == 422, r.text
        assert r.json()["detail"]["code"] == code


def test_layout_shape_is_checked(client, cat):
    data = element(cat)
    data["layout"]["sizes"] = [900]
    assert client.post("/api/elements/calculate", json=data).status_code == 422

    deep = {"kind": "field"}
    for _ in range(9):
        deep = {"kind": "split", "direction": "vertical", "sizes": [None, None],
                "children": [deep, {"kind": "field"}]}
    assert client.post("/api/elements/calculate", json=element(cat, layout=deep)).status_code == 422


def test_save_load_update_delete(client, cat):
    r = client.post("/api/elements", json=element(cat))
    assert r.status_code == 201, r.text
    saved = r.json()
    assert saved["name"] == "نافذة غرفة النوم"
    assert saved["layout"]["children"][1]["opening"] == "tilt_turn_right"

    got = client.get(f"/api/elements/{saved['id']}").json()
    assert got["layout"] == saved["layout"]
    assert got["width_mm"] == 1800
    assert saved["id"] in [e["id"] for e in client.get("/api/elements").json()]

    calc = client.get(f"/api/elements/{saved['id']}/calculation").json()
    assert calc["totals"]["price"] == 218.89

    changed = element(cat, width_mm=2000, layout={"kind": "field", "opening": "turn_left"})
    r = client.put(f"/api/elements/{saved['id']}", json=changed)
    assert r.status_code == 200, r.text
    assert r.json()["layout"] == {"kind": "field", "opening": "turn_left", "glass_id": None}
    assert r.json()["width_mm"] == 2000

    # An update that cannot be built is refused and nothing changes.
    r = client.put(f"/api/elements/{saved['id']}", json=element(cat, width_mm=50))
    assert r.status_code == 422
    assert client.get(f"/api/elements/{saved['id']}").json()["width_mm"] == 2000

    assert client.delete(f"/api/elements/{saved['id']}").status_code == 204
    assert client.get(f"/api/elements/{saved['id']}").status_code == 404


def test_profiles_in_use_cannot_be_deleted(client, cat):
    client.post("/api/elements", json=element(cat))
    assert client.delete(f"/api/profiles/{cat['W70-301']}").status_code == 409


def test_seeded_sample_element_calculates(client, cat):
    [sample] = [e for e in client.get("/api/elements").json() if e["position"] == "W01"]
    r = client.get(f"/api/elements/{sample['id']}/calculation")
    assert r.status_code == 200, r.text
    assert len(r.json()["geometry"]["fields"]) == 2
