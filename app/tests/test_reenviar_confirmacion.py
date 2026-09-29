"""Control de acceso de la nueva funcionalidad del parche Marketplace."""

import unittest
from unittest.mock import patch

from app import app


ORDER_CODE = "BDK-ABCDEF1234"
ORDER = {
    "id": "82f017f1-7655-4d35-98b4-9a0aee88a258",
    "public_order_id": ORDER_CODE,
    "user_id": 7,
    "customer_name": "Compradora de prueba",
    "customer_email": "compradora@example.invalid",
    "items": [{"product_id": "811140", "quantity": 1, "unit_price": "1120.00"}],
}


class ResendAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.lookup = patch(
            "backend.reenviar_confirmacion.database.find_order_by_public_id",
            return_value=ORDER.copy(),
        ).start()
        self.notify = patch("backend.reenviar_confirmacion.requests.post").start()
        self.notify.return_value.json.return_value = {"delivery": "recorded"}
        self.addCleanup(patch.stopall)

    def sign_in_as(self, user_id):
        with self.client.session_transaction() as session:
            session["user_id"] = user_id

    def test_owner_can_request_resend(self):
        self.sign_in_as(7)
        response = self.client.post(f"/pedidos/{ORDER_CODE}/reenviar-confirmacion")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.get_json()["delivery"], "recorded")
        self.notify.assert_called_once()
        self.assertEqual(self.notify.call_args.kwargs["json"]["email"], ORDER["customer_email"])

    def test_other_user_cannot_resend_order(self):
        self.sign_in_as(8)
        response = self.client.post(f"/pedidos/{ORDER_CODE}/reenviar-confirmacion")
        self.assertEqual(response.status_code, 404)
        self.notify.assert_not_called()

    def test_anonymous_user_cannot_resend_order(self):
        response = self.client.post(f"/pedidos/{ORDER_CODE}/reenviar-confirmacion")
        self.assertEqual(response.status_code, 401)
        self.notify.assert_not_called()

    def test_unknown_order_is_not_notified(self):
        self.sign_in_as(7)
        self.lookup.return_value = None
        response = self.client.post(f"/pedidos/{ORDER_CODE}/reenviar-confirmacion")
        self.assertEqual(response.status_code, 404)
        self.notify.assert_not_called()

    def test_cross_site_request_is_rejected(self):
        self.sign_in_as(7)
        response = self.client.post(
            f"/pedidos/{ORDER_CODE}/reenviar-confirmacion",
            headers={"Origin": "https://untrusted.example"},
        )
        self.assertEqual(response.status_code, 403)
        self.notify.assert_not_called()


if __name__ == "__main__":
    unittest.main()
