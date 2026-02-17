from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter

from . import views

app_name = "catalog"

router = DefaultRouter()
router.register(r"products", views.ProductViewSet, basename="product")

variants_router = NestedDefaultRouter(router, r"products", lookup="product")
variants_router.register(r"variants", views.ProductVariantViewSet, basename="product-variant")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(variants_router.urls)),
]
