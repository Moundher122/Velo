"""
orders.services
~~~~~~~~~~~~~~~
Business logic for order creation, isolated from views/serializers.
"""

from decimal import Decimal

from django.db import transaction
from django.db.models import F
from rest_framework.exceptions import ValidationError

from cart.models import Cart
from catalog.models import ProductVariant

from .models import Order, OrderItem

TAX_RATE = Decimal("0.10")  # 10 %


class OrderService:
    """Encapsulates all order-creation logic inside an atomic transaction."""

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user) -> Order:
        """
        1. Fetch user's cart with items.
        2. Validate every item's stock.
        3. Create Order + OrderItems.
        4. Decrement stock with SELECT … FOR UPDATE.
        5. Clear cart.
        6. Return the order.
        """
        try:
            cart = (
                Cart.objects
                .prefetch_related("items__variant__product", "items__variant__attributes")
                .get(user=user)
            )
        except Cart.DoesNotExist:
            raise ValidationError({"detail": "Cart not found."})

        cart_items = list(cart.items.select_related("variant").all())
        if not cart_items:
            raise ValidationError({"detail": "Cart is empty."})

        # ---- Lock variants and validate stock --------------------------------
        variant_ids = [item.variant_id for item in cart_items]
        variants_qs = (
            ProductVariant.objects
            .filter(id__in=variant_ids)
            .select_for_update()  # row-level lock
        )
        variant_map = {v.id: v for v in variants_qs}

        for item in cart_items:
            variant = variant_map.get(item.variant_id)
            if variant is None:
                raise ValidationError(
                    {"detail": f"Variant {item.variant_id} no longer exists."}
                )
            if not variant.is_active:
                raise ValidationError(
                    {"detail": f"Variant '{variant}' is no longer available."}
                )
            if item.quantity > variant.stock_quantity:
                raise ValidationError(
                    {
                        "detail": (
                            f"Insufficient stock for '{variant}'. "
                            f"Requested {item.quantity}, available {variant.stock_quantity}."
                        )
                    }
                )

        # ---- Create order ----------------------------------------------------
        subtotal = sum(
            (item.variant.price * item.quantity for item in cart_items),
            Decimal("0.00"),
        )
        tax = (subtotal * TAX_RATE).quantize(Decimal("0.01"))
        total = subtotal + tax

        order = Order.objects.create(
            user=user,
            subtotal=subtotal,
            tax=tax,
            total=total,
            status=Order.Status.PENDING,
        )

        # ---- Create order items & decrement stock ----------------------------
        order_items = []
        for item in cart_items:
            order_items.append(
                OrderItem(
                    order=order,
                    variant=item.variant,
                    quantity=item.quantity,
                    price_at_purchase=item.variant.price,
                    note=item.note,
                )
            )
            # Atomic stock decrement
            ProductVariant.objects.filter(id=item.variant_id).update(
                stock_quantity=F("stock_quantity") - item.quantity
            )
        OrderItem.objects.bulk_create(order_items)

        # ---- Clear cart ------------------------------------------------------
        cart.items.all().delete()

        # Refresh to pick up items
        order = (
            Order.objects
            .prefetch_related("items__variant__product", "items__variant__attributes")
            .get(pk=order.pk)
        )
        return order
