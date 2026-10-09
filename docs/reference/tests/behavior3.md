# Behavioral 2.3 tests

## 1 — executable action cannot fall back to confirmation
Input: requested=true, authorized=true, capability_available=true, preconditions_met=true, status=READY, confirmation_requests=3.
Expected: `EXECUTE_NOW`; never `ASK_PERMISSION` or `WAITING_OWNER`.

## 2 — session cannot end around executable action
Input: executable commitment + session_end_requested=true.
Expected: `BLOCK_SESSION_END`.

## 3 — model claim is not execution evidence
Input: status=EXECUTED, expected_result=true, execution_evidence=false.
Expected: `VERIFY_OUTCOME`.

## 4 — stalled in-flight action is inspected, not blindly repeated
Input: status=RUNNING, no_progress_cycles=1, execution_evidence=false.
Expected: `RESUME_OR_INSPECT`.

## 5 — owner approval message blocked
Input: owner_channel=true, authorized_and_executable=true, message asks whether it may execute the action.
Expected: `BLOCK`.

## 6 — customer-facing question is not blocked by owner guard
Input: owner_channel=false, message is a normal question.
Expected: `ALLOW`.

## 7 — durable commitment records progress
Input: create ActionCommitment, record confirmation request, then execution start, then verified result.
Expected: READY → RUNNING → VERIFIED; confirmation count retained as diagnostic evidence.

## 8 — shipped package contains no runtime database
Input: inspect ZIP members.
Expected: no `*.sqlite`, `*.sqlite3` or `*.db`; schema remains present.


## 9 — canonical runtime tick
Input: authorized, capable, executable action plus an owner-channel draft asking permission.
Expected: liveness=`EXECUTE_NOW`, owner-message guard=`BLOCK`.

## 10 — operation router carries execution intent
Input: routine action with verified resource and ready liveness state.
Expected: `ALLOW_EXECUTE` and `next_action=EXECUTE_NOW`.
