# gatherkind-legal

Public policy source, effective dates and version history. Only approved public material belongs here.

## Status

Repository foundation only. No application runtime, deployment, or consumer policy is implemented by this bootstrap.

## Start here

Read [architecture_summary.md](architecture_summary.md) and [AGENTS.md](AGENTS.md).

## Local use

```sh
git clone git@github.com:The-Andrew-Bull-Companies-Ltd/gatherkind-legal.git
cd gatherkind-legal
git status --short
git diff --check
```

No install or run command exists yet. Runtime commands will be documented alongside the first implementation.
CI checks patch whitespace, unresolved conflict markers and Git history for recognised secret patterns, and exercises the secret-protection hooks.

## Ownership

Initial repository contact: @splishysploshytime. Additional maintainers and review arrangements remain to be assigned.

This repository is intentionally public. Do not add private product specifications, working legal advice, personal data or credentials. No policy here should be treated as effective until approved and published with an effective date.

## Secret protection

Follow [.security/README.md](.security/README.md) to install the pinned scanner and local Git hooks on every new clone before committing or pushing.
