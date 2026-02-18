from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import CartItemReadSerializer, CartItemWriteSerializer, CartSerializer
from .services.services import CartService


class CartViewSet(viewsets.GenericViewSet):
    """
    Endpoints for the authenticated user's cart.
    All business logic is delegated to CartService.
    """

    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        """View the current user's cart."""
        cart = CartService.get_or_create_cart(request.user)
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"], url_path="items")
    def add_item(self, request):
        """Add an item to the cart (or increment quantity if variant already exists)."""
        serializer = CartItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = CartService.get_or_create_cart(request.user)
        item, created = CartService.add_item(
            cart,
            variant_id=serializer.validated_data["variant"].pk,
            quantity=serializer.validated_data.get("quantity", 1),
            note=serializer.validated_data.get("note", ""),
        )

        return Response(
            CartItemReadSerializer(item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=["patch", "delete"], url_path=r"items/(?P<item_pk>[^/.]+)")
    def update_or_remove_item(self, request, item_pk=None):
        """Update quantity / note or remove an item."""
        cart = CartService.get_or_create_cart(request.user)

        if request.method == "DELETE":
            CartService.remove_item(cart, item_pk)
            return Response(status=status.HTTP_204_NO_CONTENT)

        # PATCH
        item = CartService.update_item(
            cart,
            item_pk,
            quantity=request.data.get("quantity"),
            note=request.data.get("note"),
        )
        return Response(CartItemReadSerializer(item).data)

    @action(detail=False, methods=["delete"], url_path="clear")
    def clear(self, request):
        """Remove all items from the cart."""
        cart = CartService.get_or_create_cart(request.user)
        CartService.clear_cart(cart)
        return Response(status=status.HTTP_204_NO_CONTENT)
