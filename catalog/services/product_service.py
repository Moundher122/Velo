"""
catalog.services.product_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
All business logic for products and variants lives here.
No other module should query/mutate ProductVariant stock directly.
"""

from __future__ import annotations

from typing import Iterable

from django.db import transaction
from django.db.models import F, QuerySet
from rest_framework.exceptions import ValidationError

from catalog.models import Product, ProductVariant, VariantAttribute


class ProductService:

    @staticmethod
    def list_products(*, include_inactive: bool = False) -> QuerySet[Product]:
        qs = Product.objects.all()
        if not include_inactive:
            qs = qs.filter(is_active=True)
        return qs

    @staticmethod
    def get_product(product_id, *, include_inactive: bool = False) -> Product:
        qs = Product.objects.prefetch_related("variants__attributes")
        if not include_inactive:
            qs = qs.filter(is_active=True)
        try:
            return qs.get(pk=product_id)
        except Product.DoesNotExist:
            raise ValidationError({"detail": "Product not found."})


class VariantService:

    @staticmethod
    def get_variant(variant_id) -> ProductVariant:
        """Fetch a single variant with related data."""
        try:
            return (
                ProductVariant.objects
                .select_related("product")
                .prefetch_related("attributes")
                .get(pk=variant_id)
            )
        except ProductVariant.DoesNotExist:
            raise ValidationError({"detail": f"Variant {variant_id} not found."})

    @staticmethod
    def get_variants_for_product(product_id) -> QuerySet[ProductVariant]:
        return (
            ProductVariant.objects
            .filter(product_id=product_id)
            .select_related("product")
            .prefetch_related("attributes")
        )

    @staticmethod
    def validate_stock(variant: ProductVariant, requested_qty: int) -> None:
        """Raise if the variant can't fulfil the requested quantity."""
        if not variant.is_active:
            raise ValidationError(
                {"detail": f"Variant '{variant}' is no longer available."}
            )
        if requested_qty > variant.stock_quantity:
            raise ValidationError(
                {
                    "detail": (
                        f"Insufficient stock for '{variant}'. "
                        f"Requested {requested_qty}, available {variant.stock_quantity}."
                    )
                }
            )

    @staticmethod
    def lock_variants(variant_ids: Iterable) -> dict[int | str, ProductVariant]:
        """
        SELECT … FOR UPDATE on a set of variant IDs.
        Returns a dict mapping variant_id → locked variant instance.
        """
        variants_qs = (
            ProductVariant.objects
            .filter(id__in=variant_ids)
            .select_for_update()
        )
        return {v.id: v for v in variants_qs}

    @staticmethod
    def decrease_stock(variant_id, quantity: int) -> None:
        """Atomically decrease stock using F() expression."""
        updated = (
            ProductVariant.objects
            .filter(id=variant_id, stock_quantity__gte=quantity)
            .update(stock_quantity=F("stock_quantity") - quantity)
        )
        if not updated:
            raise ValidationError(
                {"detail": f"Failed to decrease stock for variant {variant_id}."}
            )

    @staticmethod
    def increase_stock(variant_id, quantity: int) -> None:
        """Atomically increase stock (e.g. on order cancellation)."""
        ProductVariant.objects.filter(id=variant_id).update(
            stock_quantity=F("stock_quantity") + quantity
        )

    @staticmethod
    @transaction.atomic
    def create_variant(*, product_id, attributes_data: list[dict] | None = None, **fields) -> ProductVariant:
        variant = ProductVariant.objects.create(product_id=product_id, **fields)
        if attributes_data:
            VariantAttribute.objects.bulk_create(
                [VariantAttribute(variant=variant, **attr) for attr in attributes_data]
            )
        return variant

    @staticmethod
    @transaction.atomic
    def update_variant(variant: ProductVariant, *, attributes_data: list[dict] | None = None, **fields) -> ProductVariant:
        for attr, value in fields.items():
            setattr(variant, attr, value)
        variant.save()

        if attributes_data is not None:
            variant.attributes.all().delete()
            VariantAttribute.objects.bulk_create(
                [VariantAttribute(variant=variant, **attr) for attr in attributes_data]
            )
        return variant
