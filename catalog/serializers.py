from rest_framework import serializers

from .models import Product, ProductVariant, VariantAttribute
from .services.product_service import VariantService



class VariantAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VariantAttribute
        fields = ("id", "key", "value")
        read_only_fields = ("id",)


class ProductVariantListSerializer(serializers.ModelSerializer):
    """Lightweight variant representation for lists."""

    attributes = VariantAttributeSerializer(many=True, read_only=True)

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "sku",
            "price",
            "stock_quantity",
            "in_stock",
            "is_active",
            "attributes",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "in_stock", "created_at", "updated_at")


class ProductVariantWriteSerializer(serializers.ModelSerializer):
    """Create / update a variant with nested attributes."""

    attributes = VariantAttributeSerializer(many=True, required=False)

    class Meta:
        model = ProductVariant
        fields = (
            "id",
            "product",
            "sku",
            "price",
            "stock_quantity",
            "is_active",
            "attributes",
        )
        read_only_fields = ("id", "product")

    def create(self, validated_data):
        attributes_data = validated_data.pop("attributes", [])
        product_id = validated_data.pop("product", None)
        if product_id and hasattr(product_id, "pk"):
            product_id = product_id.pk
        return VariantService.create_variant(
            product_id=product_id,
            attributes_data=attributes_data,
            **validated_data,
        )

    def update(self, instance, validated_data):
        attributes_data = validated_data.pop("attributes", None)
        return VariantService.update_variant(
            instance,
            attributes_data=attributes_data,
            **validated_data,
        )


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight product for list views."""

    variant_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "description",
            "image",
            "is_active",
            "variant_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "variant_count", "created_at", "updated_at")


class ProductDetailSerializer(serializers.ModelSerializer):
    """Full product with nested variants and attributes."""

    variants = ProductVariantListSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "description",
            "image",
            "is_active",
            "variants",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class ProductWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ("id", "name", "description", "image", "is_active")
        read_only_fields = ("id",)
