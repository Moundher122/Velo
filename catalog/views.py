from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, viewsets
from utils.permissions import IsAdminOrReadOnly
from .models import Product, ProductVariant
from .serializers import (
    ProductDetailSerializer,
    ProductListSerializer,
    ProductVariantListSerializer,
    ProductVariantWriteSerializer,
    ProductWriteSerializer,
)





class ProductViewSet(viewsets.ModelViewSet):
    """
    Public:  list / retrieve products.
    Admin:   create / update / delete products.
    """

    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created_at"]
    filterset_fields = ["is_active"]

    def get_queryset(self):
        qs = Product.objects.all()
        if self.action == "list":
            qs = qs.annotate(variant_count=Count("variants"))
        elif self.action == "retrieve":
            qs = qs.prefetch_related("variants__attributes")
        # Non-admin users only see active products
        if not (self.request.user.is_authenticated and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductWriteSerializer


class ProductVariantViewSet(viewsets.ModelViewSet):
    """
    CRUD for product variants (admin-only write).
    Nested under /products/{product_pk}/variants/
    """

    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        return (
            ProductVariant.objects.filter(product_id=self.kwargs["product_pk"])
            .select_related("product")
            .prefetch_related("attributes")
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductVariantWriteSerializer
        return ProductVariantListSerializer

    def perform_create(self, serializer):
        serializer.save(product_id=self.kwargs["product_pk"])
