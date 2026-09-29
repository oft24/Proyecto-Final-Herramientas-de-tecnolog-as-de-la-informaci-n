"""Private S3 storage for order receipts."""

from __future__ import annotations

import json
import os
from uuid import uuid4


def _client():
    import boto3

    return boto3.client(
        "s3",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        endpoint_url=os.getenv("S3_ENDPOINT_URL") or None,
    )


def is_ready() -> bool:
    bucket = os.getenv("S3_BUCKET", "").strip()
    if not bucket:
        return False
    try:
        _client().head_bucket(Bucket=bucket)
        return True
    except Exception:
        return False


def put_order_receipt(order: dict, items: list[dict]) -> str | None:
    bucket = os.getenv("S3_BUCKET", "").strip()
    if not bucket:
        return None
    key = f"orders/{order['id']}-{uuid4().hex[:8]}.json"
    _client().put_object(
        Bucket=bucket,
        Key=key,
        Body=json.dumps({"order": order, "items": items}, ensure_ascii=False, default=str).encode("utf-8"),
        ContentType="application/json",
        ServerSideEncryption="AES256",
    )
    return key
