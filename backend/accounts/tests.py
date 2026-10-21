from django.test import TestCase
from rest_framework.test import APIClient


class AuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def register(self, username="alice", password="Str0ng-pass!23"):
        return self.client.post("/api/auth/register", {"username": username, "password": password}, format="json")

    def test_register_returns_user_and_tokens(self):
        res = self.register()
        body = res.json()
        self.assertEqual(res.status_code, 201)
        self.assertTrue(body["success"])
        self.assertEqual(body["data"]["user"]["username"], "alice")
        self.assertIn("access", body["data"]["tokens"])
        self.assertNotIn("password", body["data"]["user"])

    def test_register_rejects_weak_password(self):
        res = self.register(password="1234")
        self.assertEqual(res.status_code, 400)
        self.assertFalse(res.json()["success"])
        self.assertIn("password", res.json()["error"]["details"])

    def test_register_rejects_duplicate_username(self):
        self.register()
        self.assertEqual(self.register().status_code, 400)

    def test_login_success_and_me(self):
        self.register()
        res = self.client.post("/api/auth/login", {"username": "alice", "password": "Str0ng-pass!23"}, format="json")
        self.assertEqual(res.status_code, 200)
        access = res.json()["data"]["tokens"]["access"]

        me = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["data"]["username"], "alice")

    def test_login_wrong_password(self):
        self.register()
        res = self.client.post("/api/auth/login", {"username": "alice", "password": "nope"}, format="json")
        self.assertEqual(res.status_code, 401)
        self.assertFalse(res.json()["success"])

    def test_invalid_token_error_is_clean(self):
        res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION="Bearer garbage")
        error = res.json()["error"]
        self.assertEqual(res.status_code, 401)
        self.assertIsNone(error["details"])
        self.assertNotIn("token_class", str(error))

    def test_me_requires_auth(self):
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_refresh_token(self):
        refresh = self.register().json()["data"]["tokens"]["refresh"]
        res = self.client.post("/api/auth/refresh", {"refresh": refresh}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertIn("access", res.json()["data"])
