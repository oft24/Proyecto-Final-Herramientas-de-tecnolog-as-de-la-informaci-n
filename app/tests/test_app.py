import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from app import app
from backend.app import CATALOG_PRODUCTS, REFRESCOS_PRODUCTS
from backend.supabase_repository import ProductRepository


class ShowroomTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.db_init = patch("backend.app.database.init_schema").start()
        self.db_create_order = patch("backend.app.database.create_order").start()
        self.notification_post = patch("backend.app.requests.post").start()
        self.notification_post.return_value.json.return_value = {"status": "sent"}
        self.addCleanup(patch.stopall)

    def test_homepage_renders(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"dangoko", response.data)
        self.assertIn(b"811140", response.data)
        self.assertIn(b"811920", response.data)
        self.assertIn(b"Todos los productos", response.data)
        self.assertIn(b"$1,120", response.data)
        self.assertNotIn(b"$0.01", response.data)
        self.assertNotIn(b"Ll\xc3\xa9vate Original", response.data)
        self.assertNotIn(b"Solo Original", response.data)
        self.assertNotIn(b"Lo que define", response.data)
        self.assertNotIn(b"Una bolsa", response.data)
        self.assertNotIn(b"Toda su ficha", response.data)
        self.assertNotIn(b"Referencia visual", response.data)
        self.assertNotIn(b"Referencia ", response.data)
        self.assertIn(b'data-language', response.data)
        self.assertIn(b'css/style.css?v=43', response.data)
        self.assertIn(b'js/device.js?v=1', response.data)
        self.assertIn(b'js/i18n.js?v=20', response.data)
        self.assertIn(b'js/app.js?v=47', response.data)
        self.assertIn(b'/assets/mobile-catalog/811140.webp?v=1', response.data)
        self.assertIn(b'data-carousel-srcset="/assets/mobile-catalog/', response.data)
        self.assertIn(b'data-server-device="desktop"', response.data)
        self.assertEqual(response.headers["X-Render-Device"], "desktop")
        self.assertIn("Sec-CH-UA-Mobile", response.headers["Accept-CH"])
        self.assertIn(b'rel="preload" as="image" href="/assets/carbonara.webp?v=4"', response.data)
        self.assertIn(b'data-carousel-src=', response.data)
        self.assertEqual(response.data.count(b'data-deferred-src='), 154)
        self.assertIn(b'data-catalog-name="811140"', response.data)
        self.assertIn(b'data-catalog-image="811920"', response.data)
        self.assertIn(b'data-catalog-name="634210"', response.data)
        self.assertIn(b'data-catalog-name="802150"', response.data)
        self.assertNotIn(b'id="brands"', response.data)
        self.assertNotIn(b'href="#brands"', response.data)
        self.assertIn(b'data-department-filter="noodles"', response.data)
        self.assertIn(b'data-department-filter="snacks"', response.data)
        self.assertEqual(response.data.count(b'data-catalog-detail="'), 83)
        self.assertEqual(response.data.count(b'data-catalog-quantity="'), 83)
        self.assertEqual(response.data.count(b'data-catalog-heat="'), 44)
        self.assertNotIn(b'data-catalog-heat="061020"', response.data)
        self.assertIn(b'data-catalog-sweetness="061020"', response.data)
        self.assertGreater(response.data.count(b'data-catalog-sweetness="'), 32)
        self.assertEqual(response.data.count(b'data-refresco-catalog-sweetness="'), 71)
        self.assertEqual(response.data.count(b'data-catalog-calories="'), 83)
        self.assertEqual(response.data.count(b'data-refresco-catalog-calories="'), 71)
        self.assertEqual(response.data.count(b'data-refresco-catalog-description="'), 71)
        self.assertIn(b'data-refresco-detail-panel', response.data)
        self.assertIn(b'data-refresco-story', response.data)
        self.assertIn(b'id="refresco-story"', response.data)
        self.assertIn(b'data-refresco-story-description', response.data)
        self.assertIn(b'data-i18n="refrescos.detailIndex"', response.data)
        self.assertIn(b'data-catalog-sweetness="811320"', response.data)
        self.assertIn(b'data-catalog-sweetness="807810"', response.data)
        self.assertEqual(response.data.count(b'data-card="'), 83)
        self.assertEqual(response.data.count(b'data-select="'), 83)
        self.assertEqual(response.data.count(b'data-card-product="'), 83)
        self.assertEqual(response.data.count(b'data-select-product="'), 83)
        self.assertEqual(response.data.count(b'data-search-product="'), 0)
        self.assertIn(b'data-search-results', response.data)
        self.assertEqual(response.data.count(b'data-catalog-spice="'), 37)
        self.assertIn(b'data-catalog-spice="811130"', response.data)
        self.assertIn(b'data-catalog-spice="634280"', response.data)
        self.assertEqual(response.data.count(b'/assets/refrescos/cutouts/'), 72)
        self.assertEqual(response.data.count(b'/assets/mobile-catalog/'), 240)
        self.assertLess(response.data.index(b'data-card-product="811120"'), response.data.index(b'data-card-product="811140"'))
        self.assertLess(response.data.index(b'data-card-product="811140"'), response.data.index(b'data-card-product="811150"'))
        self.assertLess(response.data.index(b'data-card-product="811650"'), response.data.index(b'data-card-product="811910"'))
        self.assertIn(b'data-clear-cart', response.data)
        self.assertIn(b'data-auth-dialog', response.data)
        self.assertIn(b'data-auth-form', response.data)
        self.assertIn(b'Crear pedido', response.data)
        self.assertIn(b'data-story-section', response.data)
        self.assertIn(b'data-story-sweetness-stat', response.data)
        self.assertIn(b'data-story-kcal-basis', response.data)
        self.assertIn(b'Tu carrito', response.data)
        self.assertIn(b"T\xc3\xa9rminos y condiciones", response.data)
        self.assertIn(b'href="/privacidad"', response.data)
        self.assertIn(b'href="/devoluciones"', response.data)
        self.assertIn(b'href="/cookies"', response.data)
        self.assertIn(b'name="privacy_consent"', response.data)
        self.assertIn(b'name="email"', response.data)
        self.assertIn(b"prepared-carbonara.jpg?v=3", response.data)
        favicon = self.client.get("/assets/favicon.svg")
        try:
            self.assertEqual(favicon.status_code, 200)
        finally:
            favicon.close()

    def test_health_endpoint(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")
        self.assertEqual(response.get_json()["service"], "dangoko")
        self.assertIn("database_ready", response.get_json())
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_policy_pages_are_standalone_and_accessible(self):
        expected = {
            "/terminos": b"T\xc3\xa9rminos y condiciones",
            "/privacidad": b"Aviso de privacidad",
            "/devoluciones": b"Cancelaciones, cambios y devoluciones",
            "/cookies": b"Pol\xc3\xadtica de cookies y almacenamiento local",
        }
        for path, title in expected.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertIn(title, response.data)
                self.assertIn(b'href="#policy-content"', response.data)
                self.assertIn(b'aria-label="Pol\xc3\xadticas de dangoko"', response.data)
                self.assertIn(b'css/style.css?v=43', response.data)
                self.assertIn(b"+52 55 2972 3373", response.data)

        cookies = self.client.get("/cookies")
        self.assertIn(b"Cloudflare Web Analytics", cookies.data)
        self.assertIn(b"no usa cookies", cookies.data)

    def test_checkout_requires_explicit_privacy_consent(self):
        response = self.client.post(
            "/api/checkout",
            json={
                "customer": {"name": "Test Customer"},
                "cart": [{"id": "811140", "quantity": 1}],
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("privacidad", response.get_json()["error"])

    def test_production_health_fails_when_supabase_is_unavailable(self):
        with (
            patch("backend.app.REQUIRE_SUPABASE", True),
            patch("backend.app.repository.list_products", return_value=CATALOG_PRODUCTS),
            patch("backend.app.repository.last_source", "local-fallback"),
        ):
            response = self.client.get("/api/health")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.get_json()["status"], "degraded")
        self.assertFalse(response.get_json()["database_ready"])

    def test_production_security_headers_and_trusted_hosts(self):
        response = self.client.get("/", headers={"X-Forwarded-Proto": "https"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["Cross-Origin-Opener-Policy"], "same-origin-allow-popups")
        self.assertIn("max-age=31536000", response.headers["Strict-Transport-Security"])
        csp = response.headers["Content-Security-Policy"]
        self.assertIn("script-src 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertNotIn("script-src 'self' 'unsafe-inline'", csp)

        rejected = self.client.get("/", headers={"Host": "evil.example"})
        self.assertEqual(rejected.status_code, 400)

        preview = self.client.post(
            "/api/checkout",
            base_url="https://preview.vercel.app",
            headers={"Origin": "https://preview.vercel.app"},
            json={
                "customer": {"name": "Test", "privacy_consent": True},
                "cart": [{"id": "811140", "quantity": 1}],
            },
        )
        self.assertEqual(preview.status_code, 200)

    def test_checkout_rejects_malformed_and_cross_origin_requests(self):
        malformed_item = self.client.post(
            "/api/checkout",
            json={
                "customer": {"name": "Test", "privacy_consent": True},
                "cart": ["not-an-object"],
            },
        )
        self.assertEqual(malformed_item.status_code, 400)

        duplicate = self.client.post(
            "/api/checkout",
            json={
                "customer": {"name": "Test", "privacy_consent": True},
                "cart": [
                    {"id": "811140", "quantity": 1},
                    {"id": "811140", "quantity": 1},
                ],
            },
        )
        self.assertEqual(duplicate.status_code, 400)

        cross_origin = self.client.post(
            "/api/checkout",
            headers={"Origin": "https://evil.example"},
            json={
                "customer": {"name": "Test", "privacy_consent": True},
                "cart": [{"id": "811140", "quantity": 1}],
            },
        )
        self.assertEqual(cross_origin.status_code, 403)

    def test_checkout_request_size_is_limited(self):
        response = self.client.post(
            "/api/checkout",
            json={
                "customer": {"name": "x" * 20_000, "privacy_consent": True},
                "cart": [{"id": "811140", "quantity": 1}],
            },
        )
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.content_type, "application/json")

    def test_first_render_detects_phone_from_user_agent(self):
        response = self.client.get(
            "/",
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"
                )
            },
        )
        self.assertEqual(response.headers["X-Render-Device"], "mobile")
        self.assertIn(b'class="is-mobile-device"', response.data)
        self.assertIn(b'data-server-device="mobile"', response.data)

    def test_client_hint_detects_mobile_with_desktop_user_agent(self):
        response = self.client.get(
            "/",
            headers={"User-Agent": "Mozilla/5.0", "Sec-CH-UA-Mobile": "?1"},
        )
        self.assertEqual(response.headers["X-Render-Device"], "mobile")
        self.assertIn(b'data-device="mobile"', response.data)

    def test_first_render_keeps_tablet_separate_from_phone(self):
        response = self.client.get(
            "/",
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 14; Pixel Tablet) "
                    "AppleWebKit/537.36 Chrome/128.0 Safari/537.36"
                )
            },
        )
        self.assertEqual(response.headers["X-Render-Device"], "tablet")
        self.assertIn(b'class="" data-server-device="tablet"', response.data)

    def test_invalid_supabase_configuration_uses_local_fallback(self):
        fallback = [{"sku": "local-product"}]
        with patch.dict(
            "os.environ",
            {
                "NEXT_PUBLIC_SUPABASE_URL": "[SENSITIVE]",
                "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY": "[SENSITIVE]",
            },
        ):
            repository = ProductRepository()

        self.assertFalse(repository.is_configured)
        self.assertEqual(repository.list_products(fallback), fallback)
        self.assertEqual(repository.last_source, "local-fallback")

    def test_checkout_does_not_open_whatsapp_automatically(self):
        response = self.client.get("/js/app.js")
        try:
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b"window.open(\"\", \"buldakshop-whatsapp\")", response.data)
            self.assertNotIn(b"https://wa.me/", response.data)
            self.assertIn(b"/api/auth/register", response.data)
            self.assertIn(b"/api/auth/login", response.data)
        finally:
            response.close()

    def test_products_have_complete_selected_flavor_content(self):
        response = self.client.get("/api/products")
        self.assertEqual(response.status_code, 200)
        for product in response.get_json()["products"]:
            self.assertEqual(len(product["directions"]), 4)
            self.assertEqual(len(product["recommendations"]), 3)
            self.assertTrue(product["prepared_image"].startswith("/assets/prepared-"))
            self.assertGreater(product["price"], 1)
            self.assertTrue(product["price_label"].startswith("$"))

    def test_all_legacy_buldak_descriptions_have_three_localized_profiles(self):
        i18n_path = Path(__file__).resolve().parents[1] / "frontend" / "static" / "js" / "i18n.js"
        i18n_source = i18n_path.read_text(encoding="utf-8")
        profile_skus = [
            item["sku"] for item in CATALOG_PRODUCTS
            if "disponible por caja cerrada" in item["description_es"].lower()
        ]
        self.assertEqual(len(profile_skus), 22)
        for sku in profile_skus:
            self.assertGreaterEqual(i18n_source.count(f'"{sku}": {{'), 3, sku)

    def test_catalog_has_all_references_and_images(self):
        response = self.client.get("/api/catalog")
        self.assertEqual(response.status_code, 200)
        catalog = response.get_json()["products"]
        self.assertEqual(len(catalog), 83)
        self.assertEqual({item["sku"] for item in catalog}.__len__(), 83)
        self.assertIn("Agotado", next(item["status"] for item in catalog if item["sku"] == "811720"))
        self.assertEqual(next(item["brand"] for item in catalog if item["sku"] == "634210"), "Master Kong")
        self.assertEqual(next(item["category"] for item in catalog if item["sku"] == "802150"), "chips")
        self.assertEqual(next(item["category"] for item in catalog if item["sku"] == "807331"), "cookies")
        self.assertEqual(next(item["category"] for item in catalog if item["sku"] == "851120"), "candy")
        self.assertEqual(next(item["category"] for item in catalog if item["sku"] == "061010"), "bakery")
        cheese = next(item for item in catalog if item["sku"] == "811200")
        self.assertEqual(cheese["shu"], "2,323")
        self.assertEqual(cheese["kcal"], "550")
        self.assertEqual(cheese["cook_time"], "5 min")
        self.assertTrue(cheese["facts_verified"])
        self.assertEqual(len(cheese["facts_sources"]), 3)
        for item in catalog:
            self.assertGreater(item["price"], 1, item["sku"])
            self.assertTrue(item["price_label"].startswith("$"), item["sku"])
            self.assertGreaterEqual(item["units_per_case"], 1, item["sku"])
            self.assertIn(" de ", item["pack_label"], item["sku"])
            self.assertTrue(item["image"].startswith("/assets/"), item["sku"])
            self.assertTrue(item["source_url"].startswith("https://"), item["sku"])
            self.assertNotIn("google.com/search", item["source_url"], item["sku"])
            self.assertTrue(item["description_verified"], item["sku"])
            self.assertIn(item["heat_level"], range(6), item["sku"])
            self.assertEqual(item["heat"], item["heat_level"] * 20, item["sku"])
            self.assertEqual(item["heat_applicable"], item["heat_level"] > 0, item["sku"])
            self.assertTrue(item["heat_label_es"].endswith("/5"), item["sku"])
            self.assertTrue(item["heat_label_en"].endswith("/5"), item["sku"])
            self.assertTrue(item["heat_label_zh"].endswith("/5"), item["sku"])
            self.assertIn(item["sweetness_level"], range(6), item["sku"])
            self.assertEqual(item["sweetness"], item["sweetness_level"] * 20, item["sku"])
            self.assertEqual(item["sweetness_applicable"], item["sweetness_level"] > 0, item["sku"])
            if item["sweetness_level"]:
                self.assertTrue(item["sweetness_label_es"].endswith("/5"), item["sku"])
                self.assertTrue(item["sweetness_label_en"].endswith("/5"), item["sku"])
                self.assertTrue(item["sweetness_label_zh"].endswith("/5"), item["sku"])
            self.assertTrue(item["name_es"], item["sku"])
            self.assertTrue(item["name_en"], item["sku"])
            self.assertTrue(item["name_zh"], item["sku"])
            self.assertTrue(item["description_es"], item["sku"])
            self.assertTrue(item["description_en"], item["sku"])
            self.assertTrue(item["description_zh"], item["sku"])
            self.assertTrue(item["brand"], item["sku"])
            self.assertTrue(item["unit_size"], item["sku"])
            self.assertTrue(item["unit_noun"], item["sku"])
            self.assertTrue(item["kcal"], item["sku"])
            self.assertGreaterEqual(item["kcal_value"], 0, item["sku"])
            self.assertIsInstance(item["kcal_estimated"], bool, item["sku"])
            self.assertTrue(item["kcal_basis_es"], item["sku"])
            self.assertTrue(item["kcal_basis_en"], item["sku"])
            self.assertTrue(item["kcal_basis_zh"], item["sku"])
            self.assertTrue(item["nutrition_source_url"].startswith("https://"), item["sku"])
            self.assertEqual(item["cook_time_applicable"], item["requires_cooking"], item["sku"])
            if item["cook_time_applicable"]:
                self.assertTrue(item["cook_time"], item["sku"])
            image_response = self.client.get(item["image"].split("?")[0])
            try:
                self.assertEqual(image_response.status_code, 200, item["sku"])
                self.assertGreater(len(image_response.get_data()), 1000, item["sku"])
            finally:
                image_response.close()

        spicy_items = [
            item for item in catalog
            if item["category"] in {"soups", "bowls", "tteokbokki"}
        ]
        self.assertEqual(len(spicy_items), 37)
        for item in spicy_items:
            self.assertIn(item["spice_level"], range(1, 6), item["sku"])

        ranli_cake = next(item for item in catalog if item["sku"] == "061020")
        self.assertEqual(ranli_cake["heat_level"], 0)
        self.assertEqual(ranli_cake["sweetness_level"], 3)
        self.assertEqual(ranli_cake["kcal"], "≈380")
        self.assertEqual(ranli_cake["kcal_basis_es"], "por 100 g")
        self.assertFalse(ranli_cake["requires_cooking"])
        self.assertFalse(ranli_cake["heat_applicable"])
        self.assertTrue(ranli_cake["sweetness_applicable"])

    def test_checkout_accepts_catalog_products_at_case_price(self):
        invalid = self.client.post("/api/checkout", json={"cart": []})
        self.assertEqual(invalid.status_code, 400)

        valid = self.client.post(
            "/api/checkout",
            json={
                "customer": {"name": "Test Customer", "privacy_consent": True},
                "cart": [
                    {"id": "811140", "quantity": 2},
                    {"id": "811120", "quantity": 3},
                ],
            },
        )
        payload = valid.get_json()
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(len(payload["items"]), 2)
        # 811140 and 811120 are both $1,120 per case: 2 + 3 cases = $5,600.
        self.assertEqual(payload["subtotal"], "5600.00")
        self.assertEqual(payload["shipping"], "0.00")
        self.assertEqual(payload["total"], "5600.00")

    def test_checkout_accepts_new_noodle_and_chip_products(self):
        response = self.client.post(
            "/api/checkout",
            json={
                "customer": {"name": "Test Customer", "privacy_consent": True},
                "cart": [
                    {"id": "634210", "quantity": 1},
                    {"id": "802150", "quantity": 2},
                ],
            },
        )
        payload = response.get_json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(payload["items"]), 2)
        self.assertEqual(payload["subtotal"], "2331.00")
        self.assertEqual(payload["total"], "2331.00")

    def test_refrescos_catalog_is_wholesale_with_real_photos(self):
        response = self.client.get("/api/refrescos")
        self.assertEqual(response.status_code, 200)
        drinks = response.get_json()["products"]
        self.assertEqual(len(drinks), 71)
        self.assertEqual(len({item["sku"] for item in drinks}), 71)
        self.assertEqual(next(item["name_zh"] for item in drinks if item["sku"] == "832120"), "康师傅冰红茶")
        self.assertEqual(next(item["brand"] for item in drinks if item["sku"] == "837110"), "Red Bull")
        for item in drinks:
            self.assertEqual(item["heat_level"], 0, item["sku"])
            self.assertFalse(item["heat_applicable"], item["sku"])
            self.assertIn(item["sweetness_level"], range(1, 6), item["sku"])
            self.assertEqual(item["sweetness"], item["sweetness_level"] * 20, item["sku"])
            self.assertTrue(item["sweetness_label_es"].endswith("/5"), item["sku"])
            self.assertTrue(item["sweetness_label_en"].endswith("/5"), item["sku"])
            self.assertTrue(item["sweetness_label_zh"].endswith("/5"), item["sku"])
            self.assertTrue(item["image"].startswith("/assets/refrescos/"), item["sku"])
            self.assertIn(item["sku"], item["image"])
            self.assertGreater(item["price"], 1, item["sku"])
            self.assertGreaterEqual(item["units_per_case"], 8, item["sku"])
            self.assertIn(" de ", item["pack_label"], item["sku"])
            self.assertTrue(item["name_es"], item["sku"])
            self.assertTrue(item["name_en"], item["sku"])
            self.assertTrue(item["name_zh"], item["sku"])
            self.assertTrue(item["description_es"], item["sku"])
            self.assertTrue(item["description_en"], item["sku"])
            self.assertTrue(item["description_zh"], item["sku"])
            self.assertTrue(item["brand"], item["sku"])
            self.assertTrue(item["unit_size"], item["sku"])
            self.assertTrue(item["unit_noun"], item["sku"])
            self.assertTrue(item["kcal"], item["sku"])
            self.assertTrue(item["kcal"].startswith("≈"), item["sku"])
            self.assertGreaterEqual(item["kcal_value"], 0, item["sku"])
            self.assertTrue(item["kcal_estimated"], item["sku"])
            self.assertTrue(item["kcal_basis_es"], item["sku"])
            self.assertTrue(item["kcal_basis_en"], item["sku"])
            self.assertTrue(item["kcal_basis_zh"], item["sku"])
            self.assertTrue(item["nutrition_source_url"].startswith("https://"), item["sku"])
            self.assertFalse(item["requires_cooking"], item["sku"])
            self.assertFalse(item["cook_time_applicable"], item["sku"])
            image_response = self.client.get(item["image"].split("?")[0])
            try:
                self.assertEqual(image_response.status_code, 200, item["sku"])
                self.assertGreater(len(image_response.get_data()), 4000, item["sku"])
            finally:
                image_response.close()
            cutout_path = item["image"].split("?")[0].replace("/refrescos/", "/refrescos/cutouts/")
            cutout_response = self.client.get(cutout_path)
            try:
                self.assertEqual(cutout_response.status_code, 200, item["sku"])
                self.assertGreater(len(cutout_response.get_data()), 4000, item["sku"])
            finally:
                cutout_response.close()

    def test_all_refresco_assets_are_hd_and_cutouts_are_transparent(self):
        asset_root = Path(__file__).resolve().parents[1] / "frontend" / "assets" / "refrescos"
        originals = sorted(asset_root.glob("*.webp"))
        cutouts = sorted((asset_root / "cutouts").glob("*.webp"))
        self.assertEqual(len(originals), 71)
        self.assertEqual({path.name for path in originals}, {path.name for path in cutouts})

        for original_path in originals:
            with Image.open(original_path) as original:
                original.verify()
            with Image.open(original_path) as original:
                self.assertEqual(original.size, (1600, 1600), original_path.name)

            with Image.open(asset_root / "cutouts" / original_path.name) as cutout:
                cutout.verify()
            with Image.open(asset_root / "cutouts" / original_path.name) as cutout:
                self.assertIn("A", cutout.getbands(), original_path.name)
                self.assertGreaterEqual(max(cutout.size), 1000, original_path.name)

    def test_mobile_catalog_assets_are_complete_and_lightweight(self):
        asset_root = Path(__file__).resolve().parents[1] / "frontend" / "assets" / "mobile-catalog"
        images = sorted(asset_root.glob("*.webp"))
        expected_names = {f"{item['sku']}.webp" for item in [*CATALOG_PRODUCTS, *REFRESCOS_PRODUCTS]}
        self.assertEqual({path.name for path in images}, expected_names)
        self.assertEqual(len(images), 154)

        for image_path in images:
            self.assertLess(image_path.stat().st_size, 100 * 1024, image_path.name)
            with Image.open(image_path) as image:
                image.verify()
            with Image.open(image_path) as image:
                self.assertLessEqual(max(image.size), 640, image_path.name)

    def test_phone_catalog_uses_compact_two_column_layout(self):
        css_path = Path(__file__).resolve().parents[1] / "frontend" / "static" / "css" / "style.css"
        css = css_path.read_text(encoding="utf-8")
        js_path = Path(__file__).resolve().parents[1] / "frontend" / "static" / "js" / "app.js"
        js = js_path.read_text(encoding="utf-8")
        phone_rules = css[css.index("@media (max-width: 600px)") : css.index("@media (max-width: 380px)")]
        self.assertIn("@media (max-width: 960px)", css)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr))", phone_rules)
        self.assertIn(".catalog-card.reveal { opacity: 1; transform: none; transition: none; }", phone_rules)
        self.assertIn(".catalog-card__body > .intl-names { display: none; }", phone_rules)
        self.assertIn("content-visibility: auto", css)
        self.assertIn('window.matchMedia("(max-width: 960px)")', js)
        self.assertIn('window.addEventListener("orientationchange", handleViewportChange', js)
        self.assertIn("documentOffsetTop(target) - headerOffset - 20", js)
        self.assertIn(".hero-copy > .specs { display: none; }", phone_rules)
        self.assertIn(".refrescos-info > [data-refresco-description]", phone_rules)
        self.assertIn(".refresco-story__stats { display: grid", phone_rules)

    def test_desktop_carousels_use_compositor_friendly_animation(self):
        js_path = Path(__file__).resolve().parents[1] / "frontend" / "static" / "js" / "app.js"
        css_path = Path(__file__).resolve().parents[1] / "frontend" / "static" / "css" / "style.css"
        js = js_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")
        self.assertNotIn("card.style.filter =", js)
        self.assertIn("Math.pow(CAROUSEL_DAMPING, stepScale)", js)
        self.assertIn("[-1, 0, 1].map", js)
        self.assertIn('classList.add("is-rendered")', js)
        self.assertIn("will-change: transform, opacity;", css)
        self.assertNotIn("will-change: transform, opacity, filter", css)

    def test_product_theme_changes_in_the_selection_frame(self):
        js_path = Path(__file__).resolve().parents[1] / "frontend" / "static" / "js" / "app.js"
        css_path = Path(__file__).resolve().parents[1] / "frontend" / "static" / "css" / "style.css"
        js = js_path.read_text(encoding="utf-8")
        css = css_path.read_text(encoding="utf-8")
        set_theme = js[js.index("function setTheme(") : js.index("function goTo(")]
        image_activation = js[
            js.index("function activateCarouselImage(") : js.index("const deferredImages")
        ]

        self.assertIn("preloadCarouselWindow(dom.cards, index);", set_theme)
        self.assertIn("applyCarouselTheme(theme);", set_theme)
        self.assertNotIn("pendingCarouselTheme", js)
        self.assertIn('card?.querySelector("img")', image_activation)
        self.assertIn("image.fetchPriority = priority;", image_activation)
        self.assertIn('source[data-carousel-srcset]', image_activation)
        self.assertIn("function advanceCarouselMotion", js)
        self.assertIn("CAROUSEL_STIFFNESS = 0.24", js)
        self.assertIn("CAROUSEL_MAX_ANIMATED_DISTANCE = 2", js)
        self.assertIn("@property --bg-a", css)
        self.assertIn("--theme-transition: 360ms;", css)
        self.assertIn("--bg-a var(--theme-transition) var(--ease)", css)
        self.assertNotIn("transition: background ", css)

    def test_checkout_rejects_sold_out_product(self):
        response = self.client.post(
            "/api/checkout",
            json={
                "customer": {"name": "Test Customer", "privacy_consent": True},
                "cart": [{"id": "811720", "quantity": 1}],
            },
        )
        self.assertEqual(response.status_code, 400)


