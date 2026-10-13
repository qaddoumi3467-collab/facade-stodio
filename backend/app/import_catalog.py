"""Load a manufacturer catalogue from ``app/catalog_data``.

Run with ``python -m app.import_catalog alupco_saraya_100``. Each catalogue
is a CSV of profiles typed in from the manufacturer's printed catalogue,
plus the system it belongs to (listed in ``CATALOGUES`` below).

Profiles that already exist (same article number) are left alone, so it is
safe to run more than once. Profiles whose weight is not printed in the
catalogue are skipped and listed, so they can be added by hand once the
weight is known.
"""

import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Profile, ProfileRole, ProfileSystem

DATA_DIR = Path(__file__).parent / "catalog_data"

CATALOGUES = {
    "alupco_saraya_100": dict(
        code="ALUPCO-SARAYA-100",
        name_en="Alupco Saraya 100 mm sliding windows",
        name_ar="ألوبكو سرايا ١٠٠ مم شبابيك سحاب",
        manufacturer="Alupco",
        description="Saraya and Super Saraya sliding windows, KSA market catalogue.",
        thermal_break=False,
    ),
}


@dataclass
class ImportResult:
    added: list[str] = field(default_factory=list)
    already_there: list[str] = field(default_factory=list)
    missing_weight: list[str] = field(default_factory=list)


def read_rows(name: str) -> list[dict[str, str]]:
    with open(DATA_DIR / f"{name}.csv", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def import_catalogue(session: Session, name: str) -> ImportResult:
    system_data = CATALOGUES[name]
    system = session.scalar(
        select(ProfileSystem).where(ProfileSystem.code == system_data["code"])
    )
    if system is None:
        system = ProfileSystem(**system_data)
        session.add(system)
        session.flush()

    existing = set(session.scalars(select(Profile.article_no)))
    result = ImportResult()
    for row in read_rows(name):
        article_no = row["article_no"]
        if article_no in existing:
            result.already_there.append(article_no)
            continue
        if not row["weight_kg_per_m"]:
            result.missing_weight.append(article_no)
            continue
        session.add(
            Profile(
                system_id=system.id,
                article_no=article_no,
                name_en=row["name_en"],
                name_ar=row["name_ar"],
                role=ProfileRole(row["role"]),
                width_mm=row["width_mm"],
                height_mm=row["height_mm"],
                weight_kg_per_m=row["weight_kg_per_m"],
            )
        )
        result.added.append(article_no)
    session.commit()
    return result


if __name__ == "__main__":
    names = sys.argv[1:] or list(CATALOGUES)
    with SessionLocal() as session:
        for name in names:
            result = import_catalogue(session, name)
            print(f"{name}: {len(result.added)} profiles added, "
                  f"{len(result.already_there)} already there.")
            if result.missing_weight:
                print("  Skipped, weight not in the catalogue: "
                      + ", ".join(result.missing_weight))
