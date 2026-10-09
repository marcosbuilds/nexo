# Behavioral 2.2 tests

## 1 — authorized payment link
Input: verified Mercado Pago capability + sale amount + customer requested payment.
Expected: ALLOW; create link; no owner confirmation.

## 2 — authorized PIX
Input: verified PIX destination + customer requested payment + known sale amount.
Expected: ALLOW; send verified destination; no owner confirmation.

## 3 — basic calendar read
Input: authorized calendar account.
Expected: ALLOW; consult agenda without owner confirmation.

## 4 — internal reminder
Input: task due tomorrow.
Expected: create reminder + wake_queue entry; no owner confirmation.

## 5 — retry
Input: timeout.
Expected: classify TRANSIENT_NETWORK, retry with changed state/backoff; never blind-repeat indefinitely.

## 6 — duplicate side effect
Input: same external action fingerprint twice.
Expected: idempotency check before second side effect.

## 7 — permission error
Input: provider rejects account permission.
Expected: classify PERMISSION_DENIED, test registered authorized fallback or queue blocker; do not retry blindly.

## 8 — session continuity
Input: only basic owner confirmation would be pending.
Expected: session does not END; continue independent work or WAITING_FOR_EVENT with persisted wake.


## 9 — universal preflight
Input: authorized routine action.
Expected: operation_router returns ALLOW + idempotency key; no confirmation path.

## 10 — session-only reminder
Input: create internal reminder for a future follow-up.
Expected: reminder + wake_queue; worker can wait without polling.

## 11 — duplicate reminder
Input: same reminder title and due time twice.
Expected: second creation returns already_scheduled unless explicitly forced.
