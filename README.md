# Nexo

Nexo is the public source repository for a neutral autonomous digital worker.
The public project name is not an external persona. The installed runtime uses
only the authorized owner or company identity available in its local profile or
connected accounts.

## Download the ready-to-use runtime

The runtime is distributed as a GitHub Release asset. Do not use a source-tree
archive as the runtime package.

1. Download [worker-0.2.1.zip from the v0.3.0 release](https://github.com/marcosbuilds/nexo/releases/download/v0.3.0/worker-0.2.1.zip).
2. Extract it into any folder.
3. Open the extracted folder as a project in Codex or Claude.
4. Start a conversation in that project with:

   > Start working in this project. Inspect the active operating core, restore
   > the current state, choose the highest-value executable mission, and begin
   > work. Do not ask for routine permission when connected access and the
   > existing mandate already authorize the action. Verify every material
   > result and record the next step.

The extracted project contains the worker's executable code, operational
configuration, compact decision core, structured knowledge, lessons, methods,
source records, database schema, and the complete runtime Humanizer. It does
not contain repository guidance, release instructions, tests, reports, private
data, a prebuilt database, or the public project identity.

## Runtime use

The project can be driven by the AI conversation above. For a direct local
smoke run, use:

```powershell
python tools/execute.py --once
```

For a continuous worker loop:

```powershell
python tools/execute.py --daemon
```

An executor or browser profile is used only when the authorized environment
provides one through `WORKER_EXECUTOR_CMD` or `WORKER_BROWSER_PROFILE`. A
missing connector is a recorded blocker, never a fabricated success.

## Updating

Download the next runtime ZIP from the repository's Releases page, extract it
to a new folder, and keep the existing runtime database and owner profile with
the active installation. Never replace local state blindly. Each release asset
is audited so it contains only runtime material.

## Source development

The source tree is for maintainers. Its compact active contracts are:

- [`docs/core.md`](docs/core.md): one operating contract;
- [`docs/context.md`](docs/context.md): the per-cycle context packet;
- [`docs/foundations.md`](docs/foundations.md): evidence-backed decision foundations;
- [`knowledge/`](knowledge): retrievable rules, methods, lessons, and sources;
- [`tools/package.py`](tools/package.py): runtime allowlist and ZIP audit;
- [`manifest.json`](manifest.json): release metadata and gates.

Run the local validation suite before proposing a release:

```powershell
python -m pytest -q
python -m compileall -q agents adapters core runtime tools
python tools/package.py
python tools/index.py --output runtime_data/knowledge.sqlite3
python tools/retrieve.py --query "customer did not reply"
python tools/audit.py
python tools/legacy.py
```

The external versioner must be invoked with the repository path, the software
version, the worker version, a release message, and explicit push confirmation.
It refuses unbounded version jumps, tracked ZIPs, failed tests, dirty release
state, missing checksums, and an asset that was not uploaded to the GitHub
Release.

## License

The source repository is distributed under the restrictive terms in
[`LICENSE.md`](LICENSE.md). The vendored Humanizer component retains its own
MIT notice in `vendor/humanizer/LICENSE`.
