"""Small PostgreSQL repository used by the marketplace flows."""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row


def _connection_kwargs() -> dict[str, object]:
    return {
        "host": os.getenv("DB_HOST", "db"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "dangoko"),
        "user": os.getenv("DB_USER", "dangoko"),
        "password": os.getenv("DB_PASSWORD", "dangoko-dev-password"),
        "sslmode": os.getenv("DB_SSLMODE", "prefer"),
        "connect_timeout": int(os.getenv("DB_CONNECT_TIMEOUT", "3")),
        "row_factory": dict_row,
    }


@contextmanager
def connection() -> Iterator[psycopg.Connection]:
    with psycopg.connect(**_connection_kwargs()) as conn:
        yield conn


def init_schema() -> None:
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS orders (
                id UUID PRIMARY KEY,
                user_id BIGINT REFERENCES users(id),
                customer_name TEXT NOT NULL,
                customer_email TEXT,
                subtotal NUMERIC(12, 2) NOT NULL,
                shipping NUMERIC(12, 2) NOT NULL,
                total NUMERIC(12, 2) NOT NULL,
                status TEXT NOT NULL,
                s3_key TEXT,
                notification_status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE TABLE IF NOT EXISTS order_items (
                id BIGSERIAL PRIMARY KEY,
                order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
                product_id TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price NUMERIC(12, 2) NOT NULL
            );
            """
        )


def is_ready() -> bool:
    try:
        with connection() as conn:
            conn.execute("SELECT 1")
        return True
    except (psycopg.Error, OSError, ValueError):
        return False


def create_user(name: str, email: str, password_hash: str) -> dict:
    with connection() as conn:
        row = conn.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, name, email
            """,
            (name, email, password_hash),
        ).fetchone()
        return dict(row)


def find_user(email: str) -> dict | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = %s",
            (email,),
        ).fetchone()
        return dict(row) if row else None


def find_user_by_id(user_id: int) -> dict | None:
    with connection() as conn:
        row = conn.execute(
            "SELECT id, name, email FROM users WHERE id = %s",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def create_order(
    order_id: str,
    user_id: int | None,
    customer_name: str,
    customer_email: str | None,
    subtotal: str,
    shipping: str,
    total: str,
    items: list[dict],
    s3_key: str | None,
) -> None:
    with connection() as conn:
        # Insert the order header
        conn.execute(
            """
            INSERT INTO orders (
                id, user_id, customer_name, customer_email, subtotal,
                shipping, total, status, s3_key
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'created', %s)
            """,
            (order_id, user_id, customer_name, customer_email,
             subtotal, shipping, total, s3_key),
        )
        # Insert order items using an explicit cursor (psycopg3: executemany
        # lives on the cursor, not directly on the connection object).
        if items:
            with conn.cursor() as cur:
                cur.executemany(
                    """
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    [
                        (order_id, item["product_id"],
                         item["quantity"], item["unit_price"])
                        for item in items
                    ],
                )


def serialize_order(order: dict, items: list[dict]) -> str:
    return json.dumps({"order": order, "items": items}, ensure_ascii=False, default=str)
