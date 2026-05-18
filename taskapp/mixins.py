from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy

from .rbac import is_shop_manager, resolve_shop_access_role


class ShopAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Logged-in shop manager or mechanic with a linked profile."""

    login_url = reverse_lazy('login')

    def test_func(self):
        return resolve_shop_access_role(self.request.user) is not None


class ShopManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Shop managers (group or superuser only); mechanics cannot access."""

    login_url = reverse_lazy('login')

    def test_func(self):
        return is_shop_manager(self.request.user)
