from django.contrib import admin
from .models import Store


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "phone", "is_active", "created_at")
    search_fields = ("name", "user__username", "phone")
    list_filter = ("is_active",)
