from __future__ import annotations

from decimal import Decimal
import os
from pathlib import Path
import re
from secrets import token_hex
from uuid import uuid4
from urllib.parse import urlparse

import requests
from flask import Flask, jsonify, render_template, request, send_from_directory, session
from werkzeug.security import check_password_hash, generate_password_hash

from backend import database, storage
from backend.supabase_repository import ProductRepository

ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
app = Flask(
    __name__,
    static_folder=str(FRONTEND_DIR / "static"),
    static_url_path="",
    template_folder=str(FRONTEND_DIR / "templates"),
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "local-development-key-change-me")

PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://dangokobox.com").rstrip("/")
BUSINESS_INFO = {
    "trade_name": "dangoko",
    "legal_name": os.getenv("BUSINESS_LEGAL_NAME", "").strip(),
    "address": os.getenv("BUSINESS_ADDRESS", "").strip(),
    "rfc": os.getenv("BUSINESS_RFC", "").strip(),
    "email": os.getenv("BUSINESS_EMAIL", "").strip(),
    "phone": "+52 55 2972 3373",
    "whatsapp_url": "https://wa.me/5215529723373",
}
TRUSTED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "TRUSTED_HOSTS",
        "dangokobox.com,www.dangokobox.com,localhost,127.0.0.1,.railway.app,.vercel.app",
    ).split(",")
    if host.strip()
]
IS_PRODUCTION = bool(
    os.getenv("RAILWAY_ENVIRONMENT_NAME")
    or os.getenv("VERCEL_ENV") == "production"
    or os.getenv("APP_ENV") == "production"
)
REQUIRE_SUPABASE = os.getenv(
    "REQUIRE_SUPABASE", "true" if IS_PRODUCTION else "false"
).lower() in {"1", "true", "yes", "on"}
REQUIRE_AWS = os.getenv("REQUIRE_AWS", "false").lower() in {"1", "true", "yes", "on"}
REQUIRE_RDS = os.getenv("REQUIRE_RDS", "false").lower() in {"1", "true", "yes", "on"}
NOTIFICATIONS_URL = os.getenv("NOTIFICATIONS_URL", "http://notifications:5001").rstrip("/")

app.config.update(
    MAX_CONTENT_LENGTH=16 * 1024,
    MAX_FORM_MEMORY_SIZE=16 * 1024,
    MAX_FORM_PARTS=50,
    # AWS Academy exposes this container directly over HTTP on port 5000.
    # Keep HTTPS as the secure default but allow the deployment to select its
    # actual frontend scheme through the environment.
    PREFERRED_URL_SCHEME=os.getenv("PREFERRED_URL_SCHEME", "https"),
    TRUSTED_HOSTS=TRUSTED_HOSTS,
)

MOBILE_USER_AGENT = re.compile(
    r"android.+mobile|iphone|ipod|blackberry|iemobile|windows phone|opera mini|mobile safari",
    re.IGNORECASE,
)
TABLET_USER_AGENT = re.compile(
    r"ipad|tablet|kindle|silk|playbook|android(?!.*mobile)",
    re.IGNORECASE,
)


def request_device_class() -> str:
    """Classify the first render; the browser refines this using its viewport."""
    mobile_hint = request.headers.get("Sec-CH-UA-Mobile", "").strip()
    user_agent = request.headers.get("User-Agent", "")

    if mobile_hint == "?1" or MOBILE_USER_AGENT.search(user_agent):
        return "mobile"
    if TABLET_USER_AGENT.search(user_agent):
        return "tablet"
    return "desktop"


PRODUCTS = [
    {
        "id": "811140",
        "number": "01",
        "name": "Carbonara",
        "sku": "811140",
        "tagline": "Cremosa, picante y con final de queso.",
        "description": "Salsa de pollo picante con leche, mantequilla, mozzarella y pimienta negra.",
        "weight": "130 g · paquete individual",
        "heat": 40,
        "heat_label": "Picor cremoso · 2/5",
        "shu": "2,600",
        "kcal": "550",
        "cook_time": "5 min",
        "story_title": ["Cremosa.", "Picante.", "Muy Carbonara."],
        "story": (
            "La bolsa rosa mezcla la salsa Buldak con un polvo de queso y crema. "
            "Primero llega la mozzarella y la mantequilla; después aparecen el chile, "
            "el ajo y la pimienta negra. Es una porción de 130 g con 550 kcal."
        ),
        "story_note": "Queso primero.\nPicor después.",
        "ingredients": ["Mozzarella", "Leche", "Chile", "Pimienta"],
        "ingredient_intro": "Cuatro notas que explican el sabor de Carbonara.",
        "profile": [
            {"label": "Entrada", "value": "Leche y mantequilla"},
            {"label": "Centro", "value": "Mozzarella y salsa Buldak"},
            {"label": "Final", "value": "Chile, ajo y pimienta negra"},
        ],
        "allergens": "Contiene trigo, soya y leche.",
        "directions_title": ["Cinco minutos.", "Cremosidad exacta."],
        "directions_intro": "Preparación para la bolsa Carbonara de 130 g.",
        "directions": [
            {"title": "Hierve", "text": "Lleva 600 ml de agua a ebullición."},
            {"title": "Cocina", "text": "Añade los fideos y cocina durante 5 minutos."},
            {"title": "Reserva", "text": "Escurre, dejando 8 cucharadas (aprox. 120 ml) de agua."},
            {"title": "Mezcla", "text": "Agrega la salsa y el polvo de queso; mezcla bien y sirve."},
        ],
        "prepared_image": "/assets/prepared-carbonara.jpg?v=3",
        "prepared_alt": "Buldak Carbonara preparada en un tazón junto a su paquete rosa",
        "prepared_source": "Buldak.com",
        "prepared_source_url": "https://buldak.com/us/product/buldak-ramen-carbonara/",
        "recommendations": [
            {"title": "Huevo suave", "text": "La yema refuerza la textura cremosa sin ocultar el chile."},
            {"title": "Cebollín y hongos", "text": "Aportan frescura y umami a la salsa de queso."},
            {"title": "Pepino frío", "text": "Un acompañamiento crujiente y ácido limpia el paladar."},
        ],
        "nutrition_source_url": "https://www.samyangfoods.com/eng/brand/view.do?seq=399",
        "image": "/assets/carbonara.webp?v=4",
        "colors": {
            "bg_a": "#f5d9e1",
            "bg_b": "#fff8f4",
            "glow": "#ffc1d2",
            "ink": "#2b171e",
            "accent": "#b3123f",
        },
        "keywords": "carbonara carbo cremosa crema suave queso rosa mozzarella",
    },
    {
        "id": "811120",
        "number": "02",
        "name": "Original",
        "sku": "811120",
        "tagline": "El clásico: chile directo y final tostado.",
        "description": "Salsa de pollo picante, chile rojo, sésamo y alga tostada sin una capa láctea.",
        "weight": "140 g · paquete individual",
        "heat": 82,
        "heat_label": "Muy picante · 5/5",
        "shu": "4,404",
        "kcal": "530",
        "cook_time": "5 min",
        "story_title": ["Directa.", "Tostada.", "La original."],
        "story": (
            "La bolsa negra es la receta que inició el reto Buldak. La salsa se adhiere "
            "al fideo sin caldo: primero se siente el pollo especiado y el curry; luego "
            "sube el chile, con sésamo y alga tostada al final."
        ),
        "story_note": "Sin caldo.\nPicor frontal.",
        "ingredients": ["Chile rojo", "Sésamo", "Alga tostada", "Ajo"],
        "ingredient_intro": "Los elementos que forman el perfil seco y tostado de Original.",
        "profile": [
            {"label": "Entrada", "value": "Pollo especiado y curry"},
            {"label": "Centro", "value": "Chile rojo y ajo"},
            {"label": "Final", "value": "Sésamo y alga tostada"},
        ],
        "allergens": "Contiene trigo, soya y sésamo.",
        "directions_title": ["Cinco minutos.", "Treinta segundos al fuego."],
        "directions_intro": "Preparación para la bolsa Original de 140 g.",
        "directions": [
            {"title": "Hierve", "text": "Lleva 600 ml de agua a ebullición."},
            {"title": "Cocina", "text": "Añade los fideos y cocina durante 5 minutos."},
            {"title": "Reserva", "text": "Escurre, dejando 1/2 taza (aprox. 120 ml) de agua."},
            {"title": "Saltea", "text": "Añade la salsa, saltea 30 segundos y termina con las hojuelas."},
        ],
        "prepared_image": "/assets/prepared-original.webp?v=3",
        "prepared_alt": "Buldak Original preparada en sartén junto a su paquete negro",
        "prepared_source": "Buldak.com",
        "prepared_source_url": "https://buldak.com/us/product/buldak-ramen-original/",
        "recommendations": [
            {"title": "Huevo frito", "text": "La yema redondea el picor y añade cuerpo al fideo."},
            {"title": "Alga y cebollín", "text": "Refuerzan el acabado tostado y aportan frescura."},
            {"title": "Bebida láctea fría", "text": "La grasa láctea ayuda a bajar la sensación de capsaicina."},
        ],
        "nutrition_source_url": "https://www.samyangfoods.com/eng/brand/view.do?seq=245",
        "image": "/assets/original.webp?v=4",
        "colors": {
            "bg_a": "#120e0d",
            "bg_b": "#2a110b",
            "glow": "#ff642f",
            "ink": "#f8f2ef",
            "accent": "#ff5a20",
        },
        "keywords": "original picante fuego clásico negra chile sésamo alga",
    },
    {
        "id": "811150",
        "number": "03",
        "name": "Quattro Cheese",
        "sku": "811150",
        "tagline": "Cuatro quesos, salsa espesa y picor tardío.",
        "description": "Mozzarella, cheddar, gouda y camembert sobre la salsa Buldak picante.",
        "weight": "145 g · paquete individual",
        "heat": 60,
        "heat_label": "Picante con queso · 3/5",
        "shu": "≈2,323",
        "kcal": "590",
        "cook_time": "5 min 30 s",
        "story_title": ["Cuatro quesos.", "Una salsa.", "Picor tardío."],
        "story": (
            "Mozzarella, cheddar, gouda y camembert forman una salsa densa y salada. "
            "La primera impresión es láctea; el chile aparece después y se queda en el "
            "paladar. La bolsa del catálogo contiene 145 g."
        ),
        "story_note": "Cuatro quesos.\nUn final picante.",
        "ingredients": ["Mozzarella", "Cheddar", "Gouda", "Camembert"],
        "ingredient_intro": "Los cuatro quesos declarados para Quattro Cheese.",
        "profile": [
            {"label": "Entrada", "value": "Mozzarella cremosa"},
            {"label": "Centro", "value": "Cheddar y gouda salados"},
            {"label": "Final", "value": "Camembert, ajo y chile"},
        ],
        "allergens": "Contiene trigo, soya y leche.",
        "directions_title": ["Cinco y medio.", "Todo el queso."],
        "directions_intro": "Preparación para la bolsa Quattro Cheese de 145 g.",
        "directions": [
            {"title": "Hierve", "text": "Lleva 600 ml de agua a ebullición."},
            {"title": "Cocina", "text": "Añade los fideos y cocina 5 minutos con 30 segundos."},
            {"title": "Reserva", "text": "Escurre, dejando 6 cucharadas (aprox. 90 ml) de agua."},
            {"title": "Mezcla", "text": "Añade la salsa y el polvo de cuatro quesos; mezcla y sirve."},
        ],
        "prepared_image": "/assets/prepared-quattro.jpg?v=3",
        "prepared_alt": "Buldak Quattro Cheese preparada con queso fundido en un tazón amarillo",
        "prepared_source": "Buldak.com",
        "prepared_source_url": "https://buldak.com/us/product/buldak-ramen-quattro-cheese/",
        "recommendations": [
            {"title": "Maíz dorado", "text": "Su dulzor equilibra el chile y combina con los cuatro quesos."},
            {"title": "Pollo a la plancha", "text": "Añade proteína sin competir con la salsa cremosa."},
            {"title": "Pepinillos crujientes", "text": "La acidez corta la grasa y refresca entre bocados."},
        ],
        "nutrition_source_url": "https://samyangamerica.com/buldak/quattro-cheese",
        "image": "/assets/quattro.webp?v=4",
        "colors": {
            "bg_a": "#f3c45d",
            "bg_b": "#fff2d6",
            "glow": "#ffde8f",
            "ink": "#392608",
            "accent": "#b64b0c",
        },
        "keywords": "quattro cuatro quesos mozzarella cheddar gouda camembert amarilla",
    },
]

CATALOG_CATEGORIES = [
    {"id": "all", "label": "Todos"},
    {"id": "soups", "label": "Sopas y fideos"},
    {"id": "bowls", "label": "Bowls y vasos"},
    {"id": "tteokbokki", "label": "Tteokbokki"},
    {"id": "sauces", "label": "Salsas"},
    {"id": "chips", "label": "Papas y botanas"},
    {"id": "cookies", "label": "Galletas"},
    {"id": "candy", "label": "Dulces y gomitas"},
    {"id": "bakery", "label": "Pan y pastel"},
]


