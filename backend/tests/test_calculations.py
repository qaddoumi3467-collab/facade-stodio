from decimal import Decimal

import pytest

from app import calculations as calc


class TestProfile:
    def test_weight_of_cut_piece(self):
        # 1.245 kg/m x 1.5 m
        assert calc.profile_weight_kg("1.245", 1500) == Decimal("1.868")

    def test_weight_of_full_bar(self):
        assert calc.profile_weight_kg("1.412", 6000) == Decimal("8.472")

    def test_weight_rounds_half_up(self):
        # 0.5 kg/m x 1 mm = 0.0005 kg -> 0.001
        assert calc.profile_weight_kg("0.5", 1) == Decimal("0.001")

    def test_price_of_cut_piece(self):
        assert calc.profile_price("9.80", 2350) == Decimal("23.03")

    def test_accepts_fractional_mm(self):
        assert calc.profile_weight_kg("2", "1250.5") == Decimal("2.501")

    @pytest.mark.parametrize("length", [0, -10])
    def test_rejects_non_positive_length(self, length):
        with pytest.raises(ValueError):
            calc.profile_weight_kg("1.2", length)
        with pytest.raises(ValueError):
            calc.profile_price("9.8", length)


class TestGlass:
    def test_area(self):
        assert calc.glass_area_m2(1200, 1500) == Decimal("1.8000")

    def test_area_rounds_to_four_places(self):
        # 333 x 333 = 110889 mm² = 0.110889 m²
        assert calc.glass_area_m2(333, 333) == Decimal("0.1109")

    def test_weight_single_pane(self):
        # 1 m² of 6 mm glass = 15 kg
        assert calc.glass_weight_kg(6, 1000, 1000) == Decimal("15.000")

    def test_weight_double_glazing_ignores_air_gap(self):
        # 6-16-6 -> 12 mm of glass; 1.2 x 1.5 m = 1.8 m² -> 54 kg
        assert calc.glass_weight_kg(12, 1200, 1500) == Decimal("54.000")

    def test_price(self):
        assert calc.glass_price(42, 1200, 1500) == Decimal("75.60")

    @pytest.mark.parametrize("w,h", [(0, 1000), (1000, 0), (-1, 5)])
    def test_rejects_bad_size(self, w, h):
        with pytest.raises(ValueError):
            calc.glass_area_m2(w, h)
        with pytest.raises(ValueError):
            calc.glass_weight_kg(6, w, h)

    @pytest.mark.parametrize(
        "build_up,expected",
        [
            ("6", "6"),
            ("6-16-6", "12"),
            ("4-12-4-12-4", "12"),
            ("8.76-16-6", "14.76"),
            (" 4 - 12 - 4 ", "8"),
        ],
    )
    def test_glass_thickness_from_build_up(self, build_up, expected):
        assert calc.glass_thickness_from_build_up(build_up) == Decimal(expected)

    @pytest.mark.parametrize("build_up", ["", "6-16", "6--6", "a-16-6", "6-0-6"])
    def test_bad_build_up(self, build_up):
        with pytest.raises(ValueError):
            calc.glass_thickness_from_build_up(build_up)
