"""Unit tests for the extractors."""

from __future__ import annotations

from src.extractors.base_extractor import BaseExtractor
from src.extractors.postgres import PostgresExtractor
from src.extractors.sqlserver import SQLServerExtractor


def test_sqlserver_extractor(config):
    extractor = SQLServerExtractor(config["paths"]["sqlserver_sales"])
    df = extractor.extract()

    assert isinstance(extractor, BaseExtractor)
    assert extractor.source_system == "core"
    assert len(df) == 6  # 9001-9003, 9005-9007 (9004 absent)
    assert list(df.columns) == [
        "tx_id",
        "checkout_timestamp",
        "customer_blob",
        "sku_code",
        "gross_amt_usd",
        "tax_amt",
        "is_refunded",
    ]


def test_postgres_extractor(config):
    extractor = PostgresExtractor(config["paths"]["postgres_sales"])
    df = extractor.extract()

    assert isinstance(extractor, BaseExtractor)
    assert extractor.source_system == "acquired"
    assert len(df) == 5  # includes the duplicate 9005
    assert list(df.columns) == [
        "id",
        "sale_date",
        "customer_id",
        "product_sku",
        "total_price",
        "currency",
        "order_status",
    ]