CATALOG_PRODUCTS = [
    {
        "sku": "811140", "name": "Carbonara", "category": "bags", "category_label": "Bolsa",
        "weight": "130 g", "case": "40 paquetes", "image": "/assets/carbonara.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-carbonara/", "status": "Disponible",
    },
    {
        "sku": "811130", "name": "Cream Carbonara", "category": "bags", "category_label": "Bolsa",
        "weight": "140 g", "case": "40 paquetes", "image": "/assets/catalog/cream-carbonara.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-cream-carbonara/", "status": "Disponible",
    },
    {
        "sku": "811200", "name": "Cheese", "category": "bags", "category_label": "Bolsa",
        "weight": "140 g", "case": "40 paquetes", "image": "/assets/catalog/cheese.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-cheese/", "status": "Disponible",
    },
    {
        "sku": "811150", "name": "Quattro Cheese", "category": "bags", "category_label": "Bolsa",
        "weight": "145 g", "case": "40 paquetes", "image": "/assets/quattro.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-quattro-cheese/", "status": "Disponible",
    },
    {
        "sku": "811270", "name": "Rosé", "category": "bags", "category_label": "Bolsa",
        "weight": "140 g", "case": "40 paquetes", "image": "/assets/catalog/rose.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-rose/", "status": "Disponible",
    },
    {
        "sku": "811320", "name": "Sweet & Spicy", "category": "bags", "category_label": "Bolsa",
        "weight": "140 g", "case": "40 paquetes", "image": "/assets/catalog/sweet-spicy.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-swicy/", "status": "Disponible",
    },
    {
        "sku": "811000", "name": "Taco", "category": "bags", "category_label": "Bolsa",
        "weight": "140 g", "case": "40 paquetes", "image": "/assets/catalog/taco.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-taco/", "status": "Disponible",
    },
    {
        "sku": "811340", "name": "Yakisoba", "category": "bags", "category_label": "Bolsa",
        "weight": "150 g", "case": "40 paquetes", "image": "/assets/catalog/yakisoba.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-yakisoba/", "status": "Disponible",
    },
    {
        "sku": "811220", "name": "Habanero Lime", "category": "bags", "category_label": "Bolsa",
        "weight": "135 g", "case": "40 paquetes", "image": "/assets/catalog/habanero-lime.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-habanero-lime/", "status": "Disponible",
    },
    {
        "sku": "811120", "name": "Original", "category": "bags", "category_label": "Bolsa",
        "weight": "140 g", "case": "40 paquetes", "image": "/assets/original.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-original/", "status": "Disponible",
    },
    {
        "sku": "811210", "name": "2X Spicy", "category": "bags", "category_label": "Bolsa",
        "weight": "140 g", "case": "40 paquetes", "image": "/assets/catalog/2x-spicy.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-2x/", "status": "Disponible",
    },
    {
        "sku": "811616", "name": "Sweet & Spicy Korean Chicken", "category": "bowls", "category_label": "Big Bowl",
        "weight": "115 g", "case": "6 bowls", "image": "/assets/catalog/sweet-spicy-bowl.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-swicy-big-bowl/", "status": "Disponible",
    },
    {
        "sku": "811618", "name": "Quattro Cheese Big Bowl", "category": "bowls", "category_label": "Big Bowl",
        "weight": "110 g", "case": "6 bowls", "image": "/assets/catalog/quattro-bowl.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-quattro-cheese-big-bowl/", "status": "Disponible",
    },
    {
        "sku": "811622", "name": "Carbonara Big Bowl", "category": "bowls", "category_label": "Big Bowl",
        "weight": "105 g", "case": "6 bowls", "image": "/assets/catalog/carbonara-bowl.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-carbonara-big-bowl/", "status": "Disponible",
    },
    {
        "sku": "811624", "name": "Original Big Bowl", "category": "bowls", "category_label": "Big Bowl",
        "weight": "105 g", "case": "6 bowls", "image": "/assets/catalog/original-bowl.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-original-big-bowl/", "status": "Disponible",
    },
    {
        "sku": "811640", "name": "Rosé Big Bowl", "category": "bowls", "category_label": "Big Bowl",
        "weight": "105 g", "case": "6 bowls", "image": "/assets/catalog/rose-bowl.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-rose-big-bowl/", "status": "Disponible",
    },
    {
        "sku": "811650", "name": "Rosé Wide Glass Noodle", "category": "bowls", "category_label": "Wide Glass Noodle",
        "weight": "169.4 g", "case": "16 bowls", "image": "/assets/catalog/wide-glass-noodle.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-wide-glass-noodle-rose-169-4g/", "status": "Disponible",
    },
    {
        "sku": "811612", "name": "Original Big Bowl", "category": "bowls", "category_label": "Big Bowl · SKU alterno",
        "weight": "105 g", "case": "6 bowls", "image": "/assets/catalog/original-bowl.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-ramen-original-big-bowl/", "status": "Disponible",
    },
    {
        "sku": "811710", "name": "Carbonara Tteokbokki", "category": "tteokbokki", "category_label": "Tteokbokki",
        "weight": "179 g", "case": "16 bowls", "image": "/assets/catalog/carbonara-tteokbokki.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-carbonara-tteokbokki-179g/", "status": "Disponible",
    },
    {
        "sku": "811720", "name": "Original Tteokbokki", "category": "tteokbokki", "category_label": "Tteokbokki",
        "weight": "179 g", "case": "16 bowls", "image": "/assets/catalog/original-tteokbokki.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-tteokbokki-185g/", "status": "Agotado · 14 jul 2026",
    },
    {
        "sku": "811910", "name": "Potato Chips Habanero Lime", "category": "snacks", "category_label": "Snack",
        "weight": "120 g", "case": "12 bolsas", "image": "/assets/catalog/chips-habanero.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-potato-chips-habanero-lime-120g/", "status": "Disponible",
    },
    {
        "sku": "811920", "name": "Potato Chips Original", "category": "snacks", "category_label": "Snack",
        "weight": "120 g", "case": "12 bolsas", "image": "/assets/catalog/chips-original.webp?v=4",
        "source_url": "https://buldak.com/us/product/buldak-potato-chips-original-120g/", "status": "Disponible",
    },
]


def _catalog_item(
    sku, name_es, name_en, name_zh, category, category_label, brand,
    description_es, description_en, description_zh, unit_size, source_url,
):
    """Create one local catalog row with copy for every supported language."""
    return {
        "sku": sku,
        "name": name_es,
        "name_es": name_es,
        "name_en": name_en,
        "name_zh": name_zh,
        "category": category,
        "category_label": category_label,
        "brand": brand,
        "description": description_es,
        "description_es": description_es,
        "description_en": description_en,
        "description_zh": description_zh,
        "weight": unit_size,
        "image": f"/assets/products/{sku}.webp?v=2",
        "source_url": source_url,
        "status": "Disponible",
    }


# Products from CATALAGO ACTUALIZADO MX26 that were not present in the first
# Buldak-only build. The storefront groups them by department instead of by PDF.
CATALOG_PRODUCTS.extend([
    _catalog_item(
        "811430", "Buldak Original · vaso", "Buldak Ramen Original Cup",
        "原味火鸡面（杯装）", "bowls", "Vaso", "Buldak",
        "El sabor Original en vaso individual: salsa espesa, sésamo, alga y picor directo.",
        "Original Buldak in a single cup, with thick sauce, sesame, seaweed and direct heat.",
        "经典原味杯装火鸡面，浓郁辣酱搭配芝麻与海苔，辣味直接。", "70 g",
        "https://buldak.com/us/product/buldak-ramen-original-cup/",
    ),
    _catalog_item(
        "811300", "Salsa Buldak Carbonara", "Buldak Hot Sauce Carbonara",
        "奶油味火鸡辣酱", "sauces", "Salsa", "Buldak",
        "Salsa cremosa y picante estilo Carbonara para pasta, pollo, papas o botanas.",
        "Creamy, spicy Carbonara-style sauce for pasta, chicken, fries or snacks.",
        "奶油味火鸡辣酱，适合意面、鸡肉、薯条和零食蘸食。", "200 g",
        "https://buldak.com/us/product/buldak-hot-sauce-carbonara-200g/",
    ),
    _catalog_item(
        "811280", "Salsa Buldak Original", "Buldak Hot Sauce Original",
        "原味火鸡辣酱", "sauces", "Salsa", "Buldak",
        "La salsa clásica Buldak en botella: picante, sabrosa y lista para cocinar o acompañar.",
        "Classic Buldak sauce in a bottle: hot, savory and ready for cooking or dipping.",
        "瓶装经典原味火鸡辣酱，香辣浓郁，可用于烹饪或蘸食。", "200 g",
        "https://buldak.com/us/product/buldak-hot-sauce-original-200g/",
    ),
    _catalog_item(
        "811290", "Sobres de salsa Buldak Original", "Buldak Hot Sauce Original Sticks",
        "原味火鸡辣酱便携条", "sauces", "Sobres", "Buldak",
        "Porciones individuales de salsa Original para llevar y dosificar con facilidad.",
        "Single-serve Original sauce sticks that are easy to carry and portion.",
        "原味火鸡辣酱便携条装，方便携带并精准控制用量。", "6 g",
        "https://buldak.com/us/product/buldak-hot-sauce-original-6g/",
    ),
    _catalog_item(
        "811311", "MEP ajo y almeja", "MEP Garlic & Clam Ramen",
        "MEP 蒜香蛤蜊拉面", "soups", "Sopa", "MEP",
        "Caldo marino limpio con almeja, alga y un golpe aromático de ajo.",
        "A clean seafood broth with clam, seaweed and an aromatic garlic kick.",
        "清爽海鲜汤底，融合蛤蜊、海苔与浓郁蒜香。", "120 g",
        "https://samyangamerica.com/mep/Garlic-clam",
    ),
    _catalog_item(
        "811312", "MEP res y pimienta negra", "MEP Black Pepper & Beef Ramen",
        "MEP 黑胡椒牛肉拉面", "soups", "Sopa", "MEP",
        "Caldo de res con mucho umami, pimienta negra fragante y picor en capas.",
        "Umami-rich beef broth with fragrant black pepper and layered heat.",
        "浓郁牛肉汤底，黑胡椒香气突出，辣味层次丰富。", "120 g",
        "https://samyangamerica.com/mep/Black-Pepper-Beef",
    ),
    _catalog_item(
        "811310", "MEP pollo, chile rojo y cilantro", "MEP Red Pepper, Chicken & Cilantro Ramen",
        "MEP 红椒香菜鸡肉拉面", "soups", "Sopa", "MEP",
        "Caldo ligero de pollo con chile rojo, cilantro y un final brillante de lima.",
        "Light chicken broth with red pepper, cilantro and a bright lime finish.",
        "清爽鸡汤搭配红椒、香菜与青柠尾韵。", "120 g",
        "https://samyangamerica.com/mep/red-pepper",
    ),
    _catalog_item(
        "811810", "Tangle tomate intenso", "Tangle Chunky Tomato Pasta",
        "Tangle 浓郁番茄意面", "soups", "Pasta", "Tangle",
        "Pasta instantánea con salsa de tomate espesa, ajo, cebolla y trozos de tomate.",
        "Instant pasta with chunky tomato sauce, garlic, onion and tomato pieces.",
        "即食意面搭配浓郁番茄酱、大蒜、洋葱与番茄颗粒。", "105 g",
        "https://longdan.co.uk/products/samyang-tangle-chunky-tomato-pasta-105g",
    ),
    _catalog_item(
        "811815", "Tangle bulgogi Alfredo", "Tangle Bulgogi Alfredo Big Bowl",
        "Tangle 韩式烤肉白酱意面（大碗）", "bowls", "Bowl", "Tangle",
        "Fideos anchos con salsa Alfredo cremosa y notas dulces y saladas de bulgogi.",
        "Wide noodles with creamy Alfredo sauce and sweet-savory bulgogi notes.",
        "宽面搭配奶油白酱与韩式烤肉的甜咸风味。", "105 g",
        "https://en.tangle-pasta.com/products/",
    ),
    _catalog_item(
        "811816", "Tangle crema de hongos", "Tangle Creamy Mushroom Big Bowl",
        "Tangle 奶油蘑菇意面（大碗）", "bowls", "Bowl", "Tangle",
        "Pasta cremosa con hongos, pimienta y una textura elástica de fideo ancho.",
        "Creamy mushroom pasta with pepper and bouncy wide noodles.",
        "奶油蘑菇酱搭配胡椒与弹韧宽面。", "105 g",
        "https://en.tangle-pasta.com/products/",
    ),
    _catalog_item(
        "811814", "Tangle ajo y aceite", "Tangle Garlic Oil Big Bowl",
        "Tangle 蒜香油意面（大碗）", "bowls", "Bowl", "Tangle",
        "Pasta de ajo y aceite con perejil, chile suave y fideo ancho de alta proteína.",
        "Garlic-oil pasta with parsley, gentle chili and high-protein wide noodles.",
        "蒜香油意面搭配欧芹、柔和辣椒与高蛋白宽面。", "100 g",
        "https://en.tangle-pasta.com/products/",
    ),
    _catalog_item(
        "634210", "Master Kong costilla y cebollín", "Master Kong Scallion Braised Ribs Noodle",
        "康师傅葱香排骨面", "soups", "Sopa", "Master Kong",
        "Sopa suave de costilla de cerdo con cebollín y chalota aromática.",
        "Mild pork-rib soup with scallion and aromatic shallot.",
        "温和排骨汤底，融合葱香与红葱头香气。", "104 g",
        "https://www.lunarmart.co.za/products/scallion-braised-rib-noodle",
    ),
    _catalog_item(
        "634220", "Master Kong res estofada", "Master Kong Braised Beef Noodle",
        "康师傅红烧牛肉面", "soups", "Sopa", "Master Kong",
        "El clásico caldo rojo de res estofada, profundo, especiado y reconfortante.",
        "The classic braised-beef red broth: deep, spiced and comforting.",
        "经典红烧牛肉汤底，浓郁、香料丰富且温暖满足。", "106 g",
        "https://tonymarket.shop/products/ksf-braised-beef-flavour-noodles-104g",
    ),
    _catalog_item(
        "634240", "Master Kong camarón y pastel de pescado", "Master Kong Shrimp & Fish Cake Noodle",
        "康师傅鲜虾鱼板面", "soups", "Sopa", "Master Kong",
        "Caldo marino ligero con camarón, alga y rebanadas de pastel de pescado.",
        "Light seafood broth with shrimp, seaweed and fish-cake slices.",
        "清爽海鲜汤底，搭配鲜虾、海带与鱼板。", "98 g",
        "https://www.nicedayshop.eu/product/%E5%BA%B7%E5%B8%88%E5%82%85%E9%B2%9C%E8%99%BE%E9%B1%BC%E6%9D%BF%E9%9D%A2-98g/",
    ),
    _catalog_item(
        "634250", "Master Kong res con mostaza encurtida", "Master Kong Pickled Mustard Beef Noodle",
        "康师傅老坛酸菜牛肉面", "soups", "Sopa", "Master Kong",
        "Caldo de res ácido y sabroso con mostaza encurtida al estilo tradicional.",
        "Tangy, savory beef broth with traditionally pickled mustard greens.",
        "酸爽牛肉汤底，搭配传统老坛酸菜。", "117 g",
        "https://www.lunarmart.co.za/products/beef-sour-pickle-noodles",
    ),
    _catalog_item(
        "634260", "Master Kong pollo y hongo shiitake", "Master Kong Mushroom Chicken Noodle",
        "康师傅香菇炖鸡面", "soups", "Sopa", "Master Kong",
        "Caldo suave de pollo guisado con el umami terroso del hongo shiitake.",
        "Gentle stewed-chicken broth with earthy shiitake umami.",
        "温润炖鸡汤底，融合香菇的醇厚鲜味。", "100 g",
        "https://www.ramencrate.co.nz/products/master-kang-mushroom-chicken-ramen-box",
    ),
    _catalog_item(
        "634270", "Master Kong res picante", "Master Kong Spicy Beef Noodle",
        "康师傅香辣牛肉面", "soups", "Sopa", "Master Kong",
        "Caldo rojo de res con chile, cilantro y un picor cálido y persistente.",
        "Red beef broth with chili, cilantro and warm, lingering heat.",
        "红汤牛肉面搭配辣椒与香菜，辣味温暖持久。", "104 g",
        "https://www.norexmarket.no/products/%E5%BA%B7%E5%B8%88%E5%82%85-%E9%A6%99%E8%BE%A3%E7%89%9B%E8%82%89%E9%9D%A2-inst-noodles-spicy-beef-104g",
    ),
    _catalog_item(
        "634280", "Master Kong res con pimienta verde", "Master Kong Green Peppercorn Beef Noodle",
        "康师傅藤椒牛肉面", "soups", "Sopa", "Master Kong",
        "Caldo de res con pimienta verde de Sichuan: cítrico, aromático y ligeramente adormecedor.",
        "Beef broth with green Sichuan peppercorn: citrusy, aromatic and gently numbing.",
        "牛肉汤搭配藤椒，清香柑橘感并带来轻柔麻感。", "102 g",
        "https://barakibodegon.net/products/maestro-kong-ramen-fideos-con-carne",
    ),
    _catalog_item(
        "634252", "Master Kong res con pimienta verde · bowl", "Master Kong Green Peppercorn Beef Bowl",
        "康师傅藤椒牛肉面（碗装）", "bowls", "Bowl", "Master Kong",
        "La sopa de res y pimienta verde de Sichuan en un bowl práctico de 108 g.",
        "Green Sichuan peppercorn beef soup in a convenient 108 g bowl.",
        "藤椒牛肉面碗装，108 克方便冲泡。", "108 g",
        "https://www.suning.com/item/0071470014/11027098006.html",
    ),
    _catalog_item(
        "802150", "Lay's pepino", "Lay's Cucumber Flavor Potato Chips",
        "乐事黄瓜味薯片", "chips", "Papas", "Lay's",
        "Papas delgadas con sabor fresco de pepino, sal ligera y final limpio.",
        "Thin chips with fresh cucumber flavor, light salt and a clean finish.",
        "薄脆薯片带有清新黄瓜风味、轻盐感与清爽尾韵。", "90 g",
        "https://mc.alpremium.ca/products/alp-m000692474392794",
    ),
    _catalog_item(
        "802440", "Lay's Max calamar a la parrilla", "Lay's Max Grilled Squid Flavor",
        "乐事铁板鱿鱼味大波浪薯片", "chips", "Papas", "Lay's",
        "Papas onduladas con sabor ahumado, salado y umami de calamar a la parrilla.",
        "Wavy chips with smoky, savory grilled-squid umami.",
        "大波浪薯片呈现铁板鱿鱼的烟熏咸鲜风味。", "70 g",
        "https://lilisglass.com/products/lay-s-grilled-squid-flavor",
    ),
    _catalog_item(
        "802120", "Lay's hot pot picante", "Lay's Numb & Spicy Hot Pot Flavor",
        "乐事飘香麻辣锅味薯片", "chips", "Papas", "Lay's",
        "Papas con chile, especias de hot pot y un toque ligeramente adormecedor.",
        "Chips with chili, hot-pot spices and a gently numbing finish.",
        "薯片融合辣椒与麻辣火锅香料，并带有轻微麻感。", "70 g",
        "https://candyfunhouse.ca/products/lays-numb-spicy-hot-pot-chips-china-80g",
    ),
    _catalog_item(
        "802110", "Lay's estofado italiano", "Lay's Italian Red Meat Flavor",
        "乐事意大利香浓红烩味薯片", "chips", "Papas", "Lay's",
        "Papas con tomate, hierbas y el perfil sabroso de un estofado de carne.",
        "Chips with tomato, herbs and the savory profile of a red meat stew.",
        "薯片融合番茄、香草与浓郁红烩肉风味。", "70 g",
        "https://lilisglass.com/products/lay-s-italian-red-meat-favor-70g",
    ),
    _catalog_item(
        "802410", "Lay's Max picante", "Lay's Max Pure Spicy Flavor",
        "乐事辛辣味大波浪薯片", "chips", "Papas", "Lay's",
        "Corte ondulado grueso con chile directo y textura extra crujiente.",
        "Thick wavy-cut chips with direct chili heat and extra crunch.",
        "厚切大波浪薯片，辣椒风味直接，口感格外酥脆。", "70 g",
        "https://www.joybuy.co.uk/dp/Lays-Big-Wave-Potato-Chips-Spicy/10005951",
    ),
    _catalog_item(
        "802420", "Lay's Max alita de pollo asada", "Lay's Max Roasted Chicken Wing Flavor",
        "乐事香脆烤鸡翅味大波浪薯片", "chips", "Papas", "Lay's",
        "Papas onduladas con notas de pollo asado, ajo, dulzor suave y humo.",
        "Wavy chips with roasted chicken, garlic, gentle sweetness and smoke.",
        "大波浪薯片融合烤鸡翅、蒜香、微甜与烟熏风味。", "70 g",
        "https://theexoticclub.com/products/lays-roasted-chicken-wing-flavor-asia",
    ),
    _catalog_item(
        "802160", "Lay's cangrejo dorado", "Lay's Golden Fried Crab Flavor",
        "乐事金黄炒蟹味薯片", "chips", "Papas", "Lay's",
        "Papas crujientes con cangrejo salado, un punto dulce y acabado marino.",
        "Crisp chips with savory crab, gentle sweetness and a seafood finish.",
        "酥脆薯片呈现咸鲜蟹味、微甜感与海鲜尾韵。", "70 g",
        "https://popshoplife.com/products/lays-fried-crab-flavor-china",
    ),
    _catalog_item(
        "854170", "Want Want rollos sabor verduras", "Want Want Lonely God Vegetable Potato Rolls",
        "旺旺浪味仙田园蔬菜味", "chips", "Botana", "Want Want",
        "Rollos ligeros de papa con cebollín, ajo y un condimento suave de verduras.",
        "Light potato rolls with scallion, garlic and mild vegetable seasoning.",
        "轻盈花式薯卷，融合葱香、蒜香与柔和田园蔬菜味。", "70 g",
        "https://want-want.co/products/potato-twist-veggie",
    ),
    _catalog_item(
        "854180", "Want Want rollos sabor alga", "Want Want Lonely God Seaweed Potato Rolls",
        "旺旺浪味仙海苔味", "chips", "Botana", "Want Want",
        "Rollos crujientes de papa con alga tostada y un final salado lleno de umami.",
        "Crisp potato rolls with roasted seaweed and a savory umami finish.",
        "酥脆花式薯卷搭配烤海苔，咸鲜味十足。", "70 g",
        "https://want-want.co/collections/types?q=snacks",
    ),
])


