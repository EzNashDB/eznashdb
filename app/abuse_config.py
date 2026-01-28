"""Configuration for user-based abuse prevention system."""

# Rate limiting
RATE_LIMIT = "30/60m"  # 30 requests per 60 minutes per user

# Episode settings
EPISODE_TIMEOUT_MINUTES = 60  # Episode ends after 60 min with no violations
SENSITIVE_CAP_PER_EPISODE = 10  # Additional requests allowed after violation

# Points decay
POINTS_DECAY_HOURS = 24  # -1 point per 24 hours with no new episode

# Escalation ladder: points -> (requires_captcha, cooldown_minutes)
ESCALATION_LADDER = {
    0: (False, 0),  # No restrictions
    1: (True, 0),  # CAPTCHA only
    2: (True, 60),  # CAPTCHA + 1 hour cooldown
    3: (True, 120),  # CAPTCHA + 2 hour cooldown
    4: (True, 1440),  # CAPTCHA + 24 hour cooldown
}
PERMANENT_BAN_THRESHOLD = 5  # 5+ points = permanent ban

# Sensitive URL names that require abuse prevention checks
SENSITIVE_URL_NAMES = [
    "eznashdb:update_shul",
    "eznashdb:google_maps_proxy",
]
