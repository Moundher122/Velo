import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Cart(models.Model):
    """Shopping cart linked to an authenticated user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Cart({self.user})"

    @property
    def subtotal(self) -> Decimal:
        """Calculate subtotal from all cart items."""
        return sum(
            (item.line_total for item in self.items.select_related("variant")),
            Decimal("0.00"),
        )

    @property
    def item_count(self) -> int:
        return self.items.count()


class CartItem(models.Model):
    """A single line item inside a cart."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey(
        "catalog.ProductVariant",
        on_delete=models.CASCADE,
        related_name="cart_items",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("cart", "variant")]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.variant} × {self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.variant.price * self.quantity