class DatabaseCreateOrderTests(unittest.TestCase):
    """Verify that create_order uses cursor.executemany (psycopg3 compatible)."""

    def test_create_order_uses_cursor_executemany(self):
        """
        conn.executemany does not exist in psycopg3.
        create_order must use conn.cursor().executemany instead.
        This test mocks the connection and verifies the correct path is taken.
        """
        from unittest.mock import MagicMock, patch, call
        from backend import database

        mock_cursor = MagicMock()
        mock_conn = MagicMock()
        # Make cursor() return a context-manager that yields mock_cursor
        mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
        # Remove executemany from conn to ensure it is NOT called on the connection
        del mock_conn.executemany

        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=mock_conn)
        mock_ctx.__exit__ = MagicMock(return_value=False)

        with patch("backend.database.connection", return_value=mock_ctx):
            database.create_order(
                order_id="test-uuid-001",
                user_id=1,
                customer_name="Test",
                customer_email="test@example.com",
                subtotal="1120.00",
                shipping="0.00",
                total="1120.00",
                items=[
                    {"product_id": "811140", "quantity": 1, "unit_price": "1120.00"}
                ],
                s3_key="orders/test.json",
            )

        # The order header must be inserted via conn.execute
        mock_conn.execute.assert_called_once()

        # The order items must be inserted via cursor.executemany, NOT conn.executemany
        mock_cursor.executemany.assert_called_once()
        args = mock_cursor.executemany.call_args[0]
        self.assertIn("order_items", args[0])
        self.assertEqual(args[1][0][0], "test-uuid-001")  # order_id
        self.assertEqual(args[1][0][1], "811140")          # product_id


if __name__ == "__main__":
    unittest.main()
