"""Control de acceso de la nueva funcionalidad del parche Marketplace."""

import unittest
import json
import os
import tempfile
from pathlib import Path
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
        self.account = patch(
            "backend.reenviar_confirmacion.database.find_user_by_id",
            return_value={"id": 7, "name": "Compradora", "email": ORDER["customer_email"]},
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

    def test_guest_order_cannot_be_claimed_by_signed_in_user(self):
        self.sign_in_as(7)
        self.lookup.return_value = {**ORDER, "user_id": None}
        response = self.client.post(f"/pedidos/{ORDER_CODE}/reenviar-confirmacion")
        self.assertEqual(response.status_code, 404)
        self.notify.assert_not_called()

    def test_resend_uses_account_email_not_old_order_address(self):
        self.sign_in_as(7)
        self.lookup.return_value = {**ORDER, "customer_email": "other@example.invalid"}
        response = self.client.post(f"/pedidos/{ORDER_CODE}/reenviar-confirmacion")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            self.notify.call_args.kwargs["json"]["email"],
            ORDER["customer_email"],
        )

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

    def test_notification_failure_is_not_reported_as_success(self):
        self.sign_in_as(7)
        # requests raises a RequestException for connection and HTTP failures.
        from requests import RequestException

        self.notify.side_effect = RequestException("temporarily unavailable")
        response = self.client.post(f"/pedidos/{ORDER_CODE}/reenviar-confirmacion")
        self.assertEqual(response.status_code, 503)


class NotificationServiceTests(unittest.TestCase):
    def test_health_checks_storage_without_adding_events(self):
        from notifications_service import app as notification_app

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "volume" / "events.jsonl"
            with patch("notifications_service.LOG_PATH", log_path):
                response = notification_app.test_client().get("/salud")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.get_json()["log_ready"])
                self.assertEqual(log_path.read_text(encoding="utf-8"), "")
                log_path.write_text('{"event":"existing"}\n', encoding="utf-8")
                notification_app.test_client().get("/salud")
                self.assertEqual(log_path.read_text(encoding="utf-8"), '{"event":"existing"}\n')

    def test_health_fails_when_volume_is_not_writable(self):
        from notifications_service import app as notification_app

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "events.jsonl"
            with patch("notifications_service.LOG_PATH", log_path), patch.object(
                Path, "open", side_effect=PermissionError("read-only volume")
            ):
                response = notification_app.test_client().get("/salud")
            self.assertEqual(response.status_code, 503)
            self.assertFalse(response.get_json()["log_ready"])

    def test_notification_is_not_accepted_when_log_write_fails(self):
        from notifications_service import app as notification_app

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "events.jsonl"
            with patch("notifications_service.LOG_PATH", log_path), patch.object(
                Path, "open", side_effect=PermissionError("read-only volume")
            ), patch.dict(os.environ, {"SMTP_HOST": ""}):
                for route in ("/notifications/order", "/notifications/order/resend"):
                    response = notification_app.test_client().post(
                        route, json={"order_id": ORDER_CODE, "email": ORDER["customer_email"]}
                    )
                    self.assertEqual(response.status_code, 503)
                    self.assertNotIn("delivery", response.get_json())

    def test_resend_is_logged_without_claiming_email_delivery(self):
        from notifications_service import app as notification_app

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "events.jsonl"
            with patch("notifications_service.LOG_PATH", log_path), patch.dict(os.environ, {"SMTP_HOST": ""}):
                response = notification_app.test_client().post(
                    "/notifications/order/resend",
                    json={"order_id": ORDER_CODE, "email": ORDER["customer_email"]},
                )
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.get_json()["delivery"], "recorded")
            event = json.loads(log_path.read_text(encoding="utf-8"))
            self.assertEqual(event["event"], "order.confirmation_resent")

    def test_smtp_delivery_is_reported_only_after_send(self):
        from notifications_service import app as notification_app

        with tempfile.TemporaryDirectory() as directory:
            log_path = Path(directory) / "events.jsonl"
            settings = {
                "SMTP_HOST": "smtp.example.invalid",
                "SMTP_FROM": "orders@example.invalid",
                "SMTP_STARTTLS": "false",
            }
            with (
                patch("notifications_service.LOG_PATH", log_path),
                patch("notifications_service.smtplib.SMTP") as smtp,
                patch.dict(os.environ, settings),
            ):
                response = notification_app.test_client().post(
                    "/notifications/order/resend",
                    json={"order_id": ORDER_CODE, "email": ORDER["customer_email"]},
                )
            self.assertEqual(response.status_code, 202)
            self.assertEqual(response.get_json()["delivery"], "email_sent")
            smtp.return_value.__enter__.return_value.send_message.assert_called_once()


if __name__ == "__main__":
    unittest.main()
