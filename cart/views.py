from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import CartItemReadSerializer, CartItemWriteSerializer, CartSerializer


class CartViewSet(viewsets.GenericViewSet):
    """
    Endpoints for the authenticated user's cart.

    GET    /cart/           → view cart
    POST   /cart/items/     → add item
    PATCH  /cart/items/{id}/ → update quantity
    DELETE /cart/items/{id}/ → remove item
    DELETE /cart/clear/     → empty the cart
    """

    permission_classes = [permissions.IsAuthenticated]

    def _get_cart(self):
        cart, _ = Cart.objects.prefetch_related(
            "items__variant__product",
            "items__variant__attributes",
        ).get_or_create(user=self.request.user)
        return cart

    def list(self, request):
        """View the current user's cart."""
        cart = self._get_cart()
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=["post"], url_path="items")
    def add_item(self, request):
        """Add an item to the cart (or increment quantity if variant already exists)."""
        cart = self._get_cart()
        serializer = CartItemWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        variant = serializer.validated_data["variant"]
        quantity = serializer.validated_data.get("quantity", 1)
        note = serializer.validated_data.get("note", "")

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            variant=variant,
            defaults={"quantity": quantity, "note": note},
        )
        if not created:
            item.quantity += quantity
            # Re-validate stock
            if item.quantity > variant.stock_quantity:
                return Response(
                    {"quantity": f"Only {variant.stock_quantity} items available in stock."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            item.note = note or item.note
            item.save()

        return Response(
            CartItemReadSerializer(item).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=False, methods=["patch", "delete"], url_path=r"items/(?P<item_pk>[^/.]+)")
    def update_or_remove_item(self, request, item_pk=None):
        """Update quantity / note or remove an item."""
        cart = self._get_cart()
        try:
            item = cart.items.select_related("variant").get(pk=item_pk)
        except CartItem.DoesNotExist:
            return Response({"detail": "Item not found."}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "DELETE":
            item.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # PATCH
        serializer = CartItemWriteSerializer(item, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(CartItemReadSerializer(item).data)

    @action(detail=False, methods=["delete"], url_path="clear")
    def clear(self, request):
        """Remove all items from the cart."""
        cart = self._get_cart()
        cart.items.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
