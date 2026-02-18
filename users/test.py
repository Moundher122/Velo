from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()



def _register_payload(**overrides):
    defaults = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "strongpass123",
    }
    defaults.update(overrides)
    return defaults



class UserModelTests(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="u@example.com", username="u1", password="pass1234"
        )
        self.assertEqual(user.email, "u@example.com")
        self.assertTrue(user.check_password("pass1234"))
        self.assertFalse(user.is_staff)

    def test_str_returns_email(self):
        user = User.objects.create_user(
            email="u@example.com", username="u1", password="pass1234"
        )
        self.assertEqual(str(user), "u@example.com")

    def test_email_is_unique(self):
        User.objects.create_user(email="dup@example.com", username="a", password="pass1234")
        with self.assertRaises(Exception):
            User.objects.create_user(email="dup@example.com", username="b", password="pass1234")



class RegisterViewTests(TestCase):
    URL = "/api/auth/register/"

    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        resp = self.client.post(self.URL, _register_payload(), format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", resp.data)
        self.assertIn("access", resp.data["tokens"])
        self.assertIn("refresh", resp.data["tokens"])
        self.assertEqual(resp.data["user"]["email"], "test@example.com")
        self.assertTrue(User.objects.filter(email="test@example.com").exists())

    def test_register_duplicate_email(self):
        self.client.post(self.URL, _register_payload(), format="json")
        resp = self.client.post(self.URL, _register_payload(username="other"), format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        resp = self.client.post(
            self.URL, _register_payload(password="short"), format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_email(self):
        payload = _register_payload()
        payload.pop("email")
        resp = self.client.post(self.URL, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_username(self):
        payload = _register_payload()
        payload.pop("username")
        resp = self.client.post(self.URL, payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class LoginViewTests(TestCase):
    URL = "/api/auth/login/"

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="login@example.com", username="loginuser", password="strongpass123"
        )

    def test_login_success(self):
        resp = self.client.post(
            self.URL,
            {"email": "login@example.com", "password": "strongpass123"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("tokens", resp.data)
        self.assertIn("access", resp.data["tokens"])
        self.assertEqual(resp.data["user"]["email"], "login@example.com")

    def test_login_wrong_password(self):
        resp = self.client.post(
            self.URL,
            {"email": "login@example.com", "password": "wrongpass"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_nonexistent_user(self):
        resp = self.client.post(
            self.URL,
            {"email": "noone@example.com", "password": "irrelevant"},
            format="json",
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileViewTests(TestCase):
    URL = "/api/auth/profile/"

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="profile@example.com",
            username="profileuser",
            password="strongpass123",
            phone="123456789",
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["email"], "profile@example.com")
        self.assertEqual(resp.data["username"], "profileuser")
        self.assertEqual(resp.data["phone"], "123456789")

    def test_update_profile(self):
        resp = self.client.patch(
            self.URL, {"username": "newname", "phone": "0000"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "newname")
        self.assertEqual(self.user.phone, "0000")

    def test_profile_unauthenticated(self):
        self.client.force_authenticate(user=None)
        resp = self.client.get(self.URL)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_email_is_read_only(self):
        resp = self.client.patch(
            self.URL, {"email": "hacker@example.com"}, format="json"
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "profile@example.com")



class TokenRefreshTests(TestCase):
    REGISTER_URL = "/api/auth/register/"
    REFRESH_URL = "/api/auth/token/refresh/"

    def setUp(self):
        self.client = APIClient()

    def test_refresh_token(self):
        resp = self.client.post(self.REGISTER_URL, _register_payload(), format="json")
        refresh = resp.data["tokens"]["refresh"]
        resp = self.client.post(self.REFRESH_URL, {"refresh": refresh}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_refresh_with_invalid_token(self):
        resp = self.client.post(
            self.REFRESH_URL, {"refresh": "invalidtoken"}, format="json"
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
