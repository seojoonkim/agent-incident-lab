# Agent Incident Lab

**Turn an agent mistake into a tracked recovery and prevention workflow.**

A small, local-first Python incident ledger with a JSON CLI and installable skills for **Hermes Agent** and **OpenClaw**. MIT licensed. Python 3.9+. No runtime dependencies or API keys required.

> **Early prototype, not an autonomous repair system.** The Hermes native plugin observes exhausted API errors and failed tool results with trusted session IDs, and injects a scoped reminder on the next turn. The skills guide manual ledger use. Neither integration enforces completion or verifies evidence independently. No promise of zero recurrence.

## Install

Install from GitHub (not yet published on PyPI):

```sh
pipx install 'git+https://github.com/seojoonkim/agent-incident-lab.git@v0.1.0'
incidentlab --help
```

Alternatively:

```sh
uv tool install 'git+https://github.com/seojoonkim/agent-incident-lab.git@v0.1.0'
```

You need Python, Git, and either pipx or uv. Do not run both installation methods.

## Hermes Agent

Native automatic observation (recommended):

```sh
hermes plugins install seojoonkim/agent-incident-lab --ref RELEASE_COMMIT_SHA --enable
hermes plugins doctor incidentlab --ci
```

Use the immutable commit shown in the latest release rather than a branch. The plugin stores only sanitized failure classes, task/session IDs, counts, and timestamps in profile-owned plugin state. It does not store prompts, tool arguments/results, URLs, keys, or provider error messages. Intermediate retry failures and events without a session ID are ignored. Start a new session or restart the gateway only when it can be done without interrupting work.

Manual workflow skill:

```sh
incidentlab-install hermes
```

Creates `$HERMES_HOME/skills/incidentlab/SKILL.md` (default `~/.hermes/skills/incidentlab/SKILL.md`). For a named profile, explicitly supply its home:

```sh
incidentlab-install hermes --home ~/.hermes/profiles/my-agent
```

Start a new Hermes session, then load `/incidentlab`. Try: “Record the mistake we just identified, finish the original task, and track the prevention evidence separately.”

## OpenClaw

```sh
incidentlab-install openclaw
```

Creates `~/.openclaw/skills/incidentlab/SKILL.md`. For a custom state home use `--home /path/to/home`. Start a fresh session and ask the agent to load the `incidentlab` skill. Workspace overrides and host skill allowlists can affect discovery.

The OpenClaw integration is a skill, not a native OpenClaw plugin. Do not use `openclaw plugins install` for this repository. Automatic observation is currently Hermes-only. Python and the installed environment must be accessible on the host executing commands; sandbox/container users must install inside that environment. The installer binds the skill to the installed Python executable, avoiding reliance on the gateway's PATH. Reinstall the skill if that environment moves.

Installer scope: only writes the named skill. It never changes approval policy, restarts gateways, or modifies sibling profiles. Repeated identical installation is a no-op; different existing content is preserved and installation fails with a clear error. Back up/remove the existing skill yourself when intentionally replacing it. Uninstall by removing only the `skills/incidentlab` folder and uninstalling the package; incident databases are retained.

## Example workflow

```sh
incidentlab --db ./incidents.db record \
  --scope 'agent-a/account-a/dm-42/no-thread' \
  --task 'task-17' \
  --failure 'provider-error-classified-as-success' \
  --evidence 'restricted-local-log-reference'
```

Copy the returned incident ID:

```sh
incidentlab --db ./incidents.db show INCIDENT_ID
incidentlab --db ./incidents.db attest INCIDENT_ID original --evidence 'original-task-receipt'
incidentlab --db ./incidents.db attest INCIDENT_ID red --evidence 'failing-test-receipt'
incidentlab --db ./incidents.db attest INCIDENT_ID green --evidence 'passing-test-receipt'
incidentlab --db ./incidents.db attest INCIDENT_ID deployment --evidence 'runtime-readback-receipt'
incidentlab --db ./incidents.db close INCIDENT_ID
```

Example strings are placeholders, **not real evidence**. Never fabricate a receipt to pass a gate. If deployment or a test is inapplicable, keep the incident open and explain why: this version deliberately has no waiver feature.

`close` exits 2 with a JSON error until all four attestations exist. Original task recovery and prevention are independent obligations. A closed incident is immutable through the public API; a recurrence creates a new incident. Repeated reports for the same open scope/task/failure accumulate events.

## Python API

```python
from incidentlab import Store

store = Store("incidents.db")
try:
    incident = store.record("agent-a/dm-42", "task-17", "false-success", "log-ref")
    print(store.show(incident))
finally:
    store.close()
```

## What is—and is not—verified

| Capability | v0.1.0 |
|---|---|
| Transactional SQLite ledger and event history | Yes |
| Scope/task/failure deduplication | Yes, exact strings |
| Separate recovery and prevention gates | Yes |
| Hermes/OpenClaw skill file installer | Yes |
| Host skill directory installation tests | Yes, isolated homes |
| Hermes native exhausted-API/tool-failure observation | Yes, profile plugin state |
| Live end-to-end model behavior in both hosts | Not certified |
| Automatic detection / mandatory stop hook | No |
| Running tests and authenticating receipts | No |
| Autonomous source repair or deployment | No |

Anyone with write access to the database can alter it. This is not a tamper-proof audit system. Scope strings are supplied by the caller, not authenticated host identities. Keep credentials and private transcripts out of evidence strings; use references to private artifacts. There is no automatic redactor, network service, or telemetry upload. Use a private directory for databases.

## Why another tool?

[Reflexion](https://arxiv.org/abs/2303.11366) studies learning from linguistic feedback. [Langfuse](https://langfuse.com/resources/engineering/llm-regression-testing) turns evaluation datasets into regression gates. [OpenHands hooks](https://docs.openhands.dev/openhands/usage/customization/hooks) can enforce checks before stopping.

Incident Lab's focus is narrower: keep the original deliverable and recurrence prevention visible as two independent obligations. Integrate with evaluators and agent frameworks rather than claiming to replace them.

Host references: [Hermes skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills/), [OpenClaw skills](https://docs.openclaw.ai/tools/skills).

## Development

```sh
git clone https://github.com/seojoonkim/agent-incident-lab.git
cd agent-incident-lab
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

On Windows use `.venv\Scripts\python.exe`. CI tests Python 3.9, 3.12, and 3.14 on Linux. macOS local smoke tests include package installation and CLI round trips. Windows host skill execution is not certified.

## Roadmap

1. Versioned structured scope with trusted adapter provenance.
2. Bounded approved-test runner and artifact-bound receipts.
3. Observation-only host event adapters, then explicit stop gates.
4. Permissioned repair proposals/PRs with independent verification and rollback.

Contributions should include reproducing tests and preserve privacy, scope isolation, and explicit authorization. Do not add a blanket approval bypass or automatically replay unrelated historical work.

## License

[MIT](LICENSE).
