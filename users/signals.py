from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from app import brevo
from app.async_utils import run_in_background
from users.models import User


@receiver(post_save, sender=User)
def sync_new_user_to_brevo(sender, instance, created, **kwargs):
    """
    Deferred to after commit so a rolled-back signup never reaches Brevo.
    Backgrounded so a slow/down Brevo can't add latency to the signup request.
    """
    if not created or not instance.email:
        return

    transaction.on_commit(lambda: run_in_background(brevo.sync_contact, instance))
