from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from catalog.models import Product, ProductVariant, VariantAttribute

User = get_user_model()



def _create_admin():
    return User.objects.create_user(
        email="admin@example.com",
        username="admin",
        password="adminpass123",
        is_staff=True,
    )


def _create_user():
    return User.objects.create_user(
        email="user@example.com",
        username="regular",
        password="userpass123",
    )


def _create_product(**overrides):
    defaults = {"name": "Test Bike", "description": "A great bike"}
    defaults.update(overrides)
    return Product.objects.create(**defaults)


def _create_variant(product, **overrides):
    defaults = {"price": Decimal("299.99"), "stock_quantity": 10}
    defaults.update(overrides)
    return ProductVariant.objects.create(product=product, **defaults)


class ProductModelTests(TestCase):
    def test_str(self):
        product = _create_product(name="Road Bike")
        self.assertEqual(str(product), "Road Bike")

    def test_ordering_by_created_at_desc(self):
        p1 = _create_product(name="First")
        p2 = _create_product(name="Second")
        products = list(Product.objects.all())
        self.assertEqual(products[0], p2)
        self.assertEqual(products[1], p1)

    def test_default_is_active(self):
        product = _create_product()
        self.assertTrue(product.is_active)


class ProductVariantModelTests(TestCase):
    def setUp(self):
        self.product = _create_product()

    def test_in_stock_property(self):
        variant = _create_variant(self.product, stock_quantity=5)
        self.assertTrue(variant.in_stock)

    def test_out_of_stock(self):
        variant = _create_variant(self.product, stock_quantity=0)
        self.assertFalse(variant.in_stock)

    def test_ordering_by_price(self):
        v_expensive = _create_variant(self.product, price=Decimal("500.00"), sku="EXP")
        v_cheap = _create_variant(self.product, price=Decimal("100.00"), sku="CHP")
        variants = list(ProductVariant.objects.filter(product=self.product))
        self.assertEqual(variants[0], v_cheap)
        self.assertEqual(variants[1], v_expensive)


class VariantAttributeModelTests(TestCase):
    def test_str(self):
        product = _create_product()
        variant = _create_variant(product)
        attr = VariantAttribute.objects.create(variant=variant, key="color", value="red")
        self.assertEqual(str(attr), "color: red")

    def test_unique_together(self):
        product = _create_product()
        variant = _create_variant(product)
        VariantAttribute.objects.create(variant=variant, key="size", value="M")
        with self.assertRaises(Exception):
            VariantAttribute.objects.create(variant=variant, key="size", value="L")


class ProductListTests(TestCase):
    URL = "/api/products/"

    def setUp(self):
        self.client = APIClient()
        self.product = _create_product()
        _create_variant(self.product)

    def test_list_products_public(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["count"], 1)

    def test_inactive_products_hidden_for_anon(self):
        _create_product(name="Hidden", is_active=False)
        resp = self.client.get(self.URL)
        self.assertEqual(resp.data["count"], 1)

    def test_inactive_products_visible_for_admin(self):
        _create_product(name="Hidden", is_active=False)
        admin = _create_admin()
        self.client.force_authenticate(user=admin)
        resp = self.client.get(self.URL)
        self.assertEqual(resp.data["count"], 2)

    def test_search_by_name(self):
        _create_product(name="Mountain Bike")
        resp = self.client.get(self.URL, {"search": "Mountain"})
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(resp.data["results"][0]["name"], "Mountain Bike")

    def test_filter_by_is_active(self):
        admin = _create_admin()
        self.client.force_authenticate(user=admin)
        _create_product(name="Inactive Bike", is_active=False)
        resp = self.client.get(self.URL, {"is_active": "false"})
        self.assertEqual(resp.data["count"], 1)


class ProductRetrieveTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.product = _create_product()
        self.variant = _create_variant(self.product, sku="V1")
        VariantAttribute.objects.create(variant=self.variant, key="color", value="blue")

    def test_retrieve_product_with_variants(self):
        resp = self.client.get(f"/api/products/{self.product.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["name"], "Test Bike")
        self.assertEqual(len(resp.data["variants"]), 1)
        self.assertEqual(resp.data["variants"][0]["sku"], "V1")
        self.assertEqual(len(resp.data["variants"][0]["attributes"]), 1)

    def test_retrieve_inactive_product_anon_404(self):
        self.product.is_active = False
        self.product.save()
        resp = self.client.get(f"/api/products/{self.product.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)



class ProductWriteTests(TestCase):
    URL = "/api/products/"

    def setUp(self):
        self.client = APIClient()
        self.admin = _create_admin()
        self.user = _create_user()

    def test_create_product_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            self.URL,
            {"name": "New Bike", "description": "Brand new", "is_active": True},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Product.objects.filter(name="New Bike").exists())

    def test_create_product_as_regular_user_forbidden(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(
            self.URL, {"name": "Hack Bike"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_product_anon_forbidden(self):
        resp = self.client.post(self.URL, {"name": "Anon Bike"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_product_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        product = _create_product()
        resp = self.client.patch(
            f"{self.URL}{product.pk}/",
            {"name": "Updated Bike"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        product.refresh_from_db()
        self.assertEqual(product.name, "Updated Bike")

    def test_delete_product_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        product = _create_product()
        resp = self.client.delete(f"{self.URL}{product.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_delete_product_as_regular_user_forbidden(self):
        self.client.force_authenticate(user=self.user)
        product = _create_product()
        resp = self.client.delete(f"{self.URL}{product.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)



class ProductVariantAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = _create_admin()
        self.product = _create_product()
        self.base_url = f"/api/products/{self.product.pk}/variants/"

    def test_list_variants(self):
        _create_variant(self.product, sku="V1")
        _create_variant(self.product, sku="V2", price=Decimal("199.99"))
        resp = self.client.get(self.base_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 2)

    def test_create_variant_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.post(
            self.base_url,
            {
                "sku": "NEW-SKU",
                "price": "149.99",
                "stock_quantity": 20,
                "is_active": True,
                "attributes": [{"key": "color", "value": "green"}],
            },
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ProductVariant.objects.filter(sku="NEW-SKU").exists())
        variant = ProductVariant.objects.get(sku="NEW-SKU")
        self.assertEqual(variant.attributes.count(), 1)
        self.assertEqual(variant.attributes.first().value, "green")

    def test_create_variant_anon_forbidden(self):
        resp = self.client.post(
            self.base_url,
            {"sku": "X", "price": "10.00", "stock_quantity": 1},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_variant_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        variant = _create_variant(self.product, sku="PATCH-ME")
        resp = self.client.patch(
            f"{self.base_url}{variant.pk}/",
            {"price": "999.99"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        variant.refresh_from_db()
        self.assertEqual(variant.price, Decimal("999.99"))

    def test_delete_variant_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        variant = _create_variant(self.product, sku="DEL-ME")
        resp = self.client.delete(f"{self.base_url}{variant.pk}/")
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ProductVariant.objects.filter(pk=variant.pk).exists())
