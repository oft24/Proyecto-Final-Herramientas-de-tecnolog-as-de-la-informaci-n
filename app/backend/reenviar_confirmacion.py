"""Adaptación inicial del parche de Marketplace para el modelo de pedidos de Dangoko.

Esta versión conserva la omisión de autorización del parche docente para la
corrida roja de QA. No debe desplegarse públicamente ni promoverse a Producción.
"""

from __future__ import annotations

import os
import re
from urllib.parse import urlparse

import requests
from flask import Blueprint, jsonify, request

from backend import database


reenviar_bp = Blueprint("reenviar", __name__)
ORDER_CODE = re.compile(r"BDK-[0-9A-F]{10}\Z")


@reenviar_bp.post("/pedidos/<string:pedido_id>/reenviar-confirmacion")
def reenviar_confirmacion(pedido_id: str):
    """Reenvía la confirmación asociada a un pedido existente."""
    origin = request.headers.get("Origin")
    if origin and urlparse(origin).netloc.lower() != request.host.lower():
        return jsonify(error="Origen de solicitud no permitido."), 403

    pedido_id = pedido_id.upper()
    if not ORDER_CODE.fullmatch(pedido_id):
        return jsonify(error="Pedido no encontrado."), 404
    try:
        pedido = database.find_order_by_public_id(pedido_id)
    except Exception:
        return jsonify(error="La base de datos no está disponible."), 503
    if pedido is None:
        return jsonify(error="Pedido no encontrado."), 404

    # La autorización por propietario se añadirá después de la corrida roja.
    try:
        response = requests.post(
            os.getenv("NOTIFICATIONS_URL", "http://notifications:5001").rstrip("/")
            + "/notifications/order/resend",
            json={
                "order_id": pedido["public_order_id"],
                "customer_name": pedido["customer_name"],
                "email": pedido["customer_email"],
                "items": [
                    {
                        "product_id": item["product_id"],
                        "quantity": item["quantity"],
                        "unit_price": str(item["unit_price"]),
                    }
                    for item in pedido["items"]
                ],
            },
            timeout=3,
        )
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError):
        return jsonify(error="No se pudo solicitar la confirmación."), 503

    return jsonify(
        order_id=pedido_id,
        status="accepted",
        delivery=result.get("delivery", "recorded"),
    ), 202
