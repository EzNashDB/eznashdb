from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin as DjangoLoginRequiredMixin


class LoginRequiredMixin(DjangoLoginRequiredMixin):
    """
    Custom LoginRequiredMixin that adds informative messages when redirecting to login.

    Views can override `login_required_message` to customize the message shown.
    """

    login_required_message = "Please log in to continue."

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.info(request, self.login_required_message)
        return super().dispatch(request, *args, **kwargs)