def _snack_item(sku, name_es, name_en, name_zh, category, label, brand,
                profile_es, profile_en, profile_zh, unit_size, source_url):
    """Create a multilingual snack or bakery row from the MX26 catalog."""
    return _catalog_item(
        sku, name_es, name_en, name_zh, category, label, brand,
        f"{name_es}: {profile_es}",
        f"{name_en}: {profile_en}",
        f"{name_zh}：{profile_zh}",
        unit_size, source_url,
    )


# Remaining consumer products from CATALAGO ACTUALIZADO MX26. Tableware and
# disposable food-service supplies from Catalogo 0908 are intentionally kept
# outside the shop because they are not retail food or beverage merchandise.
CATALOG_PRODUCTS.extend([
    _catalog_item(
        "811611", "Buldak Original · tazón grande", "Buldak Original Big Bowl",
        "原味火鸡面（大碗）", "bowls", "Bowl", "Buldak",
        "Tazón grande de fideos Buldak Original con salsa picante, sésamo y alga.",
        "Large Buldak Original noodle bowl with spicy sauce, sesame and seaweed.",
        "原味火鸡面大碗装，搭配香辣酱、芝麻与海苔。", "105 g",
        "https://buldak.com/us/product/buldak-ramen-original-big-bowl/",
    ),
    _snack_item("880700", "Pocky chocolate", "Pocky Chocolate Biscuit Sticks", "百奇巧克力味饼干棒", "cookies", "Galletas", "Pocky", "palitos de galleta crujiente cubiertos con chocolate.", "crisp biscuit sticks coated in chocolate.", "酥脆饼干棒裹上巧克力涂层。", "70 g", "https://www.glico.com/global/"),
    _snack_item("880701", "Pocky fresa", "Pocky Strawberry Biscuit Sticks", "百奇草莓味饼干棒", "cookies", "Galletas", "Pocky", "palitos de galleta con cobertura dulce de fresa.", "biscuit sticks with a sweet strawberry coating.", "饼干棒裹上香甜草莓涂层。", "51 g", "https://www.glico.com/global/"),
    _snack_item("807331", "KitKat chocolate oscuro", "KitKat Dark Chocolate Pouch", "奇巧黑巧克力威化", "cookies", "Chocolate", "KitKat", "obleas crujientes cubiertas con chocolate oscuro.", "crisp wafers coated in dark chocolate.", "酥脆威化裹上黑巧克力。", "96 g", "https://www.kitkat.com/"),
    _snack_item("807341", "KitKat chocolate con leche", "KitKat Milk Chocolate Pouch", "奇巧牛奶巧克力威化", "cookies", "Chocolate", "KitKat", "obleas crujientes cubiertas con chocolate con leche.", "crisp wafers coated in milk chocolate.", "酥脆威化裹上牛奶巧克力。", "96 g", "https://www.kitkat.com/"),
    _snack_item("807810", "Maiduowei gomita de mango pelable", "Maiduowei Peelable Mango Gummy", "麦多维多芒果剥皮软糖", "candy", "Gomitas", "Maiduowei", "gomita grande de mango hecha con jugo de fruta, con una capa exterior que se puede separar y centro suave.", "large mango gummy made with fruit juice, with a peelable outer layer and soft center.", "添加真实果汁的大芒果剥皮软糖，外层可剥，内芯柔软。", "141 g", "https://www.yami.com/zh/p/metavita-big-mango-gummy-141g/1018137551"),
    _snack_item("164397", "Hsu Fu Chi pastel de piña tradicional", "Hsu Fu Chi Thick Pineapple Cake", "徐福记厚切土凤梨酥", "cookies", "Pastelillo", "Hsu Fu Chi", "pastelillo grueso con relleno de piña dulce y ligeramente ácido.", "thick pastry with sweet, gently tart pineapple filling.", "厚切酥皮包裹酸甜土凤梨馅。", "190 g", "https://www.hsufuchifoods.com/"),
    _snack_item("164398", "Hsu Fu Chi pastel de piña y mango", "Hsu Fu Chi Mango Pineapple Cake", "徐福记台农芒果凤梨酥", "cookies", "Pastelillo", "Hsu Fu Chi", "pastelillo suave con relleno tropical de piña y mango.", "soft pastry with tropical pineapple and mango filling.", "柔软酥皮搭配凤梨与台农芒果馅。", "190 g", "https://www.hsufuchifoods.com/"),
    _snack_item("851110", "Dr. Bear gomita de fresa", "Dr. Bear Strawberry Juice Gummies", "熊博士草莓果汁软糖", "candy", "Gomitas", "Hsu Fu Chi", "gomitas pequeñas con sabor de jugo de fresa.", "small gummies flavored with strawberry juice.", "小包装草莓果汁软糖。", "20 g", "https://www.hsufuchifoods.com/"),
    _snack_item("851120", "Dr. Bear gomitas de frutas", "Dr. Bear Assorted Fruit Gummies", "熊博士缤纷果汁软糖", "candy", "Gomitas", "Hsu Fu Chi", "mezcla de gomitas suaves con distintos sabores frutales.", "soft gummies in assorted fruit flavors.", "多种水果口味的柔软果汁软糖。", "20 g", "https://www.hsufuchifoods.com/"),
    _snack_item("851122", "Dr. Bear ositos de fruta", "Dr. Bear Mixed Fruit Gummy Bears", "熊博士综合水果熊仔软糖", "candy", "Gomitas", "Hsu Fu Chi", "ositos de goma masticables con mezcla de frutas.", "chewy gummy bears with mixed fruit flavors.", "综合水果味熊仔软糖，柔韧有嚼劲。", "60 g", "https://www.hsufuchifoods.com/"),
    _snack_item("851124", "Dr. Bear gomitas de cola", "Dr. Bear Cola Gummies", "熊博士可乐味软糖", "candy", "Gomitas", "Hsu Fu Chi", "gomitas masticables con sabor clásico de cola.", "chewy gummies with classic cola flavor.", "经典可乐味软糖。", "60 g", "https://www.hsufuchifoods.com/"),
    _snack_item("851160", "Dr. Bear gomita de mango pelable", "Dr. Bear Peelable Mango Gummies", "熊博士芒果剥皮软糖", "candy", "Gomitas", "Hsu Fu Chi", "gomita de mango pelable con centro tierno.", "peelable mango gummy with a tender center.", "可剥皮芒果软糖，内芯柔软。", "60 g", "https://www.hsufuchifoods.com/"),
    _snack_item("851180", "Dr. Bear paletas de frutas", "Dr. Bear Assorted Fruit Lollipops", "熊博士综合果汁大棒糖", "candy", "Paletas", "Hsu Fu Chi", "surtido de paletas con sabores de jugo de fruta.", "assorted lollipops with fruit-juice flavors.", "综合果汁口味大棒糖。", "142.5 g", "https://www.hsufuchifoods.com/"),
    _snack_item("851192", "Hsu Fu Chi gomitas de jugo surtidas", "Hsu Fu Chi Assorted Juice Gummies", "徐福记混合果汁橡皮糖", "candy", "Gomitas", "Hsu Fu Chi", "bolsa surtida de gomitas frutales suaves.", "assorted bag of soft fruit gummies.", "混合水果口味软糖袋装。", "230 g", "https://www.hsufuchifoods.com/"),
    _snack_item("851210", "Hsu Fu Chi gomita de mango a granel", "Hsu Fu Chi Bulk Peelable Mango Gummies", "徐福记芒果剥皮软糖（散装）", "candy", "Gomitas", "Hsu Fu Chi", "formato a granel de gomitas pelables de mango.", "bulk-format peelable mango gummies.", "散装可剥皮芒果软糖。", "1.5 kg", "https://www.hsufuchifoods.com/"),
    _snack_item("851220", "Hsu Fu Chi gomita rellena de uva", "Hsu Fu Chi Crystal Grape Filled Gummies", "徐福记水晶葡萄爆浆软糖", "candy", "Gomitas", "Hsu Fu Chi", "gomitas de uva con centro líquido y frutal.", "grape gummies with a juicy liquid center.", "水晶葡萄味爆浆夹心软糖。", "1.5 kg", "https://www.hsufuchifoods.com/"),
    _snack_item("851230", "Hsu Fu Chi gomita rellena de durazno", "Hsu Fu Chi White Peach Filled Gummies", "徐福记白桃爆浆软糖", "candy", "Gomitas", "Hsu Fu Chi", "gomitas de durazno blanco con centro jugoso.", "white peach gummies with a juicy center.", "白桃味爆浆夹心软糖。", "1.5 kg", "https://www.hsufuchifoods.com/"),
    _snack_item("851430", "Hsu Fu Chi palitos de chocolate con animales", "Hsu Fu Chi Chocolate Animal Biscuit Sticks", "徐福记巧克力动物棒", "cookies", "Galletas", "Hsu Fu Chi", "palitos de galleta con chocolate en formato para compartir.", "chocolate biscuit sticks in a share-size format.", "巧克力动物造型饼干棒。", "3 kg", "https://www.hsufuchifoods.com/"),
    _snack_item("851510", "Hsu Fu Chi malvavisco relleno de durazno", "Hsu Fu Chi Peach Filled Marshmallows", "徐福记蜜桃夹心棉花糖", "candy", "Malvavisco", "Hsu Fu Chi", "malvaviscos suaves con relleno de durazno.", "soft marshmallows with peach filling.", "柔软棉花糖搭配蜜桃夹心。", "64 g", "https://www.hsufuchifoods.com/"),
    _snack_item("851800", "Hsu Fu Chi gelatina de maracuyá y té verde", "Hsu Fu Chi Passion Fruit Green Tea Jelly", "徐福记百香果绿茶吸吸冻", "candy", "Gelatina", "Hsu Fu Chi", "gelatina bebible con maracuyá y té verde.", "drinkable jelly with passion fruit and green tea.", "百香果绿茶味可吸果冻。", "150 g", "https://www.hsufuchifoods.com/"),
    _snack_item("851820", "Hsu Fu Chi gelatina de coco", "Hsu Fu Chi Coconut Milk Jelly", "徐福记生椰味吸吸冻", "candy", "Gelatina", "Hsu Fu Chi", "gelatina bebible cremosa con sabor de coco.", "creamy drinkable jelly with coconut flavor.", "生椰味可吸果冻，口感柔滑。", "120 g", "https://www.hsufuchifoods.com/"),
    _snack_item("806170", "Dali Garden pan francés sabor leche", "Dali Garden Milk French Soft Bread", "达利园香奶味法式软面包", "bakery", "Pan", "Dali Garden", "panecillos suaves con aroma dulce de leche.", "soft bread rolls with sweet milk aroma.", "香奶味法式软面包，柔软香甜。", "200 g", "https://www.daliyuan.com/"),
    _snack_item("806160", "Dali Garden pan francés sabor naranja", "Dali Garden Orange French Soft Bread", "达利园香橙味法式软面包", "bakery", "Pan", "Dali Garden", "panecillos suaves con notas dulces de naranja.", "soft bread rolls with sweet orange notes.", "香橙味法式软面包，柔软清香。", "200 g", "https://www.daliyuan.com/"),
    _snack_item("061010", "Ranli pastel de chocolate", "Ranli Chocolate Cake", "然利金山角巧克力蛋糕", "bakery", "Pastel", "Ranli", "pastel triangular de chocolate con bizcocho de huevo y un relleno fresco de fermento láctico.", "triangular chocolate cake with egg sponge and a fresh cultured-milk filling.", "巧克力味金山角蛋糕，以蛋香糕体搭配清爽乳酸菌夹心。", "2 kg", "https://zh.ranlifood.com/Products_details/199.html"),
    _snack_item("061020", "Ranli pastel de cebada verde", "Ranli Barley Leaf Cake", "然利金山角大麦若叶蛋糕", "bakery", "Pastel", "Ranli", "pastel triangular de cebada verde con bizcocho de huevo y relleno fresco de fermento láctico.", "triangular young-barley cake with egg sponge and a fresh cultured-milk filling.", "大麦若叶味金山角蛋糕，以蛋香糕体搭配清爽乳酸菌夹心。", "2 kg", "https://zh.ranlifood.com/Products_details/199.html"),
    _snack_item("061030", "Ranli pastel red velvet", "Ranli Red Velvet Cake", "然利金山角红丝绒蛋糕", "bakery", "Pastel", "Ranli", "pastel triangular red velvet con bizcocho de huevo y relleno fresco de fermento láctico.", "triangular red-velvet cake with egg sponge and a fresh cultured-milk filling.", "红丝绒味金山角蛋糕，以蛋香糕体搭配清爽乳酸菌夹心。", "2 kg", "https://zh.ranlifood.com/Products_details/199.html"),
    _snack_item("061050", "Ranli pastel piel de tigre", "Ranli Tiger Skin Cake", "然利虎皮蛋糕", "bakery", "Pastel", "Ranli", "bizcocho enrollado suave con una cubierta tostada tipo piel de tigre y dos texturas.", "soft rolled sponge with a toasted tiger-skin top and two contrasting textures.", "焦香虎皮包裹柔软蛋糕卷，呈现双层口感。", "2 kg", "https://zh.ranlifood.com/Products/35.html"),
    _snack_item("061060", "Ranli pan de leche en capas", "Ranli Layered Milk Bread", "然利千层牛乳面包", "bakery", "Pan", "Ranli", "pan de leche con capas definidas, textura suave y aroma lácteo intenso.", "layered milk bread with a soft texture and pronounced dairy aroma.", "层次分明的千层牛乳面包，质地柔软、奶香浓郁。", "2 kg", "https://zh.ranlifood.com/Products/35.html"),
    _snack_item("061080", "Ranli rollo suizo", "Ranli Swiss Roll Cake", "然利瑞士卷蛋糕", "bakery", "Pastel", "Ranli", "rollo de bizcocho suave con aroma de huevo y relleno cremoso.", "soft sponge roll with a rich egg aroma and creamy filling.", "蛋香浓郁的柔软瑞士卷，搭配奶油夹心。", "2 kg", "https://zh.ranlifood.com/Products/35.html"),
    _snack_item("854190", "Want Want gomita QQ de uva", "Want Want QQ Grape Gummies", "旺旺QQ巨峰葡萄味软糖", "candy", "Gomitas", "Want Want", "gomitas francesas suaves con sabor de uva Kyoho.", "soft French-style gummies with Kyoho grape flavor.", "巨峰葡萄味法式软糖。", "70 g", "https://www.want-want.com/"),
    _snack_item("854200", "Want Want gomita QQ de cereza", "Want Want QQ Cherry Gummies", "旺旺QQ智利车厘子味软糖", "candy", "Gomitas", "Want Want", "gomitas francesas suaves con sabor de cereza chilena.", "soft French-style gummies with Chilean cherry flavor.", "智利车厘子味法式软糖。", "70 g", "https://www.want-want.com/"),
    _snack_item("854210", "Want Want gomita QQ de durazno", "Want Want QQ Peach Gummies", "旺旺QQ阳山水蜜桃味软糖", "candy", "Gomitas", "Want Want", "gomitas francesas suaves con sabor de durazno de Yangshan.", "soft French-style gummies with Yangshan peach flavor.", "阳山水蜜桃味法式软糖。", "70 g", "https://www.want-want.com/"),
])


