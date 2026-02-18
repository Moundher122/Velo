"""
cart.services
~~~~~~~~~~~~~
All cart business logic lives here.
Views should delegate to this service instead of manipulating models directly.
"""

from __future__ import annotations

from django.db import transaction
from rest_framework.exceptions import ValidationError

from catalog.services.product_service import VariantService

from ..models import Cart, CartItem


class CartService:

    @staticmethod
    def get_or_create_cart(user) -> Cart:
        """Return the user's cart (create if missing), with items prefetched."""
        cart, _ = (
            Cart.objects
            .prefetch_related(
                "items__variant__product",
                "items__variant__attributes",
            )
            .select_for_update()
            .get_or_create(user=user)
        )
        return cart

    @staticmethod
    @transaction.atomic
    def add_item(cart: Cart, *, variant_id, quantity: int = 1, note: str = "") -> tuple[CartItem, bool]:
        """
        Add a variant to the cart.
        If the variant is already in the cart, increment quantity.
        Returns (cart_item, created).
        """
        variant = VariantService.get_variant(variant_id)
        VariantService.validate_stock(variant, quantity)

        item, created = (
            CartItem.objects
            .select_for_update()
            .get_or_create(
                cart=cart,
                variant=variant,
                defaults={"quantity": quantity, "note": note},
            )
        )

        if not created:
            item.refresh_from_db()
            new_qty = item.quantity + quantity
            VariantService.validate_stock(variant, new_qty)
            item.quantity = new_qty
            item.note = note or item.note
            item.save()

        return item, created

    @staticmethod
    @transaction.atomic
    def update_item(cart: Cart, item_pk, *, quantity: int | None = None, note: str | None = None) -> CartItem:
        """Update quantity and/or note of an existing cart item."""
        try:
            item = (
                cart.items
                .select_related("variant")
                .select_for_update()
                .get(pk=item_pk)
            )
        except CartItem.DoesNotExist:
            raise ValidationError({"detail": "Item not found."})

        if quantity is not None:
            if quantity < 1:
                raise ValidationError({"quantity": "Quantity must be at least 1."})
            VariantService.validate_stock(item.variant, quantity)
            item.quantity = quantity

        if note is not None:
            item.note = note

        item.save()
        return item

    @staticmethod
    def remove_item(cart: Cart, item_pk) -> None:
        """Remove a single item from the cart."""
        try:
            item = cart.items.get(pk=item_pk)
        except CartItem.DoesNotExist:
            raise ValidationError({"detail": "Item not found."})
        item.delete()

    @staticmethod
    def clear_cart(cart: Cart) -> None:
        """Remove all items from the cart."""
        cart.items.all().delete()
