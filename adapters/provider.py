"""Payment provider boundary. The worker decides what to create; adapter performs provider-specific side effects."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Protocol

class PaymentProvider(Protocol):
    def create_link(self, amount: float, description: str, metadata: dict[str,Any], idempotency_key: str) -> dict[str,Any]: ...
    def check_payment(self, reference: str, expected_amount: float) -> dict[str,Any]: ...

@dataclass
class PaymentReceipt:
    status: str
    provider_reference: str | None
    url: str | None
    evidence: dict[str,Any]