# Wholesale packing taken from the three supplied price lists: how many retail
# units travel inside one case, the size of each unit, and the price of that case.
# (units, unit_size, case_price, unit_noun)
CATALOG_PACKS = {
    "811140": (40, "130 g", 1120, "paquetes"),
    "811130": (40, "140 g", 1120, "paquetes"),
    "811200": (40, "140 g", 1120, "paquetes"),
    "811150": (40, "145 g", 1120, "paquetes"),
    "811270": (40, "140 g", 1120, "paquetes"),
    "811320": (40, "140 g", 1120, "paquetes"),
    "811000": (40, "140 g", 1120, "paquetes"),
    "811340": (40, "150 g", 1120, "paquetes"),
    "811220": (40, "135 g", 1120, "paquetes"),
    "811120": (40, "140 g", 1120, "paquetes"),
    "811210": (40, "140 g", 1120, "paquetes"),
    "811616": (6, "115 g", 340, "bowls grandes"),
    "811618": (6, "110 g", 340, "bowls grandes"),
    "811622": (6, "105 g", 340, "bowls grandes"),
    "811624": (6, "105 g", 340, "bowls grandes"),
    "811640": (6, "105 g", 340, "bowls grandes"),
    "811612": (6, "105 g", 290, "bowls grandes"),
    "811650": (12, "169.4 g", 1020, "bowls"),
    "811710": (16, "179 g", 928, "bowls"),
    "811720": (16, "185 g", 928, "bowls"),
    "811910": (12, "120 g", 900, "bolsas"),
    "811920": (12, "120 g", 900, "bolsas"),
    "811430": (6, "70 g", 186, "vasos"),
    "811300": (24, "200 g", 2640, "botellas"),
    "811280": (24, "200 g", 2688, "botellas"),
    "811290": (200, "6 g", 1000, "sobres", 50),
    "811311": (32, "120 g", 896, "bolsas"),
    "811312": (32, "120 g", 896, "bolsas"),
    "811310": (32, "120 g", 896, "bolsas"),
    "811810": (32, "105 g", 1024, "bolsas"),
    "811815": (6, "105 g", 354, "bowls"),
    "811816": (6, "105 g", 354, "bowls"),
    "811814": (6, "100 g", 354, "bowls"),
    "811611": (6, "105 g", 420, "bowls"),
    "634210": (30, "104 g", 507, "bolsas", 5),
    "634220": (30, "106 g", 507, "bolsas", 5),
    "634240": (30, "98 g", 507, "bolsas", 6),
    "634250": (30, "117 g", 507, "bolsas", 5),
    "634260": (30, "100 g", 507, "bolsas", 5),
    "634270": (30, "104 g", 507, "bolsas", 5),
    "634280": (30, "102 g", 507, "bolsas", 5),
    "634252": (12, "108 g", 384, "bowls"),
    "802150": (24, "90 g", 912, "bolsas"),
    "802440": (22, "70 g", 770, "bolsas"),
    "802120": (22, "70 g", 770, "bolsas"),
    "802110": (22, "70 g", 770, "bolsas"),
    "802410": (22, "70 g", 770, "bolsas"),
    "802420": (22, "70 g", 770, "bolsas"),
    "802160": (22, "70 g", 770, "bolsas"),
    "854170": (12, "70 g", 456, "bolsas"),
    "854180": (12, "70 g", 456, "bolsas"),
    "880700": (120, "70 g", 4985.20, "cajas", 10),
    "880701": (120, "51 g", 4985.20, "cajas", 10),
    "807331": (24, "96 g", 1080, "bolsas"),
    "807341": (24, "96 g", 1008, "bolsas"),
    "807810": (24, "141 g", 1320, "bolsas", 12),
    "164397": (20, "190 g", 1440, "cajas"),
    "164398": (20, "190 g", 1500, "cajas"),
    "851110": (120, "20 g", 960, "bolsas", 20),
    "851120": (120, "20 g", 840, "bolsas", 20),
    "851122": (60, "60 g", 1320, "bolsas", 10),
    "851124": (60, "60 g", 1380, "bolsas", 10),
    "851160": (60, "60 g", 1200, "bolsas", 10),
    "851180": (12, "142.5 g", 1320, "bolsas"),
    "851192": (20, "230 g", 1700, "bolsas"),
    "851210": (4, "1.5 kg", 1360, "bolsas"),
    "851220": (4, "1.5 kg", 1280, "bolsas"),
    "851230": (4, "1.5 kg", 1160, "bolsas"),
    "851430": (1, "3 kg", 900, "bolsas"),
    "851510": (20, "64 g", 700, "bolsas"),
    "851800": (40, "150 g", 1100, "bolsas"),
    "851820": (40, "120 g", 1100, "bolsas"),
    "806170": (15, "200 g", 825, "bolsas"),
    "806160": (15, "200 g", 825, "bolsas"),
    "061010": (1, "2 kg", 600, "cajas"),
    "061020": (1, "2 kg", 600, "cajas"),
    "061030": (1, "2 kg", 600, "cajas"),
    "061050": (1, "2 kg", 600, "cajas"),
    "061060": (1, "2 kg", 600, "cajas"),
    "061080": (1, "2 kg", 600, "cajas"),
    "854190": (40, "70 g", 880, "bolsas", 10),
    "854200": (40, "70 g", 880, "bolsas", 10),
    "854210": (40, "70 g", 880, "bolsas", 10),
}


# Relative heat for every noodle/rice-cake item in the main catalog. This is a
# 1–5 storefront scale rather than a claimed Scoville value because several
# brands do not publish SHU figures.
CATALOG_SPICE_LEVELS = {
    "811130": 1, "811270": 2, "811140": 2, "811200": 3, "811150": 3,
    "811320": 2, "811000": 3, "811340": 3, "811220": 4, "811120": 4,
    "811210": 5, "811616": 2, "811618": 3, "811622": 2, "811624": 4,
    "811640": 2, "811650": 2, "811612": 4, "811710": 2, "811720": 4,
    "811430": 4, "811611": 4,
    "811311": 2, "811312": 2, "811310": 3,
    "811810": 1, "811815": 1, "811816": 1, "811814": 1,
    "634210": 1, "634220": 1, "634240": 1, "634250": 2,
    "634260": 1, "634270": 3, "634280": 4, "634252": 4,
}


def apply_pack(product, units, unit_size, case_price, unit_noun, inner=None, promo=None):
    """Attach the wholesale case model every product is sold by."""
    if inner:
        outer = units // inner
        pack_label = f"{outer} paquetes de {inner} {unit_noun} de {unit_size}"
    else:
        pack_label = f"{units} {unit_noun} de {unit_size}"
    product.update(
        units_per_case=units,
        unit_size=unit_size,
        unit_noun=unit_noun,
        inner_packs=inner,
        pack_label=pack_label,
        pack_short=f"{units} {unit_noun}",
        case_total=f"{units} × {unit_size}",
        promo=promo,
        price=float(case_price),
        price_label=f"${case_price:,.0f}",
        unit_price_label=f"${case_price / units:,.2f}",
    )
    return product


# Export names retained from the earlier catalog. The second value is legacy
# Japanese copy and is intentionally not exposed by the three-language UI.
INTL_NAMES = {
    # --- Buldak ---
    "811140": ("Carbonara Buldak Stir-Fried Ramen", "カルボナーラブルダック炒め麺"),
    "811130": ("Cream Carbonara Buldak Stir-Fried Ramen", "クリームカルボナーラブルダック炒め麺"),
    "811200": ("Cheese Buldak Stir-Fried Ramen", "チーズブルダック炒め麺"),
    "811150": ("Quattro Cheese Buldak Stir-Fried Ramen", "クアトロチーズブルダック炒め麺"),
    "811270": ("Rosé Buldak Stir-Fried Ramen", "ロゼブルダック炒め麺"),
    "811320": ("Swicy Buldak Stir-Fried Ramen", "スワイシーブルダック炒め麺"),
    "811000": ("Taco Buldak Stir-Fried Ramen", "タコブルダック炒め麺"),
    "811340": ("Yakisoba Buldak Stir-Fried Ramen", "焼きそばブルダック炒め麺"),
    "811220": ("Habanero Lime Buldak Stir-Fried Ramen", "ハバネロライムブルダック炒め麺"),
    "811120": ("Original Buldak Stir-Fried Ramen", "ブルダック炒め麺"),
    "811210": ("2X Spicy Buldak Stir-Fried Ramen", "2倍辛ブルダック炒め麺"),
    "811616": ("Swicy Buldak Stir-Fried Ramen Big Bowl", "スワイシーブルダック炒め麺 BIG"),
    "811618": ("Quattro Cheese Buldak Stir-Fried Ramen Big Bowl", "クアトロチーズブルダック炒め麺 BIG"),
    "811622": ("Carbonara Buldak Stir-Fried Ramen Big Bowl", "カルボナーラブルダック炒め麺 BIG"),
    "811624": ("Original Buldak Stir-Fried Ramen Big Bowl", "ブルダック炒め麺 BIG"),
    "811640": ("Rosé Buldak Stir-Fried Ramen Big Bowl", "ロゼブルダック炒め麺 BIG"),
    "811650": ("Rosé Buldak Wide Glass Noodle", "ロゼブルダック太春雨"),
    "811612": ("Original Buldak Stir-Fried Ramen Big Bowl", "ブルダック炒め麺 BIG"),
    "811710": ("Carbonara Buldak Tteokbokki", "カルボナーラブルダックトッポギ"),
    "811720": ("Original Buldak Tteokbokki", "ブルダックトッポギ"),
    "811910": ("Buldak Potato Chips Habanero Lime", "ブルダックポテトチップス ハバネロライム"),
    "811920": ("Buldak Potato Chips Original", "ブルダックポテトチップス オリジナル"),
    # --- Refrescos ---
    "833130": ("Coconut Palm Coconut Juice", "椰樹 ココナッツジュース"),
    "833210": ("Wong Lo Kat Herbal Tea", "王老吉 漢方茶"),
    "831190": ("Chi Forest Sparkling Water White Peach", "元気森林 スパークリングウォーター 白桃"),
    "194280": ("Vita Peach Tea", "ビタ ピーチティー"),
    "880350": ("Binggrae Melon Flavored Milk", "ビングレ メロン牛乳"),
    "831214": ("Chi Forest Sparkling Water Lemon Cola", "元気森林 スパークリングウォーター レモンコーラ"),
    "834510": ("Shuiquanwan Lactic Acid Yogurt Drink", "水泉湾 乳酸菌飲料"),
    "832110": ("Master Kong Jasmine Green Tea", "康師傅 ジャスミン緑茶"),
    "832160": ("Master Kong Rock Sugar Pear Drink", "康師傅 氷糖雪梨"),
    "832140": ("Master Kong Honey Pomelo Tea", "康師傅 蜂蜜柚子茶"),
    "831831": ("Hawthorn Juice and Pulp Drink", "山楂樹下 サンザシドリンク"),
    "837410": ("Tea 365 Green Tea Lemon & Lemongrass", "緑茶365 レモン&レモングラス"),
    "837412": ("Tea 365 Green Tea Honey", "緑茶365 ハニー"),
    "831160": ("Chi Forest Sparkling Water Lychee", "元気森林 スパークリングウォーター ライチ"),
    "831220": ("Chi Forest Sparkling Water White Peach Can", "元気森林 スパークリングウォーター 白桃 缶"),
    "831170": ("Chi Forest Sparkling Water Grape Delight", "元気森林 スパークリングウォーター ブドウ"),
    "831140": ("Chi Forest Sparkling Water Orange Vitamin C", "元気森林 スパークリングウォーター オレンジ"),
    "831240": ("Chi Forest Sparkling Water Lychee Can", "元気森林 スパークリングウォーター ライチ 缶"),
    "833320": ("Taisun Grass Jelly Drink Original", "泰山 仙草蜜ドリンク オリジナル"),
    "833330": ("Taisun Grass Jelly Drink Lychee", "泰山 仙草蜜ドリンク ライチ"),
    "833340": ("Taisun Grass Jelly Drink Coconut", "泰山 仙草蜜ドリンク ココナッツ"),
    "837520": ("J WAY Instant Boba Fruit Juice Kit", "J WAY タピオカ フルーツジュースキット"),
    "837510": ("J WAY Instant Boba Milk Tea Kit", "J WAY タピオカ ミルクティーキット"),
    "838210": ("Dongpeng Water Boost Electrolyte Drink Lemon", "東鵬 補水啦 電解質ドリンク レモン"),
    "838212": ("Dongpeng Water Boost Electrolyte Drink Grapefruit", "東鵬 補水啦 電解質ドリンク グレープフルーツ"),
    "838214": ("Dongpeng Water Boost Electrolyte Drink Lychee", "東鵬 補水啦 電解質ドリンク ライチ"),
    "838312": ("Dongpeng Water Boost Electrolyte Drink Lemon 555 ml", "東鵬 補水啦 電解質ドリンク レモン 555ml"),
    "838314": ("Dongpeng Water Boost Electrolyte Drink Lychee 555 ml", "東鵬 補水啦 電解質ドリンク ライチ 555ml"),
    "838310": ("Dongpeng Water Boost Electrolyte Drink Grapefruit 555 ml", "東鵬 補水啦 電解質ドリンク グレープフルーツ 555ml"),
    "880910": ("Haitai Grape Bongbong Juice", "ヘテ ぶどうボンボン"),
    "880010": ("Yogo Vera Aloe Vera Drink Mango", "ヨゴベラ アロエドリンク マンゴー"),
    "880020": ("Yogo Vera Aloe Vera Drink Mango 1.5 L", "ヨゴベラ アロエドリンク マンゴー 1.5L"),
    "880030": ("Yogo Vera Aloe Vera Drink Strawberry", "ヨゴベラ アロエドリンク いちご"),
    "880040": ("Yogo Vera Aloe Vera Drink Peach 1.5 L", "ヨゴベラ アロエドリンク 白桃 1.5L"),
    "831390": ("Ramune Soda Strawberry", "ラムネ いちご"),
    "831410": ("Ramune Soda Original", "ラムネ オリジナル"),
    "880600": ("Tomomasu Watermelon Soda", "友桝飲料 スイカサイダー"),
    "880604": ("Tomomasu White Peach Soda", "友桝飲料 白桃サイダー"),
    "880602": ("Tomomasu Mango Soda", "友桝飲料 マンゴーサイダー"),
}

