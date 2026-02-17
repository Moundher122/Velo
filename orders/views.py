from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Order
from .serializers import OrderDetailSerializer, OrderListSerializer
from .services import OrderService


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    list:     GET  /orders/          → user's orders
    retrieve: GET  /orders/{id}/     → order detail
    create:   POST /orders/checkout/ → create order from cart
    """

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Order.objects.filter(user=self.request.user)
        if self.action == "retrieve":
            qs = qs.prefetch_related(
                "items__variant__product",
                "items__variant__attributes",
            )
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return OrderDetailSerializer
        return OrderListSerializer

    @action(detail=False, methods=["post"], url_path="checkout")
    def checkout(self, request):
        """Create an order from the authenticated user's cart."""
        order = OrderService.create_order_from_cart(request.user)
        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )
