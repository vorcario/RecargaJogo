"""Persistência SQLite transacional para checkout e fulfillment."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .errors import ConflictError, NotFoundError


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class OrderRepository:
    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            yield connection
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    checkout_token_hash TEXT NOT NULL,
                    player_id TEXT NOT NULL,
                    product_id TEXT NOT NULL,
                    base_diamonds INTEGER NOT NULL,
                    bonus_diamonds INTEGER NOT NULL,
                    total_diamonds INTEGER NOT NULL,
                    amount_cents INTEGER NOT NULL,
                    payment_method TEXT NOT NULL,
                    payment_provider TEXT NOT NULL,
                    provider_payment_id TEXT UNIQUE,
                    provider_idempotency_key TEXT NOT NULL UNIQUE,
                    pix_qr_code TEXT,
                    pix_copy_paste TEXT,
                    pix_expires_at TEXT,
                    beneficiary_name TEXT,
                    payment_status TEXT NOT NULL,
                    fulfillment_status TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    paid_at TEXT,
                    fulfilled_at TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    scope TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    order_id TEXT NOT NULL REFERENCES orders(id),
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (scope, idempotency_key)
                );
                CREATE TABLE IF NOT EXISTS webhook_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    order_id TEXT REFERENCES orders(id),
                    received_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS fulfillment_events (
                    id TEXT PRIMARY KEY,
                    order_id TEXT NOT NULL UNIQUE REFERENCES orders(id),
                    event_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS orders_provider_payment_idx ON orders(provider_payment_id);
                CREATE INDEX IF NOT EXISTS orders_payment_status_idx ON orders(payment_status);
                """
            )

    @staticmethod
    def _row(row: sqlite3.Row | None) -> dict[str, Any] | None:
        return dict(row) if row is not None else None

    def get_order(self, order_id: str) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not row:
            raise NotFoundError("Pedido não encontrado.")
        return self._row(row) or {}

    def get_order_by_provider(self, provider_payment_id: str | None) -> dict[str, Any] | None:
        if not provider_payment_id:
            return None
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM orders WHERE provider_payment_id = ?", (provider_payment_id,)).fetchone()
        return self._row(row)

    def create_order(
        self,
        *,
        order_id: str,
        checkout_token_hash: str,
        player_id: str,
        product: Any,
        idempotency_key: str,
        request_hash: str,
    ) -> tuple[dict[str, Any], bool]:
        created_at = now_iso()
        with self.transaction() as connection:
            replay = connection.execute(
                "SELECT request_hash, order_id FROM idempotency_keys WHERE scope = 'create_order' AND idempotency_key = ?",
                (idempotency_key,),
            ).fetchone()
            if replay:
                if replay["request_hash"] != request_hash:
                    raise ConflictError("A chave de idempotência foi reutilizada com dados diferentes.")
                row = connection.execute("SELECT * FROM orders WHERE id = ?", (replay["order_id"],)).fetchone()
                return self._row(row) or {}, False

            connection.execute(
                """INSERT INTO orders (
                    id, checkout_token_hash, player_id, product_id, base_diamonds, bonus_diamonds,
                    total_diamonds, amount_cents, payment_method, payment_provider,
                    provider_idempotency_key, payment_status, fulfillment_status, status,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PIX', 'TURBOFYPAY', ?, 'PENDING', 'PENDING', 'PENDING', ?, ?)""",
                (
                    order_id, checkout_token_hash, player_id, product.id, product.base_diamonds,
                    product.bonus_diamonds, product.total_diamonds, product.amount_cents,
                    f"pix:{order_id}", created_at, created_at,
                ),
            )
            connection.execute(
                "INSERT INTO idempotency_keys (scope, idempotency_key, request_hash, order_id, created_at) VALUES ('create_order', ?, ?, ?, ?)",
                (idempotency_key, request_hash, order_id, created_at),
            )
            row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            return self._row(row) or {}, True

    def store_pix_charge(self, order_id: str, charge: dict[str, Any]) -> dict[str, Any]:
        pix = charge.get("pix") or {}
        beneficiary = charge.get("beneficiary") or {}
        now = now_iso()
        with self.transaction() as connection:
            row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not row:
                raise NotFoundError("Pedido não encontrado.")
            if row["provider_payment_id"]:
                return self._row(row) or {}
            connection.execute(
                """UPDATE orders SET provider_payment_id = ?, pix_qr_code = ?, pix_copy_paste = ?,
                    pix_expires_at = ?, beneficiary_name = ?, updated_at = ? WHERE id = ?""",
                (
                    str(charge["id"]), pix.get("qrCode"), pix.get("copyPaste"), pix.get("expiresAt"),
                    beneficiary.get("name"), now, order_id,
                ),
            )
            row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            return self._row(row) or {}

    def record_webhook_and_apply(
        self,
        *,
        event_id: str,
        event_type: str,
        payload_hash: str,
        order_id: str | None,
        provider_payment_id: str | None,
    ) -> tuple[dict[str, Any] | None, bool, bool]:
        """Returns (order, first_event, fulfillment_event_created)."""
        with self.transaction() as connection:
            existing = connection.execute("SELECT event_id FROM webhook_events WHERE event_id = ?", (event_id,)).fetchone()
            if existing:
                row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone() if order_id else None
                return self._row(row), False, False

            if not order_id and provider_payment_id:
                mapped = connection.execute("SELECT id FROM orders WHERE provider_payment_id = ?", (provider_payment_id,)).fetchone()
                order_id = mapped["id"] if mapped else None
            connection.execute(
                "INSERT INTO webhook_events (event_id, event_type, payload_hash, order_id, received_at) VALUES (?, ?, ?, ?, ?)",
                (event_id, event_type, payload_hash, order_id, now_iso()),
            )
            if not order_id:
                return None, True, False

            row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not row:
                return None, True, False
            fulfillment_created = False
            if event_type == "charge.paid" and row["payment_status"] != "PAID":
                paid_at = now_iso()
                connection.execute(
                    """UPDATE orders SET payment_status = 'PAID', fulfillment_status = 'FULFILLMENT_PENDING',
                    status = 'FULFILLMENT_PENDING', paid_at = ?, updated_at = ? WHERE id = ?""",
                    (paid_at, paid_at, order_id),
                )
                event_cursor = connection.execute(
                    """INSERT OR IGNORE INTO fulfillment_events
                    (id, order_id, event_name, state, created_at, updated_at)
                    VALUES (?, ?, 'order.ready_for_fulfillment', 'PENDING', ?, ?)""",
                    (f"ful_{order_id}", order_id, paid_at, paid_at),
                )
                fulfillment_created = event_cursor.rowcount == 1
            elif event_type == "charge.expired" and row["payment_status"] == "PENDING":
                timestamp = now_iso()
                connection.execute(
                    "UPDATE orders SET payment_status = 'EXPIRED', status = 'EXPIRED', updated_at = ? WHERE id = ?",
                    (timestamp, order_id),
                )
            elif event_type == "charge.cancelled" and row["payment_status"] == "PENDING":
                timestamp = now_iso()
                connection.execute(
                    "UPDATE orders SET payment_status = 'FAILED', status = 'FAILED', updated_at = ? WHERE id = ?",
                    (timestamp, order_id),
                )
            current = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            return self._row(current), True, fulfillment_created

    def ready_fulfillment_events(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """SELECT o.*, f.id AS fulfillment_event_id, f.event_name, f.state AS event_state
                   FROM fulfillment_events f JOIN orders o ON o.id = f.order_id
                   WHERE o.fulfillment_status IN ('FULFILLMENT_PENDING', 'PROCESSING')
                   ORDER BY f.created_at ASC"""
            ).fetchall()
        return [self._row(row) or {} for row in rows]

    def set_fulfillment_status(self, order_id: str, status: str) -> dict[str, Any]:
        allowed = {"processing", "fulfilled", "failed"}
        if status not in allowed:
            raise ConflictError("Status de fulfillment inválido.")
        with self.transaction() as connection:
            row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            if not row:
                raise NotFoundError("Pedido não encontrado.")
            if row["payment_status"] != "PAID":
                raise ConflictError("Somente pedidos pagos podem entrar em fulfillment.")
            timestamp = now_iso()
            if status == "processing":
                fulfillment_status, aggregate, fulfilled_at, event_state = "PROCESSING", "FULFILLMENT_PENDING", None, "PROCESSING"
            elif status == "fulfilled":
                fulfillment_status, aggregate, fulfilled_at, event_state = "FULFILLED", "FULFILLED", timestamp, "FULFILLED"
            else:
                fulfillment_status, aggregate, fulfilled_at, event_state = "FAILED", "FAILED", None, "FAILED"
            connection.execute(
                """UPDATE orders SET fulfillment_status = ?, status = ?, fulfilled_at = COALESCE(?, fulfilled_at),
                updated_at = ? WHERE id = ?""",
                (fulfillment_status, aggregate, fulfilled_at, timestamp, order_id),
            )
            connection.execute("UPDATE fulfillment_events SET state = ?, updated_at = ? WHERE order_id = ?", (event_state, timestamp, order_id))
            current = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
            return self._row(current) or {}

    def fulfillment_event_count(self, order_id: str) -> int:
        with self.connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM fulfillment_events WHERE order_id = ?", (order_id,)).fetchone()
        return int(row["count"])
