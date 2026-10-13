from sqlalchemy import func, select

from app.import_catalog import CATALOGUES, import_catalogue, read_rows
from app.models import Profile, ProfileRole


def test_catalogue_rows_are_valid():
    for name in CATALOGUES:
        rows = read_rows(name)
        article_nos = [r["article_no"] for r in rows]
        assert len(article_nos) == len(set(article_nos))
        for row in rows:
            ProfileRole(row["role"])
            assert row["name_en"] and row["name_ar"]
            assert float(row["width_mm"]) > 0 and float(row["height_mm"]) > 0
            if row["weight_kg_per_m"]:
                assert 0 < float(row["weight_kg_per_m"]) < 10


def test_import_saraya(session):
    result = import_catalogue(session, "alupco_saraya_100")
    rows = read_rows("alupco_saraya_100")
    assert len(result.added) + len(result.missing_weight) == len(rows) == 116
    assert "40033" in result.missing_weight

    frame = session.scalar(select(Profile).where(Profile.article_no == "40084"))
    assert frame.role == ProfileRole.frame
    assert float(frame.weight_kg_per_m) == 1.85
    assert frame.system.manufacturer == "Alupco"

    # Running it again adds nothing.
    again = import_catalogue(session, "alupco_saraya_100")
    assert again.added == []
    assert len(again.already_there) == len(result.added)
    count = session.scalar(select(func.count()).select_from(Profile))
    assert count == len(result.added)
