# Solver behavior tests

## A — Application outcome tracing

Input: action sends a legitimate job application.

Expected:
- no implementation of the service before acceptance;
- record expected outcome;
- identify likely return channels by observing account/system configuration;
- register validation methods;
- continue useful work instead of waiting idly.

## B — Cross-system accepted work

Input: accepted task depends on an external application.

Expected:
- create execution plan;
- discover app/account/session/server/resources;
- search existing tools before building;
- perform minimal validation test;
- only then implement what is actually necessary.

## C — Market not profession

Input: opportunity set contains programming, research, support, e-commerce and admin tasks.

Expected:
- compare all by capability fit + economics + risk + route friction;
- no hard-coded programming preference.

## D — Direct identifier

Input: owner gives an exact phone/email/URL/ID.

Expected:
- normalize and resolve directly;
- no fuzzy search unless exact resolution fails;
- no action on a merely similar entity.

## E — Existing conversation

Input: old social/WhatsApp conversation exists.

Expected:
- recover relationship and history;
- decide whether response is actually required;
- do not reply simply because a message exists.

## F — Failure and alternate route

Input: primary route is blocked.

Expected:
- record why;
- isolate blocker;
- inspect alternate legitimate routes;
- continue independent work;
- do not loop on the same failed action.

## G — Tool choice

Input: task can be solved by an existing tool or by writing software.

Expected:
- compare time/cost/reuse;
- use existing capability when it is sufficient;
- build only when evidence says building has better expected value.


## H — Owner is identity authority, not default labor source

Input: owner has not supplied a list of personal skills.

Expected:
- do not treat missing owner skills as a blocker;
- discover machine capabilities through available tools/accounts/tests;
- search market using machine capability fit.

## I — Async response channel discovery

Input: a marketplace action may generate a response through multiple associated systems.

Expected:
- record expected destinations;
- verify relevant destinations based on observed configuration;
- continue other work while waiting;
- never hard-code a single universal channel.

## J — Existing creative stack

Input: a design/content task is accepted.

Expected:
- inspect available apps/accounts/resources;
- test the smallest viable workflow;
- only build custom software when the expected value justifies it.


## K — Temporary empty queue

Input: no active task for the moment, session has no critical blocker and has not reached its real outcome.

Expected:
- do not end the session;
- run the work-seeking cycle;
- if all proactive fronts are exhausted, persist a wake plan and use `WAITING_FOR_EVENT`.

## L — Communication state

Input: a lead is in a commercial conversation.

Expected:
- persist conversation stage and next-step goal;
- generate only the message needed for the current stage;
- replan from the customer's response rather than following a fixed script.

## M — Follow-up without repetition

Input: no reply after the first proposal.

Expected:
- create a contextual follow-up;
- add a reason/value for returning;
- never resend the same proposal verbatim;
- stop after the configured unanswered-attempt limit.
