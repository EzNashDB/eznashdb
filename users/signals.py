from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from app import brevo
from app.async_utils import run_in_background
from users.models import User


@receiver(post_save, sender=User)
def sync_new_user_to_brevo(sender, instance, created, **kwargs):
    """
    Deferred to after commit so a rolled-back signup never reaches Brevo.
    Backgrounded so a slow/down Brevo can't doesn't latency to the signup request.
    """
    if not created or not instance.email:
        return

    transaction.on_commit(lambda: run_in_background(_sync_and_record, instance))


def _sync_and_record(user):
    if brevo.sync_contact(user) is None:
        return

    User.objects.filter(pk=user.pk).update(brevo_synced_at=timezone.now())
