"""User-based abuse prevention enforcement logic and helpers."""

from dataclasses import dataclass
from datetime import timedelta
from enum import Enum, auto

from constance import config
from django.utils import timezone

from app.forms import AbuseAppealForm
from app.models import AbuseState

# Sensitive URL names and their associated abuse points
URL_ABUSE_POINTS = {
    "eznashdb:create_shul": 1,
    "eznashdb:update_shul": 4,
    "eznashdb:google_maps_proxy": 4,
}


class BlockReason(Enum):
    """Reason why a request was blocked or allowed."""

    NONE = auto()  # Request allowed (replaces empty string)
    PERMANENTLY_BANNED = auto()
    COOLDOWN = auto()
    EPISODE_CAP = auto()


@dataclass
class AbuseEnforcementResult:
    """Result of abuse enforcement check."""

    allowed: bool
    requires_captcha: bool = False
    reason: BlockReason = BlockReason.NONE
    cooldown_until: timezone.datetime | None = None
    abuse_state: AbuseState | None = None


def process_abuse_state(user):
    state: AbuseState = AbuseState.get_or_create(user)
    state.refresh()
    return determine_enforcement(state)


def determine_enforcement(state: AbuseState) -> AbuseEnforcementResult:
    # 1. Permanent ban
    if state.is_permanently_banned:
        return AbuseEnforcementResult(
            allowed=False,
            reason=BlockReason.PERMANENTLY_BANNED,
            abuse_state=state,
        )

    # 2. Cooldown
    if state.is_in_cooldown():
        return AbuseEnforcementResult(
            allowed=False,
            reason=BlockReason.COOLDOWN,
            cooldown_until=state.cooldown_until,
            abuse_state=state,
        )

    # 3. Episode cap (only reached if no cooldown was created)
    if state.is_episode_active() and state.points_in_episode >= config.ABUSE_POINTS_CAP_PER_EPISODE:
        return AbuseEnforcementResult(
            allowed=False,
            reason=BlockReason.EPISODE_CAP,
            abuse_state=state,
        )

    # 4. CAPTCHA
    requires_captcha = state.captcha_verification_pending

    return AbuseEnforcementResult(
        allowed=True,
        requires_captcha=requires_captcha,
        abuse_state=state,
    )


def get_cooldown_minutes(strikes):
    ladder = config.ABUSE_COOLDOWN_LADDER
    max_strikes = len(ladder) - 1
    effective_strikes = min(strikes, max_strikes)
    return ladder[effective_strikes]


def record_abuse_violation(user, was_rate_limited: bool, points: int = 1) -> None:
    """
    Record request outcome after processing.

    If rate limited or episode active: record the sensitive request.
    """
    state = AbuseState.get_or_create(user)

    if was_rate_limited or state.is_episode_active():
        state.record_violation(points)


def get_request_points(request) -> int:
    """Points this request costs against the rate budget."""
    if not hasattr(request, "resolver_match") or not request.resolver_match:
        return 0
    view_name = request.resolver_match.view_name
    return URL_ABUSE_POINTS.get(view_name, 0)


def format_retry_time(minutes):
    """Format retry time for display. Shows hours and minutes if >= 60 minutes."""
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    parts = [f"{hours} hour{'s' if hours != 1 else ''}"]
    if remaining_minutes > 0:
        parts.append(f"{remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}")
    return " ".join(parts)


def build_block_context(result):
    """
    Build the template context describing a blocked request.
    """
    context = {"abuse_state": result.abuse_state}

    if result.reason == BlockReason.PERMANENTLY_BANNED:
        context["appeal_form"] = AbuseAppealForm(initial={"abuse_state": result.abuse_state.id})
    elif result.reason == BlockReason.COOLDOWN:
        remaining_seconds = (result.cooldown_until - timezone.now()).total_seconds()
        minutes = max(1, int(remaining_seconds / 60))
        context["retry_after"] = format_retry_time(minutes)
    elif result.reason == BlockReason.EPISODE_CAP:
        # Calculate time until episode ends
        state = result.abuse_state
        if state and state.last_violation_at:
            episode_ends = state.last_violation_at + timedelta(
                minutes=config.ABUSE_EPISODE_INACTIVITY_MINUTES
            )
            remaining_seconds = (episode_ends - timezone.now()).total_seconds()
            minutes = max(1, int(remaining_seconds / 60))
            context["retry_after"] = format_retry_time(minutes)

    return context
