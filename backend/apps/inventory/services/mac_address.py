"""MAC addresses, stored in one form: six pairs of upper-case hex digits with colons."""

import re

# Separators people type between the pairs: colons, hyphens, dots (Cisco), spaces.
SEPARATORS = re.compile(r"[\s:.\-]")
HEX_12 = re.compile(r"^[0-9A-F]{12}$")


def normalize_mac_address(value: str) -> str:
    """``AA:BB:CC:DD:EE:FF`` for any way of writing the twelve digits ("aa-bb-cc-dd-ee-ff",
    "aabb.ccdd.eeff", "AABBCCDDEEFF"); anything else stays as typed, for validation to refuse.
    """
    text = value.strip()
    digits = SEPARATORS.sub("", text).upper()
    if not HEX_12.match(digits):
        return text
    return ":".join(digits[i : i + 2] for i in range(0, 12, 2))