ZH_NAMES = {
    "811140": "奶油味火鸡面", "811130": "奶油干酪味火鸡面", "811200": "芝士味火鸡面",
    "811150": "芝士联盟火鸡面", "811270": "玫瑰奶油味火鸡面", "811320": "焦糖甜辣味火鸡面",
    "811000": "塔可味火鸡面", "811340": "日式炒面味火鸡面", "811220": "哈瓦那辣椒青柠味火鸡面",
    "811120": "原味火鸡面", "811210": "双倍辣火鸡面", "811616": "焦糖甜辣味火鸡面（大碗）",
    "811618": "芝士联盟火鸡面（大碗）", "811622": "奶油味火鸡面（大碗）",
    "811624": "原味火鸡面（大碗）", "811640": "玫瑰奶油味火鸡面（大碗）",
    "811650": "玫瑰奶油味宽粉", "811612": "原味火鸡面（大碗）", "811710": "奶油味火鸡炒年糕",
    "811720": "原味火鸡炒年糕", "811910": "哈瓦那辣椒青柠味火鸡薯片", "811920": "原味火鸡薯片",
    "833130": "椰树椰汁", "833210": "王老吉凉茶", "831190": "元气森林白桃味气泡水",
    "194280": "维他蜜桃茶", "880350": "宾格瑞哈密瓜牛奶", "831214": "元气森林柠檬可乐味气泡水",
    "834510": "水泉湾乳酸菌饮品", "832110": "康师傅茉莉花茶", "832160": "康师傅冰糖雪梨",
    "832140": "康师傅蜂蜜柚子茶", "831831": "山楂树下山楂汁", "837410": "365绿茶 柠檬香茅味",
    "837412": "365绿茶 蜂蜜味", "831160": "元气森林荔枝味气泡水", "831220": "元气森林白桃味气泡水（罐装）",
    "831170": "元气森林葡萄味气泡水", "831140": "元气森林橙子味气泡水", "831240": "元气森林荔枝味气泡水（罐装）",
    "833320": "泰山仙草蜜 原味", "833330": "泰山仙草蜜 荔枝味", "833340": "泰山仙草蜜 椰子味",
    "837520": "J WAY 鲜果茶波霸套装", "837510": "J WAY 奶茶波霸套装", "838210": "东鹏补水啦 柠檬味",
    "838212": "东鹏补水啦 西柚味", "838214": "东鹏补水啦 荔枝味", "838312": "东鹏补水啦 柠檬味 555ml",
    "838314": "东鹏补水啦 荔枝味 555ml", "838310": "东鹏补水啦 西柚味 555ml", "880910": "海太葡萄汁",
    "880010": "芦荟芒果饮料", "880020": "芦荟芒果饮料 1.5L", "880030": "芦荟草莓饮料",
    "880040": "芦荟白桃饮料 1.5L", "831390": "弹珠汽水 草莓味", "831410": "弹珠汽水 原味",
    "880600": "友桝西瓜汽水", "880604": "友桝白桃汽水", "880602": "友桝芒果汽水",
}


def apply_intl_names(product):
    """Attach language-ready display copy without changing the database row."""
    name_en, _legacy_name = INTL_NAMES.get(product["sku"], (product["name"], ""))
    product["name_es"] = product.get("name_es") or product["name"]
    product["name_en"] = product.get("name_en") or name_en
    product["name_zh"] = product.get("name_zh") or ZH_NAMES.get(product["sku"], product["name"])
    product["description_es"] = product.get("description_es") or product.get("description") or f"{product['name_es']} de {product.get('brand', 'Buldak')}, disponible por caja cerrada."
    product["description_en"] = product.get("description_en") or f"{product['name_en']}, available by wholesale full case."
    product["description_zh"] = product.get("description_zh") or f"{product['name_zh']}，按批发整箱出售。"
    return product


HEAT_LEVELS = {
    # Buldak's official relative scale: mild, medium, hot, very hot, extreme.
    "811140": 2, "811130": 2, "811200": 3, "811150": 3, "811270": 2,
    "811320": 1, "811000": 3, "811340": 4, "811220": 4, "811120": 4,
    "811210": 5, "811616": 1, "811618": 3, "811622": 2, "811624": 4,
    "811640": 2, "811650": 2, "811612": 4, "811710": 2, "811720": 4,
    "811430": 4, "811611": 4,
    # The official chips guide describes these as roughly 4/10 versus the ramen.
    "811910": 2, "811920": 2,
    # Bottled sauce is hotter than the matching creamy noodle profile.
    "811300": 4, "811280": 4, "811290": 4,
    # Other explicitly spicy catalog products.
    "811311": 2, "811312": 3, "811310": 3, "811814": 1,
    "634270": 3, "634280": 2, "634252": 2,
    "802120": 3, "802410": 4,
}

HEAT_WORDS = {
    "es": ("Sin picor", "Muy suave", "Suave", "Medio", "Alto", "Extremo"),
    "en": ("Not spicy", "Very mild", "Mild", "Medium", "Hot", "Extreme"),
    "zh": ("不辣", "微辣", "轻辣", "中辣", "高辣", "极辣"),
}


def apply_heat(product):
    """Attach heat data and state whether the metric belongs in the UI."""
    sku = str(product["sku"])
    level = HEAT_LEVELS.get(sku, CATALOG_SPICE_LEVELS.get(sku, 0))
    product["heat_level"] = level
    product["heat"] = level * 20
    product["heat_label_es"] = f"{HEAT_WORDS['es'][level]} · {level}/5"
    product["heat_label_en"] = f"{HEAT_WORDS['en'][level]} · {level}/5"
    product["heat_label_zh"] = f"{HEAT_WORDS['zh'][level]} · {level}/5"
    product["heat_label"] = product["heat_label_es"]
    product["heat_applicable"] = level > 0
    return product


# Sensory sweetness, not grams of sugar. Category defaults cover products that
# are inherently sweet; savory products only receive a meter when their flavor
# profile has an identifiable sweet note.
SWEETNESS_CATEGORY_LEVELS = {
    "cookies": 4,
    "candy": 5,
    "bakery": 3,
    "te": 2,
    "agua_gas": 2,
    "jugos_lacteos": 4,
    "electrolitos": 2,
    "otros": 3,
    "boba": 4,
}

SWEETNESS_LEVELS = {
    "811140": 1, "811130": 2, "811270": 2, "811320": 3,
    "811340": 2, "811616": 3, "811622": 1, "811640": 2,
    "811650": 2, "811710": 1, "811815": 2,
    "802110": 1, "802420": 1, "802440": 1, "802160": 1,
    "807331": 3,
    "831830": 1,
}

SWEETNESS_LABELS = {
    "es": "Dulzura percibida",
    "en": "Perceived sweetness",
    "zh": "感知甜度",
}

# Exact facts used when a manufacturer source supports the value. Remaining
# products receive a visibly marked category-and-package estimate below.
VERIFIED_STORY_FACTS = {
    "811140": {
        "shu": "2,600", "kcal": "550", "kcal_value": 550,
        "kcal_estimated": False, "cook_time": "5 min", "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/top-12-combos-to-eat-with-buldak-carbonara/",
    },
    "811120": {
        "shu": "4,404", "kcal": "530", "kcal_value": 530,
        "kcal_estimated": False, "cook_time": "5 min", "facts_verified": True,
        "nutrition_source_url": "https://www.samyangfoods.com/eng/brand/view.do?seq=245",
    },
    "811150": {
        "shu": "≈2,323", "kcal": "590", "kcal_value": 590,
        "kcal_estimated": False, "cook_time": "5 min 30 s", "facts_verified": True,
        "nutrition_source_url": "https://samyangamerica.com/buldak/quattro-cheese",
    },
    "811200": {
        "shu": "2,323",
        "kcal": "550",
        "kcal_value": 550,
        "kcal_estimated": False,
        "cook_time": "5 min",
        "nutrition_source_url": "https://www.samyangfoods.com/eng/brand/view.do?seq=299",
        "facts_verified": True,
        "facts_sources": [
            "https://www.samyangfoods.com/kor/publicity/press/view.do?pageIndex=1&pageUnit=10&seq=655",
            "https://www.samyangfoods.com/eng/brand/view.do?seq=299",
            "https://buldak.com/us/product/buldak-ramen-cheese/",
        ],
    },
    "811430": {
        "kcal": "280", "kcal_value": 280, "kcal_estimated": False,
        "cook_time": "4 min", "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/5-places-to-visit-in-korea-for-local-buldak-ramen-experience/",
    },
    "811622": {
        "kcal": "470", "kcal_value": 470, "kcal_estimated": False,
        "cook_time": "4 min", "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/top-12-combos-to-eat-with-buldak-carbonara/",
    },
    "811624": {
        "kcal": "440", "kcal_value": 440, "kcal_estimated": False,
        "cook_time": "4 min", "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/5-places-to-visit-in-korea-for-local-buldak-ramen-experience/",
    },
    "811612": {
        "kcal": "440", "kcal_value": 440, "kcal_estimated": False,
        "cook_time": "4 min", "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/5-places-to-visit-in-korea-for-local-buldak-ramen-experience/",
    },
    "811611": {
        "kcal": "440", "kcal_value": 440, "kcal_estimated": False,
        "cook_time": "4 min", "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/5-places-to-visit-in-korea-for-local-buldak-ramen-experience/",
    },
    "811710": {
        "kcal": "450", "kcal_value": 450, "kcal_estimated": False,
        "cook_time": "2 min 30 s", "facts_verified": True,
        "nutrition_source_url": "https://wordpress.buldak.com/us/blog/the-best-way-to-enjoy-buldak-tteokbokki/",
    },
    "811720": {
        "kcal": "450", "kcal_value": 450, "kcal_estimated": False,
        "cook_time": "2 min 30 s", "facts_verified": True,
        "nutrition_source_url": "https://wordpress.buldak.com/us/blog/the-best-way-to-enjoy-buldak-tteokbokki/",
    },
    "811910": {
        "kcal": "160", "kcal_value": 160, "kcal_estimated": False,
        "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/buldak-potato-chip-guide/",
        "kcal_basis_es": "por porción", "kcal_basis_en": "per serving", "kcal_basis_zh": "每份",
    },
    "811920": {
        "kcal": "160", "kcal_value": 160, "kcal_estimated": False,
        "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/buldak-potato-chip-guide/",
        "kcal_basis_es": "por porción", "kcal_basis_en": "per serving", "kcal_basis_zh": "每份",
    },
    "811300": {
        "kcal": "15", "kcal_value": 15, "kcal_estimated": False,
        "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/buldak-sauce-10-best-food-hacks/",
        "kcal_basis_es": "por 6 g", "kcal_basis_en": "per 6 g", "kcal_basis_zh": "每 6 克",
    },
    "811280": {
        "kcal": "10", "kcal_value": 10, "kcal_estimated": False,
        "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/buldak-sauce-10-best-food-hacks/",
        "kcal_basis_es": "por 6 g", "kcal_basis_en": "per 6 g", "kcal_basis_zh": "每 6 克",
    },
    "811290": {
        "kcal": "10", "kcal_value": 10, "kcal_estimated": False,
        "facts_verified": True,
        "nutrition_source_url": "https://buldak.com/us/blog/buldak-sauce-10-best-food-hacks/",
        "kcal_basis_es": "por sobre de 6 g", "kcal_basis_en": "per 6 g stick", "kcal_basis_zh": "每 6 克条装",
    },
}


CALORIE_DENSITY_KCAL_PER_GRAM = {
    "soups": 3.85,
    "bowls": 3.85,
    "tteokbokki": 2.52,
    "chips": 5.40,
    "cookies": 4.80,
    "candy": 3.55,
    "bakery": 3.80,
    "sauces": 2.20,
}

DRINK_CALORIES_PER_100_ML = {
    "te": 32,
    "agua_gas": 38,
    "jugos_lacteos": 55,
    "electrolitos": 20,
    "otros": 35,
    "boba": 130,
}


def _unit_amount(value):
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(kg|g|ml|l)\b", str(value), re.I)
    if not match:
        return 100.0, "g"
    amount = float(match.group(1))
    unit = match.group(2).lower()
    if unit in {"kg", "l"}:
        amount *= 1000
        unit = "g" if unit == "kg" else "ml"
    return amount, unit


def _rounded_kcal(value):
    return max(0, int(5 * round(float(value) / 5)))


def apply_catalog_facts(product):
    """Provide relevant cooking and calorie facts for every catalog food."""
    category = product.get("category", "")
    amount, _unit = _unit_amount(product.get("unit_size") or product.get("weight"))
    density = CALORIE_DENSITY_KCAL_PER_GRAM.get(category, 3.5)
    bulk = amount > 500
    basis_amount = 100 if bulk else amount
    estimated_kcal = _rounded_kcal(density * basis_amount)
    product.update(
        kcal=f"≈{estimated_kcal}",
        kcal_value=estimated_kcal,
        kcal_estimated=True,
        kcal_basis_es="por 100 g" if bulk else "por paquete",
        kcal_basis_en="per 100 g" if bulk else "per pack",
        kcal_basis_zh="每 100 克" if bulk else "每包",
        requires_cooking=category in {"soups", "bowls", "tteokbokki"},
        cook_time_applicable=category in {"soups", "bowls", "tteokbokki"},
        facts_verified=False,
        nutrition_source_url="https://fdc.nal.usda.gov/",
    )
    if category == "soups":
        product["cook_time"] = "4 min" if product.get("brand") == "Master Kong" else "5 min"
    elif category == "bowls":
        product["cook_time"] = "4 min"
    elif category == "tteokbokki":
        product["cook_time"] = "2 min 30 s"
    else:
        product["cook_time"] = None
    product.update(VERIFIED_STORY_FACTS.get(str(product["sku"]), {}))
    product.setdefault("kcal_basis_es", "por paquete")
    product.setdefault("kcal_basis_en", "per pack")
    product.setdefault("kcal_basis_zh", "每包")
    product["kcal_basis"] = product["kcal_basis_es"]
    return product


