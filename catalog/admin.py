from django.contrib import admin

from .models import Product, ProductVariant, VariantAttribute


class VariantAttributeInline(admin.TabularInline):
    model = VariantAttribute
    extra = 1


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    show_change_link = True


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    inlines = [ProductVariantInline]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("__str__", "product", "price", "stock_quantity", "is_active")
    list_filter = ("is_active", "product")
    search_fields = ("product__name", "sku")
    inlines = [VariantAttributeInline]
