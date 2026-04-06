from django.contrib import admin

from .models import Product, ProductCategory, ProductTag


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order")
    search_fields = ("name",)
    ordering = ("sort_order", "name")


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "is_active")
    list_editable = ("is_active",)
    search_fields = ("code", "name")
    list_filter = ("is_active", "category", "tags")
    filter_horizontal = ("tags",)