def apply_drink_facts(product):
    """Estimate calories by container, preserving zero-sugar logic and basis."""
    amount, unit = _unit_amount(product.get("unit_size") or product.get("weight"))
    zero_sugar = any(
        phrase in (product.get("description_es") or "").lower()
        for phrase in ("cero azúcar", "sin azúcar")
    )
    density = 0 if zero_sugar else DRINK_CALORIES_PER_100_ML.get(product.get("category"), 35)
    bulk = amount > 750
    if product.get("category") == "boba" or unit == "g":
        value = density * amount / 100
        basis = ("por kit", "per kit", "每份套装")
    elif bulk:
        value = density
        basis = ("por 100 ml", "per 100 ml", "每 100 毫升")
    else:
        value = density * amount / 100
        basis = ("por envase", "per container", "每瓶/罐")
    kcal = _rounded_kcal(value)
    product.update(
        kcal=f"≈{kcal}", kcal_value=kcal, kcal_estimated=True,
        kcal_basis_es=basis[0], kcal_basis_en=basis[1], kcal_basis_zh=basis[2],
        kcal_basis=basis[0], requires_cooking=False, cook_time=None,
        cook_time_applicable=False, facts_verified=False,
        nutrition_source_url="https://fdc.nal.usda.gov/",
    )
    return product


def apply_sweetness(product):
    """Attach a localized sweetness meter only when the product tastes sweet."""
    level = SWEETNESS_LEVELS.get(
        str(product["sku"]),
        SWEETNESS_CATEGORY_LEVELS.get(product.get("category"), 0),
    )
    product["sweetness_level"] = level
    product["sweetness"] = level * 20
    product["sweetness_label_es"] = f"{SWEETNESS_LABELS['es']} · {level}/5"
    product["sweetness_label_en"] = f"{SWEETNESS_LABELS['en']} · {level}/5"
    product["sweetness_label_zh"] = f"{SWEETNESS_LABELS['zh']} · {level}/5"
    product["sweetness_label"] = product["sweetness_label_es"]
    product["sweetness_applicable"] = level > 0
    return product


for sort_order, catalog_product in enumerate(CATALOG_PRODUCTS, start=1):
    # Older rows used product-format categories; the complete store uses the
    # three departments requested by the shop owner.
    if catalog_product["category"] == "bags":
        catalog_product.update(category="soups", category_label="Sopa y fideos")
    elif catalog_product["category"] == "snacks":
        catalog_product.update(category="chips", category_label="Papas y botanas")
    catalog_product.setdefault("brand", "Buldak")
    catalog_product.update(
        id=catalog_product["sku"],
        sort_order=sort_order,
        is_available=not catalog_product["status"].startswith("Agotado"),
    )
    apply_pack(catalog_product, *CATALOG_PACKS[catalog_product["sku"]])
    spice_level = CATALOG_SPICE_LEVELS.get(catalog_product["sku"])
    if spice_level is not None:
        catalog_product["spice_level"] = spice_level
    apply_intl_names(catalog_product)
    apply_heat(catalog_product)
    apply_sweetness(catalog_product)
    apply_catalog_facts(catalog_product)
    catalog_product["description_verified"] = True
    catalog_product["case"] = catalog_product["pack_label"]


REFRESCOS_CATEGORIES = [
    {"id": "all", "label": "Todos"},
    {"id": "te", "label": "Té"},
    {"id": "agua_gas", "label": "Agua con gas"},
    {"id": "jugos_lacteos", "label": "Jugos y lácteos"},
    {"id": "electrolitos", "label": "Electrolitos"},
    {"id": "boba", "label": "Boba"},
    {"id": "otros", "label": "Otros"},
]

_REFRESCOS_CATEGORY_LABELS = {c["id"]: c["label"] for c in REFRESCOS_CATEGORIES}


def _refresco(sku, name, category, image, description, units, unit_size, case_price,
              unit_noun="botellas", inner=None, promo=None):
    """One wholesale line from the Catalogo 0908 drinks pages."""
    product = {
        "sku": sku, "id": sku, "name": name, "category": category,
        "category_label": _REFRESCOS_CATEGORY_LABELS[category],
        "weight": f"{unit_size} · {unit_noun.rstrip('es').rstrip('s')}",
        "image": f"/assets/refrescos/{image}.webp?v=4",
        "description": description, "status": "Disponible",
    }
    apply_pack(product, units, unit_size, case_price, unit_noun, inner=inner, promo=promo)
    product["case"] = product["pack_label"]
    return product


def _mx26_drink(
    sku, name_es, name_en, name_zh, category, brand,
    description_es, description_en, description_zh,
    units, unit_size, case_price, unit_noun="botellas", inner=None,
):
    """Create a multilingual beverage row from CATALAGO ACTUALIZADO MX26."""
    product = _refresco(
        sku, name_es, category, sku, description_es,
        units, unit_size, case_price, unit_noun, inner=inner,
    )
    product.update(
        name_es=name_es,
        name_en=name_en,
        name_zh=name_zh,
        description_es=description_es,
        description_en=description_en,
        description_zh=description_zh,
        brand=brand,
    )
    return product


# Promotions printed in the source catalog (买十送一 / 买五送二).
BUY_10_GET_1 = "promo.buy10get1"
BUY_5_GET_2 = "promo.buy5get2"


REFRESCOS_PRODUCTS = [
    _refresco("833130", "Coco Palm Jugo de Coco", "jugos_lacteos", "833130",
        "Jugo de coco 100% natural en lata, ligero, dulce y sin pulpa.",
        24, "245 ml", 650, "latas"),
    _refresco("833210", "Wang Lo Kat Té de Hierbas", "otros", "833210",
        "Bebida herbal china clásica (凉茶), dulce y refrescante, ideal para acompañar comidas picantes.",
        24, "310 ml", 450, "latas"),
    _refresco("831190", "Genki Forest Soda Durazno Blanco", "agua_gas", "831190",
        "Agua con gas sabor durazno blanco, cero azúcar, ligera y burbujeante.",
        15, "480 ml", 435),
    _refresco("194280", "Vita Té de Durazno", "te", "194280",
        "Té de durazno clásico, dulce y ligero, listo para tomar frío.",
        48, "250 ml", 850),
    _refresco("880350", "Binggrae Leche Sabor Melón", "jugos_lacteos", "880350",
        "Bebida láctea coreana con sabor a melón, cremosa y dulce.",
        24, "200 ml", 650),
    _refresco("831214", "Genki Forest Cola Limón Gasificada", "agua_gas", "831214",
        "Agua con gas sabor cola y limón, cero azúcar.",
        15, "480 ml", 425),
    _refresco("834510", "Shui Lian Wan Yogurt Original", "jugos_lacteos", "834510",
        "Bebida con sabor a yogurt, cremosa y ligeramente dulce.",
        20, "280 ml", 750),
    _refresco("832110", "Kang Shi Fu Té de Jazmín", "te", "832110",
        "Té verde con jazmín en botella verde, refrescante y floral.",
        15, "500 ml", 255),
    _refresco("832160", "Kang Shi Fu Pera con Azúcar de Roca", "te", "832160",
        "Té de pera con azúcar de roca, suave y ligeramente dulce.",
        15, "500 ml", 255),
    _refresco("832140", "Kang Shi Fu Té de Toronja con Miel", "te", "832140",
        "Té de toronja (pomelo) con miel, cítrico y dulce.",
        15, "500 ml", 255),
    _refresco("831831", "Shan Zha Shu Xia Bebida de Espino", "otros", "831831",
        "Bebida de espino (shanzha) agridulce, un clásico chino digestivo.",
        15, "350 ml", 600, promo=BUY_5_GET_2),
    _refresco("837410", "MASAN Té Verde Limón y Limoncillo", "te", "837410",
        "Té verde con limón y limoncillo, fresco y aromático.",
        24, "500 ml", 385),
    _refresco("837412", "MASAN Té Verde con Miel", "te", "837412",
        "Té verde suave endulzado con miel.",
        24, "500 ml", 385),
    _refresco("831160", "Genki Forest Soda Lichi", "agua_gas", "831160",
        "Agua con gas sabor lichi, cero azúcar, ligera y afrutada.",
        15, "480 ml", 435),
    _refresco("831220", "Genki Forest Soda Durazno Blanco Lata", "agua_gas", "831220",
        "Versión en lata del agua con gas sabor durazno blanco, cero azúcar.",
        24, "330 ml", 435, "latas", inner=6),
    _refresco("831170", "Genki Forest Soda Uva Negra de Verano", "agua_gas", "831170",
        "Agua con gas sabor uva negra, cero azúcar, dulce y burbujeante.",
        15, "480 ml", 369),
    _refresco("831140", "Genki Forest Soda Naranja con Vitamina C", "agua_gas", "831140",
        "Agua con gas sabor naranja con vitamina C, cero azúcar.",
        15, "480 ml", 435),
    _refresco("831240", "Genki Forest Soda Lichi Lata", "agua_gas", "831240",
        "Versión en lata del agua con gas sabor lichi, cero azúcar.",
        24, "330 ml", 475, "latas", inner=6),
    _refresco("833320", "Tai Shan Gelatina de Hierba Original", "otros", "833320",
        "Bebida de gelatina de hierba (仙草蜜), refrescante y ligeramente dulce.",
        24, "330 g", 510, "latas", inner=6),
    _refresco("833330", "Tai Shan Gelatina de Hierba Lichi", "otros", "833330",
        "Gelatina de hierba con sabor a lichi.",
        24, "330 g", 510, "latas", inner=6),
    _refresco("833340", "Tai Shan Gelatina de Hierba Coco", "otros", "833340",
        "Gelatina de hierba con sabor a coco.",
        24, "330 g", 510, "latas", inner=6),
    _refresco("837520", "J WAY Boba de Jugo de Fruta", "boba", "837520",
        "Kit de boba con jugo de fruta, 8 vasos individuales listos para preparar.",
        8, "125 g", 450, "vasos"),
    _refresco("837510", "J WAY Boba de Té con Leche", "boba", "837510",
        "Kit de boba de té con leche, 8 vasos individuales listos para preparar.",
        8, "78 g", 350, "vasos"),
    _refresco("838210", "Dongpeng Electrolitos Limón", "electrolitos", "838210",
        "Bebida electrolítica sabor limón para hidratación rápida.",
        12, "1000 ml", 415, promo=BUY_10_GET_1),
    _refresco("838212", "Dongpeng Electrolitos Toronja", "electrolitos", "838212",
        "Bebida electrolítica sabor toronja para hidratación rápida.",
        12, "1000 ml", 415, promo=BUY_10_GET_1),
    _refresco("838214", "Dongpeng Electrolitos Lichi", "electrolitos", "838214",
        "Bebida electrolítica sabor lichi para hidratación rápida.",
        12, "1000 ml", 415, promo=BUY_10_GET_1),
    _refresco("838312", "Dongpeng Electrolitos Limón 555 ml", "electrolitos", "838312",
        "Presentación de 555 ml de la bebida electrolítica sabor limón.",
        24, "555 ml", 575, promo=BUY_10_GET_1),
    _refresco("838314", "Dongpeng Electrolitos Lichi 555 ml", "electrolitos", "838314",
        "Presentación de 555 ml de la bebida electrolítica sabor lichi.",
        24, "555 ml", 575, promo=BUY_10_GET_1),
    _refresco("838310", "Dongpeng Electrolitos Toronja 555 ml", "electrolitos", "838310",
        "Presentación de 555 ml de la bebida electrolítica sabor toronja.",
        24, "555 ml", 575, promo=BUY_10_GET_1),
    _refresco("880910", "Haitai Jugo de Uva en Lata", "jugos_lacteos", "880910",
        "Jugo de uva coreano en lata, dulce y con trocitos de fruta (봉봉).",
        72, "238 ml", 1750, "latas", inner=12),
    _refresco("880010", "Yogo Bebida de Mango con Aloe", "jugos_lacteos", "880010",
        "Bebida de mango con trocitos de aloe vera.",
        20, "500 ml", 850),
    _refresco("880020", "Yogo Bebida de Mango con Aloe 1.5 L", "jugos_lacteos", "880020",
        "Presentación de 1.5 L de la bebida de mango con aloe vera.",
        12, "1.5 L", 1100),
    _refresco("880030", "Yogo Bebida de Fresa con Aloe", "jugos_lacteos", "880030",
        "Bebida de fresa con trocitos de aloe vera.",
        20, "500 ml", 850),
    _refresco("880040", "Yogo Bebida de Durazno con Aloe 1.5 L", "jugos_lacteos", "880040",
        "Presentación de 1.5 L de la bebida de durazno con aloe vera.",
        12, "1.5 L", 1100),
    _refresco("831390", "Ramune Fresa", "agua_gas", "831390",
        "Soda japonesa Ramune sabor fresa, con su clásica botella de canica.",
        30, "200 ml", 950),
    _refresco("831410", "Ramune Original", "agua_gas", "831410",
        "Soda japonesa Ramune sabor original, con su clásica botella de canica.",
        30, "200 ml", 950),
    _refresco("880600", "Tomomasu Soda Sabor Sandía", "agua_gas", "880600",
        "Soda artesanal japonesa sabor sandía.",
        24, "300 ml", 1225),
    _refresco("880604", "Tomomasu Soda Sabor Durazno Blanco", "agua_gas", "880604",
        "Soda artesanal japonesa sabor durazno blanco.",
        24, "300 ml", 1225),
    _refresco("880602", "Tomomasu Soda Sabor Mango", "agua_gas", "880602",
        "Soda artesanal japonesa sabor mango.",
        24, "300 ml", 1225),
]

