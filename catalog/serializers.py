from rest_framework import serializers

from .models import Product, ProductVariant, VariantAttribute



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
        read_only_fields = ("id",)

    def create(self, validated_data):
        attributes_data = validated_data.pop("attributes", [])
        variant = ProductVariant.objects.create(**validated_data)
        for attr_data in attributes_data:
            VariantAttribute.objects.create(variant=variant, **attr_data)
        return variant

    def update(self, instance, validated_data):
        attributes_data = validated_data.pop("attributes", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if attributes_data is not None:
            instance.attributes.all().delete()
            for attr_data in attributes_data:
                VariantAttribute.objects.create(variant=instance, **attr_data)

        return instance


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
