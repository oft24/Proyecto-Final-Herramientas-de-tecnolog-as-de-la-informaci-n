from __future__ import annotations

import json
import logging
import math
import os
from threading import Lock
import time
from copy import deepcopy
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class ProductRepository:
    """Small Supabase REST adapter with a safe local catalog fallback."""

    def __init__(self, cache_seconds: int = 60, failure_cache_seconds: int = 15) -> None:
        self.url = (
            os.getenv("SUPABASE_URL")
            or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
            or ""
        ).rstrip("/")
        self.key = (
            os.getenv("SUPABASE_PUBLISHABLE_KEY")
            or os.getenv("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY")
            or ""
        )
        self.cache_seconds = cache_seconds
        self.failure_cache_seconds = failure_cache_seconds
        self._cache: list[dict] = []
        self._cached_at = 0.0
        self._retry_after = 0.0
        self._lock = Lock()
        self.last_source = "not-loaded"
        self.last_error = ""

    @property
    def is_configured(self) -> bool:
        parsed_url = urlparse(self.url)
        return bool(
            self.key
            and parsed_url.scheme in {"http", "https"}
            and parsed_url.netloc
        )

    def list_products(self, fallback: list[dict]) -> list[dict]:
        now = time.monotonic()
        if self._cache and now - self._cached_at < self.cache_seconds:
            self.last_source = "supabase-cache"
            return deepcopy(self._cache)

        if not self.is_configured:
            self.last_source = "local-fallback"
            return deepcopy(fallback)

        if now < self._retry_after:
            self.last_source = "supabase-stale" if self._cache else "local-fallback"
            return deepcopy(self._cache or fallback)

        # Gunicorn runs multiple threads per worker. Serializing refreshes avoids
        # a burst of identical upstream requests when the cache expires.
        with self._lock:
            now = time.monotonic()
            if self._cache and now - self._cached_at < self.cache_seconds:
                self.last_source = "supabase-cache"
                return deepcopy(self._cache)
            if now < self._retry_after:
                self.last_source = "supabase-stale" if self._cache else "local-fallback"
                return deepcopy(self._cache or fallback)

            try:
                query = urlencode({"select": "*", "order": "sort_order.asc"})
                request = Request(
                    f"{self.url}/rest/v1/products?{query}",
                    headers={
                        "apikey": self.key,
                        "Authorization": f"Bearer {self.key}",
                        "Accept": "application/json",
                    },
                )
                with urlopen(request, timeout=4) as response:
                    raw_response = response.read(2_000_001)
                if len(raw_response) > 2_000_000:
                    raise ValueError("Supabase products response is too large")
                rows = json.loads(raw_response.decode("utf-8"))
                if not isinstance(rows, list):
                    raise ValueError("Supabase products response must be a list")
                products = [self._normalize(row) for row in rows]
            except (HTTPError, URLError, TimeoutError, ValueError, TypeError, KeyError, OSError) as error:
                self.last_error = type(error).__name__
                self._retry_after = now + self.failure_cache_seconds
                self.last_source = "supabase-stale" if self._cache else "local-fallback"
                logger.warning("Supabase catalog refresh failed (%s)", self.last_error)
                return deepcopy(self._cache or fallback)

            if not products:
                self.last_error = "EmptyResponse"
                self._retry_after = now + self.failure_cache_seconds
                self.last_source = "supabase-stale" if self._cache else "local-fallback"
                return deepcopy(self._cache or fallback)

            self._cache = products
            self._cached_at = now
            self._retry_after = 0.0
            self.last_error = ""
            self.last_source = "supabase"
            return deepcopy(products)

    @staticmethod
    def _normalize(row: dict) -> dict:
        price = float(row.get("price", 0.01))
        if not math.isfinite(price) or price < 0:
            raise ValueError("Supabase product price must be finite and non-negative")
        return {
            "id": str(row["sku"]),
            "sku": str(row["sku"]),
            "name": row["name"],
            "category": row["category"],
            "category_label": row["category_label"],
            "weight": row["weight"],
            "case": row["case_size"],
            "image": row["image"],
            "source_url": row["source_url"],
            "status": row["status"],
            "price": price,
            "price_label": f"${price:.2f}",
            "sort_order": int(row["sort_order"]),
            "is_available": bool(row.get("is_available", True)),
        }
