from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy

from .rbac import is_shop_manager, resolve_shop_access_role


class ShopAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Logged-in shop manager or mechanic with a linked profile."""

    login_url = reverse_lazy('login')

    def test_func(self):
        return resolve_shop_access_role(self.request.user) is not None

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(
                self.request,
                'Your account has no shop access. Ask a manager to link your '
                'login to a mechanic profile or add you to the Manager group.',
            )
            return redirect('login')
        return super().handle_no_permission()


class ShopManagerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Shop managers (group or superuser only); mechanics cannot access."""

    login_url = reverse_lazy('login')

    def test_func(self):
        return is_shop_manager(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(
                self.request,
                'This page is restricted to managers only.',
            )
            return redirect('task_list')
        return super().handle_no_permission()
