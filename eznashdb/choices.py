LAYOUT_CHOICES = (
    (
        "Same height as men's section",
        (
            ("is_same_height_side", "Side"),
            ("is_same_height_back", "Back"),
        ),
    ),
    (
        "Elevated (higher, but not balcony)",
        (
            ("is_elevated_side", "Side"),
            ("is_elevated_back", "Back"),
        ),
    ),
    (
        "Other",
        (
            ("is_balcony", "Balcony"),
            ("is_only_men", "Only Men"),
            ("is_mixed_seating", "Mixed Seating"),
        ),
    ),
)

ZERO_TO_EIGHTEEN = [(i, i) for i in range(19)]
