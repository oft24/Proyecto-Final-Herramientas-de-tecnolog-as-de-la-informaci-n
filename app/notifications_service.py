"""Independent notification service for Marketplace orders."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)
LOG_PATH = Path(os.getenv("NOTIFICATION_LOG_PATH", "/tmp/dangoko-notifications.jsonl"))


@app.get("/salud")
def health():
    return jsonify(status="ok", service="notifications")


@app.post("/notifications/order")
def notify_order():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict) or not payload.get("order_id"):
        return jsonify(error="order_id es obligatorio"), 400
    event = {
        "event": "order.confirmed",
        "order_id": str(payload["order_id"]),
        "recipient": payload.get("email") or payload.get("customer_name", "cliente"),
        "message": f"Pedido {payload['order_id']} confirmado para notificación.",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
    return jsonify(status="sent", event=event), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")))