REFRESCOS_PRODUCTS.extend([
    _mx26_drink("832120", "Master Kong té negro helado", "Master Kong Iced Black Tea", "康师傅冰红茶", "te", "Master Kong",
        "Té negro frío con un toque cítrico y dulzor equilibrado.", "Chilled black tea with a citrus note and balanced sweetness.", "清爽冰红茶，带柑橘香气与适度甜味。", 15, "500 ml", 285),
    _mx26_drink("832180", "Master Kong bebida de ciruela ácida", "Master Kong Sour Plum Drink", "康师傅酸梅汤", "te", "Master Kong",
        "Bebida tradicional de ciruela ahumada, agridulce y refrescante.", "Traditional smoked-plum drink, tangy, sweet and refreshing.", "传统酸梅汤，酸甜清爽并带淡淡烟熏风味。", 15, "500 ml", 285),
    _mx26_drink("832150", "Master Kong té verde", "Master Kong Green Tea", "康师傅绿茶", "te", "Master Kong",
        "Té verde listo para beber, ligero y refrescante.", "Light, refreshing ready-to-drink green tea.", "清淡爽口的即饮绿茶。", 15, "500 ml", 285),
    _mx26_drink("832130", "Master Kong té de jazmín con miel", "Master Kong Jasmine Honey Tea", "康师傅茉莉蜜茶", "te", "Master Kong",
        "Té de jazmín floral suavemente endulzado con miel.", "Floral jasmine tea gently sweetened with honey.", "茉莉花茶融合蜂蜜甜香。", 15, "500 ml", 285),
    _mx26_drink("831180", "Chi Forest soda de manzana verde", "Chi Forest Green Apple Sparkling Water", "元气森林青苹果气泡水", "agua_gas", "Chi Forest",
        "Agua con gas de manzana verde, fresca y afrutada.", "Crisp, fruity green-apple sparkling water.", "清脆果香的青苹果气泡水。", 15, "480 ml", 435),
    _mx26_drink("831270", "Chi Forest soda de durazno blanco", "Chi Forest White Peach Sparkling Water", "元气森林白桃气泡水", "agua_gas", "Chi Forest",
        "Agua con gas de durazno blanco en botella.", "White-peach sparkling water in a bottle.", "瓶装白桃气泡水。", 15, "480 ml", 435),
    _mx26_drink("831230", "Chi Forest soda de uva negra · lata", "Chi Forest Black Grape Sparkling Water · Can", "元气森林夏黑葡萄气泡水（罐装）", "agua_gas", "Chi Forest",
        "Soda de uva negra en lata, ligera y burbujeante.", "Light, bubbly black-grape sparkling water in a can.", "清爽起泡的夏黑葡萄罐装气泡水。", 24, "330 ml", 473, "latas", inner=6),
    _mx26_drink("831250", "Chi Forest soda de naranja · lata", "Chi Forest Orange Sparkling Water · Can", "元气森林橙味气泡水（罐装）", "agua_gas", "Chi Forest",
        "Soda de naranja en lata con un perfil cítrico brillante.", "Canned orange sparkling water with a bright citrus profile.", "清新明亮的橙味罐装气泡水。", 24, "330 ml", 473, "latas", inner=6),
    _mx26_drink("831290", "Chi Forest soda de fresa · lata", "Chi Forest Strawberry Sparkling Water · Can", "元气森林草莓气泡水（罐装）", "agua_gas", "Chi Forest",
        "Soda de fresa en lata, aromática y refrescante.", "Fragrant, refreshing strawberry sparkling water in a can.", "芳香清爽的草莓罐装气泡水。", 24, "330 ml", 473, "latas", inner=6),
    _mx26_drink("831310", "Alienergy electrolitos de limón", "Alienergy Lime Electrolyte Drink", "外星人青柠电解质水", "electrolitos", "Alienergy",
        "Bebida con electrolitos sabor limón para hidratarse fría.", "Lime electrolyte drink made for cold refreshment.", "青柠味电解质水，冰镇饮用更清爽。", 15, "500 ml", 495),
    _mx26_drink("831320", "Alienergy electrolitos de durazno blanco", "Alienergy White Peach Electrolyte Drink", "外星人白桃电解质水", "electrolitos", "Alienergy",
        "Bebida con electrolitos de durazno blanco, ligera y afrutada.", "Light, fruity white-peach electrolyte drink.", "轻盈果香的白桃味电解质水。", 15, "500 ml", 495),
    _mx26_drink("833110", "Coconut Palm leche de coco", "Coconut Palm Coconut Milk Drink", "椰树牌椰汁", "jugos_lacteos", "Coconut Palm",
        "La clásica bebida cremosa de leche de coco en lata.", "Classic creamy coconut-milk drink in a can.", "经典椰树牌罐装椰汁。", 24, "245 ml", 480, "latas", inner=6),
    _mx26_drink("833720", "Kirin Afternoon Tea · té con leche", "Kirin Afternoon Tea Milk Tea", "麒麟午后红茶奶茶", "te", "Kirin",
        "Té negro con leche de textura suave y sabor equilibrado.", "Smooth black milk tea with a balanced flavor.", "口感顺滑、风味平衡的红茶奶茶。", 24, "500 ml", 840),
    _mx26_drink("836110", "Mizone durazno", "Mizone Peach Vitamin Drink", "脉动桃子味", "electrolitos", "Mizone",
        "Bebida vitaminada sabor durazno, ligera y refrescante.", "Light, refreshing peach-flavored vitamin drink.", "清爽轻盈的桃子味维生素饮料。", 15, "600 ml", 420),
    _mx26_drink("831830", "Bebida de espino sin azúcar", "Sugar-Free Hawthorn Drink", "无糖山楂饮料", "otros", "Shan Zha Shu Xia",
        "Bebida agridulce de espino, sin azúcar.", "Tangy-sweet hawthorn drink with no sugar.", "酸甜清爽的无糖山楂饮料。", 15, "350 ml", 600),
    _mx26_drink("834520", "Yogurt bebible de fresa", "Strawberry Yogurt Drink", "草莓味乳酸菌饮料", "jugos_lacteos", "Shui Lian Wan",
        "Bebida de yogurt de fresa, cremosa y afrutada.", "Creamy, fruity strawberry yogurt drink.", "香甜顺滑的草莓味乳酸菌饮料。", 20, "280 ml", 760),
    _mx26_drink("834530", "Yogurt bebible de mango", "Mango Yogurt Drink", "芒果味乳酸菌饮料", "jugos_lacteos", "Shui Lian Wan",
        "Bebida de yogurt de mango, cremosa y tropical.", "Creamy, tropical mango yogurt drink.", "浓郁顺滑的芒果味乳酸菌饮料。", 20, "280 ml", 760),
    _mx26_drink("837210", "Arctic Ocean soda de naranja · vidrio", "Arctic Ocean Orange Soda · Glass Bottle", "北冰洋橙汁汽水（玻璃瓶）", "agua_gas", "Arctic Ocean",
        "Soda china clásica de naranja en botella de vidrio.", "Classic Chinese orange soda in a glass bottle.", "经典北冰洋玻璃瓶橙汁汽水。", 12, "248 ml", 384),
    _mx26_drink("871110", "Arctic Ocean soda de naranja · lata", "Arctic Ocean Orange Soda · Can", "北冰洋橙汁汽水（罐装）", "agua_gas", "Arctic Ocean",
        "La soda clásica de naranja en presentación de lata.", "The classic orange soda in a can.", "经典北冰洋罐装橙汁汽水。", 24, "11 oz", 600, "latas"),
    _mx26_drink("880170", "Woongjin bebida de aloe", "Woongjin Aloe Drink", "熊津芦荟饮料", "jugos_lacteos", "Woongjin",
        "Bebida coreana de aloe, dulce y refrescante.", "Sweet, refreshing Korean aloe drink.", "清甜爽口的韩国芦荟饮料。", 20, "500 ml", 760),
    _mx26_drink("880210", "GUGEN bebida de coco con plátano", "GUGEN Banana Coconut Milk Drink", "GUGEN 香蕉味椰奶饮料", "jugos_lacteos", "GUGEN",
        "Bebida cremosa de coco y plátano con nata de coco.", "Creamy banana coconut drink with nata de coco.", "香浓顺滑的香蕉味椰奶果粒饮料。", 24, "290 ml", 980, "botellas", inner=6),
    _mx26_drink("880220", "GUGEN bebida de coco con mango", "GUGEN Mango Coconut Milk Drink", "GUGEN 芒果味椰奶饮料", "jugos_lacteos", "GUGEN",
        "Bebida cremosa de coco y mango con nata de coco.", "Creamy mango coconut drink with nata de coco.", "香浓顺滑的芒果味椰奶果粒饮料。", 24, "290 ml", 980, "botellas", inner=6),
    _mx26_drink("880230", "GUGEN bebida de coco con fresa", "GUGEN Strawberry Coconut Milk Drink", "GUGEN 草莓味椰奶饮料", "jugos_lacteos", "GUGEN",
        "Bebida cremosa de coco y fresa con nata de coco.", "Creamy strawberry coconut drink with nata de coco.", "香浓顺滑的草莓味椰奶果粒饮料。", 24, "290 ml", 980, "botellas", inner=6),
    _mx26_drink("880330", "Binggrae leche de plátano", "Binggrae Banana Flavored Milk", "宾格瑞香蕉牛奶", "jugos_lacteos", "Binggrae",
        "La bebida láctea coreana clásica con sabor a plátano.", "The classic Korean banana-flavored milk drink.", "经典韩国宾格瑞香蕉牛奶。", 24, "200 ml", 720, "botellas", inner=6),
    _mx26_drink("880340", "Binggrae leche de fresa", "Binggrae Strawberry Flavored Milk", "宾格瑞草莓牛奶", "jugos_lacteos", "Binggrae",
        "Bebida láctea coreana suave con sabor a fresa.", "Smooth Korean strawberry-flavored milk drink.", "顺滑香甜的韩国草莓牛奶。", 24, "200 ml", 720, "botellas", inner=6),
    _mx26_drink("880360", "Binggrae leche de taro", "Binggrae Taro Flavored Milk", "宾格瑞香芋牛奶", "jugos_lacteos", "Binggrae",
        "Bebida láctea coreana cremosa con sabor a taro.", "Creamy Korean taro-flavored milk drink.", "香浓顺滑的韩国香芋牛奶。", 24, "200 ml", 720, "botellas", inner=6),
    _mx26_drink("880370", "Binggrae leche de café", "Binggrae Coffee Flavored Milk", "宾格瑞咖啡牛奶", "jugos_lacteos", "Binggrae",
        "Bebida láctea coreana con café, suave y dulce.", "Smooth, sweet Korean coffee-flavored milk drink.", "顺滑香甜的韩国咖啡牛奶。", 24, "200 ml", 720, "botellas", inner=6),
    _mx26_drink("831430", "Ramune naranja", "Ramune Orange", "哈达波子汽水橙子味", "agua_gas", "Ramune",
        "Soda japonesa Ramune sabor naranja con botella de canica.", "Orange Ramune soda in the classic marble bottle.", "经典弹珠瓶橙子味波子汽水。", 30, "200 ml", 1050),
    _mx26_drink("831490", "Ramune yuzu", "Ramune Yuzu", "哈达波子汽水柚子味", "agua_gas", "Ramune",
        "Soda japonesa Ramune con el perfil cítrico del yuzu.", "Ramune soda with a bright yuzu-citrus profile.", "清新柚子风味的弹珠汽水。", 30, "200 ml", 1050),
    _mx26_drink("880601", "Tomomasu soda de durazno blanco", "Tomomasu White Peach Soda", "友桝白桃汽水", "agua_gas", "Tomomasu",
        "Soda artesanal japonesa de durazno blanco.", "Japanese craft white-peach soda.", "日本友桝白桃风味汽水。", 24, "300 ml", 1200),
    _mx26_drink("837110", "Red Bull China", "Red Bull China", "红牛维生素功能饮料", "otros", "Red Bull",
        "Bebida energética Red Bull en su presentación china.", "Red Bull energy drink in its Chinese-market can.", "中国版红牛维生素功能饮料。", 24, "245 ml", 840, "latas"),
    _mx26_drink("A72103", "Want Want Hot Kid leche", "Want Want Hot Kid Milk Drink", "旺旺旺仔牛奶", "jugos_lacteos", "Want Want",
        "Bebida láctea dulce Want Want en lata.", "Sweet Want Want milk drink in a can.", "经典旺旺旺仔牛奶罐装饮品。", 24, "245 ml", 750, "latas"),
])

for sort_order, refresco_product in enumerate(REFRESCOS_PRODUCTS, start=1):
    brand_by_prefix = {
        "833130": "Coconut Palm", "833210": "Wong Lo Kat", "194280": "Vita",
        "880350": "Binggrae", "834510": "Shui Lian Wan", "831831": "Shan Zha Shu Xia",
        "837410": "MASAN", "837412": "MASAN", "837520": "J WAY", "837510": "J WAY",
        "880910": "Haitai", "831390": "Ramune", "831410": "Ramune",
    }
    if refresco_product.get("brand"):
        brand = refresco_product["brand"]
    elif refresco_product["sku"].startswith("831") and refresco_product["sku"] not in brand_by_prefix:
        brand = "Chi Forest"
    elif refresco_product["sku"].startswith("832"):
        brand = "Master Kong"
    elif refresco_product["sku"].startswith("8333"):
        brand = "Taisun"
    elif refresco_product["sku"].startswith("838"):
        brand = "Dongpeng"
    elif refresco_product["sku"].startswith("8800"):
        brand = "Yogo Vera"
    elif refresco_product["sku"].startswith("8806"):
        brand = "Tomomasu"
    else:
        brand = brand_by_prefix.get(refresco_product["sku"], "Importación asiática")
    refresco_product.update(
        sort_order=sort_order,
        is_available=not refresco_product["status"].startswith("Agotado"),
        brand=brand,
    )
    apply_intl_names(refresco_product)
    apply_heat(refresco_product)
    apply_sweetness(refresco_product)
    apply_drink_facts(refresco_product)


# The featured story cards mirror catalog pricing so one product never shows two prices.
_CATALOG_BY_ID = {p["id"]: p for p in CATALOG_PRODUCTS}
for featured in PRODUCTS:
    source = _CATALOG_BY_ID.get(featured["id"])
    if source:
        for field in ("price", "price_label", "unit_price_label", "pack_label", "pack_short",
                      "units_per_case", "unit_size", "unit_noun", "inner_packs", "promo",
                      "heat_level", "heat", "heat_label", "heat_label_es", "heat_label_en",
                      "heat_label_zh", "heat_applicable", "sweetness_level", "sweetness", "sweetness_label",
                      "sweetness_label_es", "sweetness_label_en", "sweetness_label_zh",
                      "sweetness_applicable", "cook_time_applicable",
                      "kcal", "kcal_value", "kcal_estimated", "kcal_basis", "kcal_basis_es",
                      "kcal_basis_en", "kcal_basis_zh", "requires_cooking", "facts_verified",
                      "nutrition_source_url"):
            featured[field] = source[field]
        featured["weight"] = source["pack_label"]
    apply_intl_names(featured)


PRODUCT_ASSET_DIR = FRONTEND_DIR / "assets"
repository = ProductRepository()


def current_catalog() -> list[dict]:
    """Merge editable Supabase rows with the complete catalog shipped in code.

    This lets the production database continue controlling availability while
    the versioned site remains the source of truth for optimized local imagery
    and newly catalogued SKUs.
    """
    stored = repository.list_products(CATALOG_PRODUCTS)
    stored_by_sku = {str(product["sku"]): product for product in stored}
    catalog = []
    for local in CATALOG_PRODUCTS:
        product = {**local, **stored_by_sku.get(str(local["sku"]), {})}
        # Department, brand and translated copy are versioned with the site.
        for field in (
            "category", "category_label", "brand", "image", "name_es", "name_en", "name_zh",
            "description", "description_es", "description_en", "description_zh",
            "source_url", "description_verified", "heat_level", "heat", "heat_label",
            "heat_label_es", "heat_label_en", "heat_label_zh",
            "heat_applicable",
            "sweetness_level", "sweetness", "sweetness_label", "sweetness_label_es",
            "sweetness_label_en", "sweetness_label_zh", "sweetness_applicable",
            "shu", "kcal", "cook_time", "nutrition_source_url", "facts_verified",
            "facts_sources",
            "kcal_value", "kcal_estimated", "kcal_basis", "kcal_basis_es",
            "kcal_basis_en", "kcal_basis_zh", "requires_cooking", "cook_time_applicable",
        ):
            if field in local:
                product[field] = local[field]
        pack = CATALOG_PACKS.get(product["sku"])
        if pack:
            apply_pack(product, *pack)
            product["case"] = product["pack_label"]
        # Ensure the product always has an 'id' field (required by checkout)
        if "id" not in product:
            product["id"] = str(product["sku"])
        # Ensure price and is_available are always present
        if "price" not in product:
            product["price"] = 0.01
        product.setdefault("is_available", not str(product.get("status", "")).startswith("Agotado"))
        apply_intl_names(product)
        catalog.append(product)
    return catalog


def carousel_catalog(catalog_products: list[dict]) -> list[dict]:
    """Keep three Buldak packs first, soups next, bowls mid-list and chips last."""
    lead_ids = ("811120", "811140", "811150")
    product_by_id = {str(product["id"]): product for product in catalog_products}
    lead = [product_by_id[product_id] for product_id in lead_ids if product_id in product_by_id]
    lead_set = set(lead_ids)
    remainder = [product for product in catalog_products if str(product["id"]) not in lead_set]
    category_order = {
        "soups": 0, "bowls": 1, "tteokbokki": 2, "sauces": 3,
        "cookies": 4, "candy": 5, "bakery": 6, "chips": 7,
    }
    remainder.sort(
        key=lambda product: (
            category_order.get(product.get("category", ""), 4),
            product.get("sort_order", 999),
        )
    )
    return [*lead, *remainder]


@app.get("/")
def index():
    catalog_products = current_catalog()
    device_class = request_device_class()
    department_counts = {
        "noodles": sum(
            product.get("category") in {"soups", "bowls", "tteokbokki", "sauces"}
            for product in catalog_products
        ),
        "snacks": sum(
            product.get("category") in {"chips", "cookies", "candy", "bakery"}
            for product in catalog_products
        ),
        "drinks": len(REFRESCOS_PRODUCTS),
    }
    return render_template(
        "index.html",
        products=PRODUCTS,
        catalog_products=catalog_products,
        carousel_products=carousel_catalog(catalog_products),
        catalog_categories=CATALOG_CATEGORIES,
        refrescos_products=REFRESCOS_PRODUCTS,
        refrescos_categories=REFRESCOS_CATEGORIES,
        department_counts=department_counts,
        device_class=device_class,
        public_base_url=PUBLIC_BASE_URL,
    )


