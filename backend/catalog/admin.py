from django.contrib import admin

from .models import Product, ProductCategory, ProductTag


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    """
    Admin surface for product family/grouping.
    """

    list_display = ("name", "sort_order")
    search_fields = ("name",)
    ordering = ("sort_order", "name")


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    """
    Admin surface for cross-cutting product labels.
    """

    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin surface for current catalog truth.

    Catalog writes are currently admin-managed, so this is the primary
    operational UI for product maintenance.
    """

    list_display = (
        "code",
        "name",
        "category",
        "units_per_box",
        "is_visible",
        "is_orderable",
    )
    list_editable = ("is_visible", "is_orderable")
    search_fields = ("code", "name")
    list_filter = ("is_visible", "is_orderable", "category", "tags")
    filter_horizontal = ("tags",)
    ordering = ("category", "code")
