from django import forms
from django.contrib import admin
from django.contrib.admin.sites import NotRegistered
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import StaffAccount, Store

User = get_user_model()

try:
    admin.site.unregister(Group)
except NotRegistered:
    pass


class StoreAdminForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        eligible_users = (
            User.objects
            .filter(is_superuser=False)
            .exclude(staff_account__isnull=False)
            .exclude(store__isnull=False)
            .order_by("username")
        )

        if self.instance and self.instance.pk:
            current_user = User.objects.filter(pk=self.instance.user_id)
            eligible_users = (eligible_users | current_user).distinct()

        self.fields["user"].queryset = eligible_users


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    form = StoreAdminForm
    list_display = ("name", "user", "phone", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "user__username", "user__email", "phone", "address")
    readonly_fields = ("created_at",)
    ordering = ("name",)


@admin.register(StaffAccount)
class StaffAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "access_level", "created_at")
    list_filter = ("access_level",)
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at",)
    ordering = ("user__username",)
