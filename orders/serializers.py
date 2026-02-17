from rest_framework import serializers

from catalog.serializers import ProductVariantListSerializer

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    variant = ProductVariantListSerializer(read_only=True)
    line_total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "variant",
            "quantity",
            "price_at_purchase",
            "note",
            "line_total",
        )
        read_only_fields = fields


class OrderListSerializer(serializers.ModelSerializer):
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "subtotal",
            "tax",
            "total",
            "status",
            "item_count",
            "created_at",
        )
        read_only_fields = fields

    def get_item_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = (
            "id",
            "subtotal",
            "tax",
            "total",
            "status",
            "items",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
