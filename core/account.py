"""Account and owner identity resolution without repeated human questions."""
from __future__ import annotations
from typing import Any


def resolve_account(accounts: list[dict[str, Any]], *, provider: str, purpose: str | None = None,
                    preferred_email: str | None = None, required_permission: str | None = None) -> dict[str, Any]:
    candidates = [a for a in accounts if str(a.get("provider", "")).lower() == provider.lower()]
    if purpose:
        exact = [a for a in candidates if purpose.lower() in str(a.get("purpose", "")).lower()]
        if exact:
            candidates = exact
    if required_permission:
        allowed = [a for a in candidates if required_permission in str(a.get("permission_level", "")) or a.get("permission_level") in {"owner", "full", "write"}]
        if allowed:
            candidates = allowed
    if preferred_email:
        exact = [a for a in candidates if str(a.get("email", "")).lower() == preferred_email.lower()]
        if exact:
            return {"status": "RESOLVED", "account": exact[0], "basis": "exact_email"}
    ready = [a for a in candidates if str(a.get("status", "")).lower() in {"ready", "logged_in", "active", "connected"}]
    if len(ready) == 1:
        return {"status": "RESOLVED", "account": ready[0], "basis": "single_ready_account"}
    if len(candidates) == 1:
        return {"status": "RESOLVED", "account": candidates[0], "basis": "single_provider_account"}
    if not candidates:
        return {"status": "NOT_FOUND", "next_action": "discover_account_or_create_when_authorized"}
    return {"status": "AMBIGUOUS", "reason": "multiple_equally_valid_accounts", "candidates": candidates}


def owner_identity(profile: dict[str, Any], account: dict[str, Any] | None = None) -> dict[str, Any]:
    identity = dict(profile.get("identity") or profile)
    return {
        "full_name": identity.get("full_name"),
        "preferred_name": identity.get("preferred_name"),
        "public_name": identity.get("public_name") or identity.get("preferred_name") or identity.get("full_name"),
        "phone": (profile.get("contact") or {}).get("phone"),
        "email": (profile.get("contact") or {}).get("primary_email"),
        "account_email": (account or {}).get("email"),
        "identity_source": "owner_profile + authorized_account",
    }
