"""Independent notification service for Marketplace orders."""

from __future__ import annotations

import json
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
LOG_PATH = Path(os.getenv("NOTIFICATION_LOG_PATH", "/tmp/dangoko-notifications.jsonl"))


@app.get("/salud")
def health():
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        # Open the actual file without writing an event. A live process is not
        # ready if its mounted volume (or an existing log) is not writable.
        with LOG_PATH.open("a", encoding="utf-8"):
            pass
    except OSError:
        return jsonify(status="unavailable", service="notifications", log_ready=False), 503
    return jsonify(status="ok", service="notifications", log_ready=True)


@app.post("/notifications/order")
def notify_order():
    return _record_order_event("order.confirmed")


@app.post("/notifications/order/resend")
def resend_order_confirmation():
    return _record_order_event("order.confirmation_resent")


def _record_order_event(event_name: str):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload.get("order_id"):
        return jsonify(error="order_id es obligatorio"), 400
    if event_name == "order.confirmation_resent" and not payload.get("email"):
        return jsonify(error="el pedido no tiene correo registrado"), 422
    delivery = "recorded"
    if event_name == "order.confirmation_resent" and os.getenv("SMTP_HOST", "").strip():
        try:
            _send_confirmation_email(payload)
            delivery = "email_sent"
        except (OSError, smtplib.SMTPException, ValueError):
            return jsonify(error="no se pudo enviar el correo de confirmación"), 503
    event = {
        "event": event_name,
        "order_id": str(payload["order_id"]),
        "recipient": payload.get("email") or payload.get("customer_name", "cliente"),
        "message": f"Confirmación solicitada para el pedido {payload['order_id']}.",
        "delivery": delivery,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        return jsonify(error="No se pudo registrar la notificación."), 503
    return jsonify(status=delivery, delivery=delivery, event=event), 202


def _send_confirmation_email(payload: dict) -> None:
    """Send plain-text mail only when an SMTP transport is configured."""
    recipient = str(payload["email"]).strip()
    sender = os.getenv("SMTP_FROM", "").strip()
    if not sender or not recipient or "\r" in recipient or "\n" in recipient:
        raise ValueError("correo inválido")
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = f"Confirmación de tu pedido {payload['order_id']}"
    lines = [
        f"Hola, {payload.get('customer_name', 'cliente')}.",
        f"Te reenviamos la confirmación del pedido {payload['order_id']}.",
        "",
        "Artículos:",
    ]
    for item in payload.get("items", []):
        lines.append(
            f"- {item['quantity']} × {item['product_id']} a ${item['unit_price']} por unidad"
        )
    message.set_content("\n".join(lines))
    with smtplib.SMTP(
        os.environ["SMTP_HOST"], int(os.getenv("SMTP_PORT", "587")), timeout=8
    ) as transport:
        if os.getenv("SMTP_STARTTLS", "true").lower() in {"1", "true", "yes", "on"}:
            transport.starttls(context=ssl.create_default_context())
        username = os.getenv("SMTP_USERNAME", "")
        if username:
            transport.login(username, os.getenv("SMTP_PASSWORD", ""))
        transport.send_message(message)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")))