POLICY_PAGES = {
    "terminos": {
        "title": "Términos y condiciones",
        "description": "Condiciones aplicables al catálogo y a las solicitudes de cotización de dangoko.",
        "sections": [
            ("Naturaleza del servicio", "dangokobox.com muestra un catálogo mayorista y prepara solicitudes de cotización. El sitio no procesa pagos ni concluye por sí solo una compraventa. El pedido se formaliza cuando el vendedor confirma por escrito existencias, total, impuestos, envío, forma de pago y entrega, y el cliente acepta esas condiciones."),
            ("Precios y disponibilidad", "Los precios se muestran en pesos mexicanos por caja cerrada, salvo indicación distinta. Existencias, precios y promociones pueden cambiar antes de la confirmación final. Ningún cargo se realiza desde este sitio."),
            ("Entrega, cancelación y garantía", "La cobertura, costo y plazo estimado de entrega se informan antes del pago. Las cancelaciones, devoluciones, cambios y garantías se atienden conforme a la política publicada y a los derechos irrenunciables previstos por la legislación aplicable."),
            ("Información de productos", "Ingredientes, alérgenos, contenido, nutrición y preparación pueden variar por presentación o mercado. Debe verificarse siempre el empaque recibido. Las marcas y fotografías pertenecen a sus respectivos titulares y se usan para identificar los productos ofrecidos."),
            ("Sitio independiente", "dangoko es un proyecto independiente y no está afiliado, patrocinado, autorizado ni respaldado por Samyang Foods Co., Ltd. ni por las demás marcas mostradas."),
        ],
    },
    "privacidad": {
        "title": "Aviso de privacidad",
        "description": "Cómo se tratan los datos necesarios para preparar una cotización.",
        "sections": [
            ("Responsable", "El operador de la marca dangoko es responsable del tratamiento realizado directamente por dangokobox.com. Los datos completos de identificación y contacto disponibles se muestran al final de esta página."),
            ("Datos tratados", "El registro solicita nombre, correo y contraseña; la contraseña se almacena mediante hash y no en texto plano. Los pedidos guardan el usuario, productos, cantidades y totales necesarios para su seguimiento. El carrito y el idioma se conservan localmente en el navegador. Cloudflare Web Analytics mide de forma agregada el rendimiento de las páginas mediante datos técnicos de carga; no usa cookies, localStorage ni crea perfiles individuales. AWS y sus servicios pueden procesar temporalmente datos técnicos de infraestructura, como dirección IP, agente de usuario y registros de seguridad."),
            ("Finalidades", "El nombre, el correo, los productos y sus cantidades se utilizan para autenticar la cuenta, crear el pedido en RDS, prevenir abuso técnico y permitir su seguimiento. La medición agregada de Cloudflare se utiliza únicamente para mejorar estabilidad y velocidad. No se usan datos para publicidad comportamental ni se venden."),
            ("Transferencias y encargados", "La aplicación conserva en RDS los datos necesarios de la cuenta y del pedido. El servicio interno de notificaciones recibe el pedido únicamente después de que RDS confirma su creación. Cloudflare, AWS y los servicios de infraestructura intervienen como proveedores técnicos."),
            ("Derechos y contacto", "La persona titular puede solicitar acceso, rectificación, cancelación u oposición, así como revocar su consentimiento, mediante el contacto publicado al final. La solicitud debe identificar a la persona y describir claramente el derecho que desea ejercer."),
            ("Cambios", "Las modificaciones sustanciales a este aviso se publicarán en esta misma dirección. Última actualización: 6 de septiembre de 2026."),
        ],
    },
    "devoluciones": {
        "title": "Cancelaciones, cambios y devoluciones",
        "description": "Reglas claras para cotizaciones y pedidos confirmados.",
        "sections": [
            ("Solicitudes de cotización", "Un pedido creado en este sitio puede abandonarse o cancelarse sin costo antes de aceptar por escrito las condiciones y realizar el pago. Agregar productos al carrito no obliga a comprar."),
            ("Antes del pago", "El vendedor debe confirmar existencias, importe total, impuestos aplicables, costo y plazo de envío, forma de pago y condiciones específicas de cancelación, cambio, devolución y garantía antes de recibir el pago."),
            ("Producto incorrecto, dañado o defectuoso", "Comunícate tan pronto como sea posible por el medio de contacto publicado, conserva empaque y comprobante, e incluye fotografías cuando ayuden a identificar el problema. Según corresponda, se acordará reposición, cambio, bonificación o reembolso sin limitar los derechos reconocidos por la ley."),
            ("Alimentos y bebidas", "Por seguridad e higiene, el estado del empaque, el lote, la fecha de caducidad y la conservación del producto son relevantes para evaluar una devolución. Esto no elimina los derechos aplicables cuando el producto sea incorrecto, esté dañado, resulte impropio para consumo o no corresponda con lo ofrecido."),
            ("Derechos del consumidor", "Esta política complementa y no sustituye los derechos irrenunciables previstos en la Ley Federal de Protección al Consumidor. Cada solución y, en su caso, el plazo de reembolso se confirmarán por escrito."),
        ],
    },
    "cookies": {
        "title": "Política de cookies y almacenamiento local",
        "description": "Tecnologías utilizadas por dangokobox.com y cómo controlarlas.",
        "sections": [
            ("Sin publicidad ni perfiles", "El sitio no instala píxeles publicitarios, cookies de marketing ni herramientas para crear perfiles de comportamiento."),
            ("Medición de rendimiento", "Cloudflare Web Analytics puede inyectar un beacon de rendimiento para medir de forma agregada tiempos de carga y Core Web Vitals. Según Cloudflare, esta medición no usa cookies, localStorage ni identifica o rastrea a las personas entre sitios. Se utiliza únicamente para mejorar el funcionamiento del sitio."),
            ("Almacenamiento estrictamente funcional", "El navegador guarda localmente el contenido del carrito y el idioma elegido. Esa información permanece en el dispositivo, no identifica por sí sola a una persona y es necesaria para conservar sus preferencias entre visitas."),
            ("Proveedores externos", "AWS entrega y protege la infraestructura del sitio, RDS conserva los pedidos y S3 almacena los recibos. Google Fonts sirve la tipografía Archivo. Cada proveedor puede tratar datos técnicos conforme a sus propias políticas."),
            ("Consentimiento", "La medición de rendimiento descrita no almacena cookies ni datos en el navegador. Si en el futuro se incorporan cookies publicitarias, perfiles de comportamiento o tecnologías que requieran consentimiento, se solicitará antes de activarlas."),
            ("Cómo borrar preferencias", "El carrito y el idioma pueden eliminarse desde la configuración de datos del sitio en el navegador. Bloquear el almacenamiento local puede impedir que esas preferencias se conserven."),
        ],
    },
}


def render_policy(policy_key: str):
    policy = POLICY_PAGES[policy_key]
    return render_template(
        "policy.html",
        policy=policy,
        policy_key=policy_key,
        business=BUSINESS_INFO,
        public_base_url=PUBLIC_BASE_URL,
    )


@app.get("/terminos")
def terms_page():
    return render_policy("terminos")


@app.get("/privacidad")
def privacy_page():
    return render_policy("privacidad")


@app.get("/devoluciones")
def returns_page():
    return render_policy("devoluciones")


@app.get("/cookies")
def cookies_page():
    return render_policy("cookies")


def _current_user() -> dict | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    try:
        return database.find_user_by_id(int(user_id))
    except Exception:
        return None


@app.post("/api/auth/register")
def register():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    if not 2 <= len(name) <= 80 or "@" not in email or not 8 <= len(password) <= 128:
        return jsonify(error="Nombre, correo o contraseña no válidos."), 400
    try:
        database.init_schema()
        user = database.create_user(name, email, generate_password_hash(password))
    except Exception as error:
        if "duplicate" in str(error).lower() or "unique" in str(error).lower():
            return jsonify(error="Ese correo ya está registrado."), 409
        return jsonify(error="No se pudo crear la cuenta.", detail=type(error).__name__), 503
    session["user_id"] = user["id"]
    return jsonify(user={"id": user["id"], "name": user["name"], "email": user["email"]}), 201


@app.post("/api/auth/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email", "")).strip().lower()
    password = str(payload.get("password", ""))
    try:
        user = database.find_user(email)
    except Exception:
        return jsonify(error="La base de datos no está disponible."), 503
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify(error="Credenciales incorrectas."), 401
    session["user_id"] = user["id"]
    return jsonify(user={"id": user["id"], "name": user["name"], "email": user["email"]})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify(status="signed_out")


@app.get("/api/auth/me")
def auth_me():
    user = _current_user()
    return jsonify(authenticated=bool(user), user=user)


@app.get("/api/health")
def health():
    # Exercise the same read path as the storefront so this is a readiness
    # check, not merely a check that environment variables exist.
    current_catalog()
    catalog_ready = repository.last_source in {"supabase", "supabase-cache"}
    rds_ready = database.is_ready()
    s3_ready = storage.is_ready()
    status_code = 503 if (
        (REQUIRE_SUPABASE and not catalog_ready)
        or (REQUIRE_RDS and not rds_ready)
        or (REQUIRE_AWS and not s3_ready)
    ) else 200
    return jsonify(
        status="ok" if status_code == 200 else "degraded",
        service="dangoko",
        application="marketplace",
        database="supabase" if repository.is_configured else "local-fallback",
        catalog_source=repository.last_source,
        database_ready=rds_ready,
        s3_ready=s3_ready,
        supabase_required=REQUIRE_SUPABASE,
        rds_required=REQUIRE_RDS,
        aws_required=REQUIRE_AWS,
    ), status_code


@app.get("/salud")
def salud():
    return health()


@app.get("/api/products")
def products():
    return jsonify(products=PRODUCTS)


@app.get("/api/catalog")
def catalog():
    return jsonify(products=current_catalog(), source=repository.last_source)


@app.get("/api/refrescos")
def refrescos():
    return jsonify(products=REFRESCOS_PRODUCTS)


@app.get("/assets/<path:filename>")
def product_asset(filename: str):
    """Serve product photography through Flask in every WSGI environment."""
    return send_from_directory(PRODUCT_ASSET_DIR, filename, max_age=31536000)


@app.post("/api/checkout")
def checkout():
    origin = request.headers.get("Origin")
    # TRUSTED_HOSTS validates request.host. Matching Origin to that validated
    # host keeps previews functional without accepting cross-site submissions.
    if origin and urlparse(origin).netloc.lower() != request.host.lower():
        return jsonify(error="Origen de solicitud no permitido."), 403

    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(error="La solicitud no contiene JSON válido."), 400

    customer = payload.get("customer")
    cart = payload.get("cart")
    if not isinstance(customer, dict):
        return jsonify(error="Los datos del cliente no son válidos."), 400

    name = str(customer.get("name", "")).strip()
    if not 1 <= len(name) <= 80:
        return jsonify(error="Ingresa un nombre válido."), 400
    if customer.get("privacy_consent") is not True:
        return jsonify(error="Debes aceptar el aviso de privacidad para continuar."), 400
    if not isinstance(cart, list) or not cart or len(cart) > 50:
        return jsonify(error="Tu carrito está vacío."), 400
    catalog_by_id = {product["id"]: product for product in [*current_catalog(), *REFRESCOS_PRODUCTS]}
    total = Decimal("0")
    normalized_cart = []
    seen_ids = set()
    for item in cart:
        if not isinstance(item, dict):
            return jsonify(error="Uno de los artículos del carrito no es válido."), 400
        product_id = str(item.get("id", ""))
        quantity = item.get("quantity")
        product = catalog_by_id.get(product_id)
        if (
            product is None
            or isinstance(quantity, bool)
            or not isinstance(quantity, int)
            or quantity < 1
            or quantity > 20
            or product_id in seen_ids
            or not product.get("is_available", True)
        ):
            return jsonify(error="Uno de los artículos del carrito no es válido."), 400
        seen_ids.add(product_id)
        total += Decimal(str(product["price"])) * quantity
        normalized_cart.append({"id": product["id"], "quantity": quantity})

    shipping = Decimal("0")
    order_id = f"BDK-{token_hex(5).upper()}"
    authenticated_user = _current_user()
    customer_email = str(customer.get("email", "")).strip() or (
        authenticated_user["email"] if authenticated_user else None
    )
    order_uuid = str(uuid4())
    order_items = [
        {
            "product_id": item["id"],
            "quantity": item["quantity"],
            "unit_price": str(catalog_by_id[item["id"]]["price"]),
        }
        for item in normalized_cart
    ]
    receipt = {
        "id": order_uuid,
        "public_order_id": order_id,
        "customer_name": name,
        "customer_email": customer_email,
        "subtotal": f"{total:.2f}",
        "shipping": f"{shipping:.2f}",
        "total": f"{total + shipping:.2f}",
        "items": order_items,
    }
    s3_key = None
    try:
        s3_key = storage.put_order_receipt(receipt, order_items)
    except Exception as error:
        if REQUIRE_AWS:
            return jsonify(error="No se pudo guardar el recibo privado en S3.", detail=type(error).__name__), 503
    try:
        database.init_schema()
        database.create_order(
            order_uuid,
            authenticated_user["id"] if authenticated_user else None,
            name,
            receipt["customer_email"],
            receipt["subtotal"],
            receipt["shipping"],
            receipt["total"],
            order_items,
            s3_key,
        )
    except Exception as error:
        # Never notify or present a successful checkout when the durable order
        # record was not created. Notifications are downstream of RDS.
        return jsonify(error="No se pudo guardar el pedido en RDS.", detail=type(error).__name__), 503
    notification_status = "fallback"
    try:
        notification = requests.post(
            f"{NOTIFICATIONS_URL}/notifications/order",
            json={
                "order_id": order_id,
                "customer_name": name,
                "email": receipt["customer_email"],
            },
            timeout=3,
        )
        notification.raise_for_status()
        notification_status = notification.json().get("status", "sent")
    except (requests.RequestException, ValueError):
        if os.getenv("REQUIRE_NOTIFICATIONS", "false").lower() in {"1", "true", "yes", "on"}:
            return jsonify(error="El servicio de notificaciones no está disponible."), 503
    return jsonify(
        status="confirmed",
        order_id=order_id,
        user_id=authenticated_user["id"] if authenticated_user else None,
        items=normalized_cart,
        subtotal=f"{total:.2f}",
        shipping=f"{shipping:.2f}",
        total=f"{total + shipping:.2f}",
        notification_status=notification_status,
        receipt_key=s3_key,
    )


@app.after_request
def add_response_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    forwarded_proto = request.headers.get("X-Forwarded-Proto", "").split(",", 1)[0].strip()
    is_https = request.is_secure or forwarded_proto == "https"
    if is_https:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if response.mimetype == "text/html":
        # upgrade-insecure-requests only makes sense when already on HTTPS;
        # on plain HTTP it causes the browser to upgrade sub-resource requests
        # to HTTPS, which fails and breaks all CSS/JS/image loading.
        csp_upgrade = "upgrade-insecure-requests; " if is_https else ""
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "base-uri 'none'; "
            "connect-src 'self'; "
            "font-src 'self' https://fonts.gstatic.com; "
            "form-action 'self'; "
            "frame-ancestors 'none'; "
            "img-src 'self' data:; "
            "manifest-src 'self'; "
            "media-src 'self'; "
            "object-src 'none'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            + csp_upgrade +
            "worker-src 'self'"
        )
        response.headers["Accept-CH"] = "Sec-CH-UA-Mobile"
        response.headers["X-Render-Device"] = request_device_class()
        response.vary.add("Sec-CH-UA-Mobile")
        response.vary.add("User-Agent")
    if request.path.startswith(("/assets/", "/css/", "/js/")):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif request.path in {"/api/catalog", "/api/products", "/api/refrescos"}:
        response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    elif request.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.errorhandler(413)
def request_too_large(_error):
    if request.path.startswith("/api/"):
        return jsonify(error="La solicitud excede el tamaño permitido."), 413
    return "Solicitud demasiado grande.", 413


if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )
