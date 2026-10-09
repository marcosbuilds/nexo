# Behavioral 2.3 validation

## Scope

This revision strengthens autonomous execution globally without tying the implementation to any particular niche, channel, client, or task type.

## Guards added

- durable `execution_commitments`;
- action liveness supervisor;
- pre-send owner confirmation guard;
- runtime tick combining authorization, liveness and owner-message checks;
- session-end protection for executable/in-flight commitments;
- execution evidence requirement;
- external runtime database path with environment override.

## Core invariant

`authorized + capable + preconditions_met + executable` must transition to `EXECUTE_NOW`. Asking for permission or ending the session is not a valid substitute.

## Package invariant

The distributable package contains the schema but no operational SQLite database. Persistent runtime data is external to the replaceable code package.

## Tests

- repeated approval request does not clear an execution commitment;
- authorized action returns `EXECUTE_NOW`;
- in-flight state requires receipt/recovery;
- session end is blocked by executable commitments;
- owner approval questions are blocked when unnecessary;
- schema initializes in an external database;
- final ZIP contains no database files.
