from django.core.validators import MinValueValidator
from django.db import models


class Product(models.Model):
    """A product in the catalog."""

    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="products/%Y/%m/", blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    """
    A purchasable variant of a product.
    Each variant has its own price, stock, and set of attributes.
    """

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants",
    )
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["price"]

    def __str__(self):
        attrs = ", ".join(f"{a.key}={a.value}" for a in self.attributes.all())
        return f"{self.product.name} ({attrs})" if attrs else f"{self.product.name} – ${self.price}"

    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0


class VariantAttribute(models.Model):
    """
    Dynamic key-value attribute for a variant.
    """

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.CASCADE,
        related_name="attributes",
    )
    key = models.CharField(max_length=50)
    value = models.CharField(max_length=255)

    class Meta:
        ordering = ["key"]
        unique_together = [("variant", "key")]

    def __str__(self):
        return f"{self.key}: {self.value}"
