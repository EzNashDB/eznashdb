from django.contrib.auth.models import AbstractUser, Permission
from django.db import models
from django.utils.translation import gettext_lazy as _
from waffle.models import CACHE_EMPTY, AbstractBaseSample, AbstractBaseSwitch, AbstractUserFlag
from waffle.utils import get_cache, get_setting, keyfmt


class User(AbstractUser):
    pass


class Flag(AbstractUserFlag):
    FLAG_PERMISSIONS_CACHE_KEY = "FLAG_PERMISSIONS_CACHE_KEY"
    FLAG_PERMISSIONS_CACHE_KEY_DEFAULT = "flag:%s:permissions"

    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        help_text=_("Activate this flag for users with any of these permissions."),
    )

    def get_flush_keys(self, flush_keys=None):
        flush_keys = super().get_flush_keys(flush_keys)
        permissions_cache_key = get_setting(
            Flag.FLAG_PERMISSIONS_CACHE_KEY, Flag.FLAG_PERMISSIONS_CACHE_KEY_DEFAULT
        )
        flush_keys.append(keyfmt(permissions_cache_key, self.name))
        return flush_keys

    def is_active_for_user(self, user):
        is_active = super().is_active_for_user(user)
        if is_active:
            return is_active

        flag_permission_ids = self._get_permission_ids()
        user_permission_ids = set(user.user_permissions.all().values_list("pk", flat=True))
        if any(flag_perm_id in user_permission_ids for flag_perm_id in flag_permission_ids):
            return True

    def _get_permission_ids(self):
        cache = get_cache()
        cache_key = keyfmt(
            get_setting(Flag.FLAG_PERMISSIONS_CACHE_KEY, Flag.FLAG_PERMISSIONS_CACHE_KEY_DEFAULT),
            self.name,
        )
        cached = cache.get(cache_key)
        if cached == CACHE_EMPTY:
            return set()
        if cached:
            return cached

        permission_ids = set(self.user_permissions.all().values_list("pk", flat=True))
        if not permission_ids:
            cache.add(cache_key, CACHE_EMPTY)
            return set()

        cache.add(cache_key, permission_ids)
        return permission_ids


class Switch(AbstractBaseSwitch):
    pass


class Sample(AbstractBaseSample):
    pass
