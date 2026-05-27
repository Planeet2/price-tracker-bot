from contextlib import contextmanager
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from app.config import settings


@contextmanager
def get_connection():
    conn = psycopg2.connect(
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
        host=settings.db_host,
        port=settings.db_port,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS products (
                    id SERIAL PRIMARY KEY,
                    external_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    target_price NUMERIC(12, 2),
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS price_history (
                    id SERIAL PRIMARY KEY,
                    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                    price NUMERIC(12, 2) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_price_history_product_created
                    ON price_history(product_id, created_at DESC);
                """
            )


def upsert_product(external_id: str, name: str, url: str, target_price: Optional[int] = None) -> int:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO products (external_id, name, url, target_price, is_active, updated_at)
                VALUES (%s, %s, %s, %s, TRUE, NOW())
                ON CONFLICT (external_id) DO UPDATE SET
                    name = EXCLUDED.name,
                    url = EXCLUDED.url,
                    is_active = TRUE,
                    target_price = COALESCE(EXCLUDED.target_price, products.target_price),
                    updated_at = NOW()
                RETURNING id;
                """,
                (external_id, name, url, target_price),
            )
            return cur.fetchone()[0]


def save_price(product_id: int, price: int) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO price_history (product_id, price) VALUES (%s, %s);",
                (product_id, price),
            )


def get_last_price(product_id: int) -> Optional[float]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT price
                FROM price_history
                WHERE product_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
                """,
                (product_id,),
            )
            row = cur.fetchone()
            return float(row[0]) if row else None


def get_active_products() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, external_id, name, url, target_price
                FROM products
                WHERE is_active = TRUE
                ORDER BY id;
                """
            )
            return list(cur.fetchall())


def get_products_with_latest_price() -> list[dict]:
    with get_connection() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    p.id,
                    p.name,
                    p.url,
                    p.target_price,
                    latest.price,
                    latest.created_at AS checked_at
                FROM products p
                LEFT JOIN LATERAL (
                    SELECT price, created_at
                    FROM price_history ph
                    WHERE ph.product_id = p.id
                    ORDER BY created_at DESC
                    LIMIT 1
                ) latest ON TRUE
                WHERE p.is_active = TRUE
                ORDER BY p.id;
                """
            )
            return list(cur.fetchall())


def deactivate_product(product_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET is_active = FALSE, updated_at = NOW() WHERE id = %s;",
                (product_id,),
            )
            return cur.rowcount > 0


def set_target_price(product_id: int, target_price: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE products SET target_price = %s, updated_at = NOW() WHERE id = %s AND is_active = TRUE;",
                (target_price, product_id),
            )
            return cur.rowcount > 0
