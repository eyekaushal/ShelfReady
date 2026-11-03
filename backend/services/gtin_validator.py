class GtinValidator:
    """
    Checks a GTIN (the number under a barcode: EAN-13, UPC-12, GTIN-8 or GTIN-14).

    The last digit is a check digit computed with the GS1 "mod 10" rule, so a single
    mistyped digit (very common in brand spreadsheets) is caught. Plain maths, no AI.
    """

    VALID_LENGTHS = (8, 12, 13, 14)

    @classmethod
    def error_for(cls, gtin: str) -> str | None:
        """Returns a human-readable problem, or None if the GTIN is valid."""
        if not gtin.isdigit():
            return "GTIN must contain digits only."
        if len(gtin) not in cls.VALID_LENGTHS:
            return "GTIN must be 8, 12, 13 or 14 digits long."
        if int(gtin[-1]) != cls.check_digit(gtin[:-1]):
            return "GTIN check digit is wrong. Please re-check the barcode number."
        return None

    @classmethod
    def is_valid(cls, gtin: str) -> bool:
        return cls.error_for(gtin) is None

    @staticmethod
    def check_digit(digits: str) -> int:
        """
        GS1 mod-10: starting from the RIGHT, multiply digits by 3, 1, 3, 1, ...
        add them up, and the check digit is what brings the total up to a multiple of 10.

        Example (EAN-13 "400638133393" + ?): weighted sum = 89 → check digit = 1 (89 + 1 = 90).
        """
        total = 0
        for position, char in enumerate(reversed(digits)):
            weight = 3 if position % 2 == 0 else 1
            total += int(char) * weight
        return (10 - total % 10) % 10
