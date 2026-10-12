import pytest

from app.seed import seed

SYSTEM = {"code": "W70", "name_en": "Casement 70", "name_ar": "مفصلي ٧٠"}


def make_system(client, **overrides):
    r = client.post("/api/systems", json={**SYSTEM, **overrides})
    assert r.status_code == 201, r.text
    return r.json()


def profile_data(system_id, **overrides):
    return {
        "system_id": system_id,
        "article_no": "W70-101",
        "name_en": "Outer frame",
        "name_ar": "حلق خارجي",
        "role": "frame",
        "width_mm": 70,
        "height_mm": 55,
        "weight_kg_per_m": 1.245,
        "price_per_m": 9.8,
        **overrides,
    }


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_system_crud_keeps_arabic(client):
    system = make_system(client)
    assert system["name_ar"] == "مفصلي ٧٠"
    assert client.get(f"/api/systems/{system['id']}").json()["name_ar"] == "مفصلي ٧٠"

    updated = client.put(
        f"/api/systems/{system['id']}", json={**SYSTEM, "thermal_break": True}
    ).json()
    assert updated["thermal_break"] is True

    assert client.delete(f"/api/systems/{system['id']}").status_code == 204
    assert client.get(f"/api/systems/{system['id']}").status_code == 404


def test_duplicate_code_is_rejected(client):
    make_system(client)
    assert client.post("/api/systems", json=SYSTEM).status_code == 409


def test_profile_crud_and_filters(client):
    a = make_system(client)
    b = make_system(client, code="S120", name_en="Sliding", name_ar="سحاب")
    client.post("/api/profiles", json=profile_data(a["id"]))
    client.post(
        "/api/profiles",
        json=profile_data(b["id"], article_no="S120-1", name_en="Rail", name_ar="سكة"),
    )

    assert len(client.get("/api/profiles").json()) == 2
    only_a = client.get("/api/profiles", params={"system_id": a["id"]}).json()
    assert [p["article_no"] for p in only_a] == ["W70-101"]
    by_arabic = client.get("/api/profiles", params={"q": "سكة"}).json()
    assert [p["article_no"] for p in by_arabic] == ["S120-1"]


def test_profile_needs_existing_system(client):
    r = client.post("/api/profiles", json=profile_data(9999))
    assert r.status_code == 422


@pytest.mark.parametrize(
    "field,value", [("width_mm", 0), ("weight_kg_per_m", -1), ("role", "window")]
)
def test_profile_validation(client, field, value):
    system = make_system(client)
    r = client.post("/api/profiles", json=profile_data(system["id"], **{field: value}))
    assert r.status_code == 422


def test_system_in_use_cannot_be_deleted(client):
    system = make_system(client)
    client.post("/api/profiles", json=profile_data(system["id"]))
    assert client.delete(f"/api/systems/{system['id']}").status_code == 409


def test_profile_piece_calculation(client):
    system = make_system(client)
    profile = client.post("/api/profiles", json=profile_data(system["id"])).json()
    r = client.get(f"/api/profiles/{profile['id']}/piece", params={"length_mm": 1500})
    assert r.json() == {"length_mm": 1500, "weight_kg": 1.868, "price": 14.7}
    bad = client.get(f"/api/profiles/{profile['id']}/piece", params={"length_mm": 0})
    assert bad.status_code == 422


def test_glass_pane_calculation(client):
    glass = client.post(
        "/api/glass",
        json={
            "code": "DG6166",
            "name_en": "Double 6-16-6",
            "name_ar": "مزدوج ٦-١٦-٦",
            "build_up": "6-16-6",
            "total_thickness_mm": 28,
            "glass_thickness_mm": 12,
            "price_per_m2": 42,
        },
    ).json()
    r = client.get(
        f"/api/glass/{glass['id']}/pane", params={"width_mm": 1200, "height_mm": 1500}
    )
    assert r.json() == {
        "width_mm": 1200,
        "height_mm": 1500,
        "area_m2": 1.8,
        "weight_kg": 54.0,
        "price": 75.6,
    }


def test_glass_thicker_than_unit_is_rejected(client):
    r = client.post(
        "/api/glass",
        json={
            "code": "X",
            "name_en": "x",
            "name_ar": "x",
            "total_thickness_mm": 6,
            "glass_thickness_mm": 12,
        },
    )
    assert r.status_code == 422


def test_hardware_crud(client):
    system = make_system(client)
    item = client.post(
        "/api/hardware",
        json={
            "system_id": system["id"],
            "article_no": "HW-H01",
            "name_en": "Handle",
            "name_ar": "مقبض",
            "category": "handle",
            "price_per_unit": 6.5,
        },
    ).json()
    assert item["unit"] == "piece"
    assert client.get("/api/hardware", params={"q": "مقبض"}).json()[0]["id"] == item["id"]


def test_seed_is_repeatable(client, session):
    seed(session)
    seed(session)
    assert len(client.get("/api/systems").json()) == 2
    assert len(client.get("/api/profiles").json()) == 6
    assert len(client.get("/api/glass").json()) == 3
    assert len(client.get("/api/hardware").json()) == 4
