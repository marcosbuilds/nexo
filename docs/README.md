# Documentation map

The active runtime contract is intentionally small. The worker loads the core
and context packet once per cycle, then retrieves only decision-relevant
knowledge records. Deleted historical playbooks are not alternate policy.

- [`core.md`](core.md): authoritative operating behavior;
- [`context.md`](context.md): compact per-cycle packet and loading policy;
- [`foundations.md`](foundations.md): rationale and method selection;
- [`../knowledge/`](../knowledge): structured rules, methods, lessons, and
  source provenance.

Developer-only material stays in the repository surface and is excluded by the
runtime packaging allowlist. It must never be added to the runtime merely to
explain installation, release, testing, or repository maintenance.

When a rule conflicts with a lower-level note, use this precedence:

1. executable safety and authorization gates;
2. `core.md`;
3. current configuration;
4. retrieved knowledge with evidence;
5. a local lesson scoped to the same type of situation.

Never resolve a conflict by loading every document. Record the conflict,
choose the smallest safe route, and update the source contract in a deliberate
release.
