from rest_framework import serializers

from catalog.serializers import ProductVariantListSerializer
from catalog.services.product_service import VariantService

from .models import Cart, CartItem


class CartItemReadSerializer(serializers.ModelSerializer):
    """Read-only cart item with full variant info."""

    variant = ProductVariantListSerializer(read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "variant", "quantity", "note", "line_total", "created_at")
        read_only_fields = ("id", "line_total", "created_at")


class CartItemWriteSerializer(serializers.ModelSerializer):
    """Add / update a cart item."""

    class Meta:
        model = CartItem
        fields = ("id", "variant", "quantity", "note")
        read_only_fields = ("id",)

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1.")
        return value

    def validate(self, attrs):
        variant = attrs.get("variant") or (self.instance and self.instance.variant)
        quantity = attrs.get("quantity", getattr(self.instance, "quantity", 1))

        if variant:
            # Delegate all stock/active checks to the catalog service
            VariantService.validate_stock(variant, quantity)
        return attrs


class CartSerializer(serializers.ModelSerializer):
    """Full cart with items and computed subtotal."""

    items = CartItemReadSerializer(many=True, read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "items", "subtotal", "item_count", "created_at", "updated_at")
        read_only_fields = fields
