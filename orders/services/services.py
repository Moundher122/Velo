"""
orders.services
~~~~~~~~~~~~~~~
Business logic for order creation, isolated from views/serializers.
All product/variant interactions go through catalog.services.
All cart interactions go through cart.services.
"""

from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from cart.services.services import CartService
from catalog.services.product_service import VariantService

from ..models import Order, OrderItem

TAX_RATE = Decimal("0.10") # 10% tax rate, for example


class OrderService:
    """Encapsulates all order-creation logic inside an atomic transaction."""

    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user) -> Order:
        """
        1. Fetch user's cart via CartService.
        2. Lock variants via VariantService.
        3. Validate stock via VariantService.
        4. Create Order + OrderItems.
        5. Decrement stock via VariantService.
        6. Clear cart via CartService.
        7. Return the order.
        """
        cart = CartService.get_or_create_cart(user)

        cart_items = list(cart.items.select_related("variant").all())
        if not cart_items:
            raise ValidationError({"detail": "Cart is empty."})

        variant_ids = [item.variant_id for item in cart_items]
        variant_map = VariantService.lock_variants(variant_ids)

        for item in cart_items:
            variant = variant_map.get(item.variant_id)
            if variant is None:
                raise ValidationError(
                    {"detail": f"Variant {item.variant_id} no longer exists."}
                )
            VariantService.validate_stock(variant, item.quantity)

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
            VariantService.decrease_stock(item.variant_id, item.quantity)

        OrderItem.objects.bulk_create(order_items)

        CartService.clear_cart(cart)

        order = (
            Order.objects
            .prefetch_related("items__variant__product", "items__variant__attributes")
            .get(pk=order.pk)
        )
        return order
