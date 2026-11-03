import pytest

from services.gtin_validator import GtinValidator


class TestGtinValidator:
    @pytest.mark.parametrize(
        "gtin",
        [
            "96385074",  # GTIN-8
            "036000291452",  # UPC-12
            "4006381333931",  # EAN-13
            "8901063010574",  # EAN-13, Indian prefix 890
            "10012345678902",  # GTIN-14
        ],
    )
    def test_valid_gtins(self, gtin):
        assert GtinValidator.is_valid(gtin)

    def test_wrong_check_digit(self):
        assert "check digit" in GtinValidator.error_for("4006381333932")

    @pytest.mark.parametrize("gtin", ["1234567", "123456789", "12345678901", "123456789012345"])
    def test_wrong_lengths(self, gtin):
        assert "8, 12, 13 or 14" in GtinValidator.error_for(gtin)

    def test_letters_are_rejected(self):
        assert "digits only" in GtinValidator.error_for("40063813339A1")

    def test_check_digit_maths(self):
        assert GtinValidator.check_digit("400638133393") == 1
