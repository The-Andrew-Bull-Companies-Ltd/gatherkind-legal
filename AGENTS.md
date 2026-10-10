# Contributor instructions

- Read architecture_summary.md first; consult the smallest relevant specification or slice.
- Distinguish accepted decisions, recommendations, backlog and actual implementation status.
- Keep one authoritative owner for each rule, state transition and presentation concern.
- Keep tests self-contained within this repository. Version and test cross-repository contracts.
- Verify dependency compatibility with official documentation before installation; add only what the current slice needs.
- Never commit secrets, production care data, service-role credentials or private keys. Never log care content or tokens.
- Missing environment configuration must fail clearly; never silently select production.
- Use local/capture services in development. Do not reuse Guidra resources or identifiers.
- Prepare and test database migrations locally in gatherkind-api. Hosted migrations are deployed by a human through a designated CI workflow; no direct hosted migration from an agent session.
- Use branches and reviewed PRs for production-impacting changes. No force push to main or destructive history rewrite.
- Add strict type checking, linting and focused tests when a runtime is introduced; the initial hygiene workflow is not application validation.
- Report exact commands run, platforms actually tested, limitations and remaining external setup.

This repository is PUBLIC. Do not copy private specifications or internal legal review here.

- Before committing or pushing, follow [.security/README.md](.security/README.md), install the repository-local secret hooks on new clones, and keep the checks enabled. Never bypass them on project commits/pushes; rejection tests belong in disposable repositories only.
