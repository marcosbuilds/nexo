"""Payment metadata and idempotent link preparation. Provider side effects live in adapters."""
from __future__ import annotations
import hashlib
import json
from typing import Any


def sale_fingerprint(sale: dict[str, Any]) -> str:
    raw = json.dumps({
        "job_id": sale.get("job_id"), "customer_id": sale.get("customer_id"),
        "amount": sale.get("amount"), "currency": sale.get("currency", "BRL"),
        "description": sale.get("description"), "reference": sale.get("reference"),
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


def prepare_link(sale: dict[str, Any]) -> dict[str, Any]:
    amount = float(sale.get("amount", 0) or 0)
    if amount <= 0:
        return {"status": "BLOCKED", "reason": "sale_amount_missing"}
    fp = sale_fingerprint(sale)
    label = str(sale.get("description") or f"Pagamento referente ao trabalho {sale.get('job_id', '')}").strip()
    metadata = {
        "reference": sale.get("reference") or fp[:16],
        "job_id": sale.get("job_id"),
        "customer_id": sale.get("customer_id"),
        "description": label,
    }
    return {
        "status": "READY_FOR_PROVIDER",
        "idempotency_key": fp,
        "amount": round(amount, 2),
        "currency": sale.get("currency", "BRL"),
        "description": label,
        "metadata": metadata,
    }
