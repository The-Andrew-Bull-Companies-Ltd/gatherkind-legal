# Secret checks for this repository

Gitleaks 8.30.1 runs locally before commits and pushes. It uses the bundled default rules plus the reviewed Supabase secret-key rule in `.gitleaks.toml`. No scanner licence or external scanning service is required. Gitleaks is in security-maintenance mode; review future replacements/upgrades deliberately.

## Setup on every new clone or machine

Use Python 3.10+ and Git. The installer also requires curl and internet access to the official Gitleaks release. Supported binaries are macOS arm64/x64 and Linux arm64/x64; Windows setup is not implemented.

```sh
python3 .security/secrets.py install
python3 .security/secrets.py install-hooks
python3 .security/secrets.py history
```

The installer verifies a pinned SHA-256 of the official archive, extracts only the executable and writes it to ignored `.tools/gitleaks/gitleaks`. `install-hooks` changes only this repository's `core.hooksPath` to `.githooks`; it refuses to replace an unrelated hook setup. Git does not enable hooks automatically on clone. Keep these hook files present on the branch being used. No global Git configuration or other project's tooling is changed.

## What runs

- Pre-commit scans the staged diff, even if the worktree differs, and rejects staged paths that match ignore rules (including `git add -f .env`).
- Pre-push scans all available Git history plus the supplied pushed tips, so deleting a secret in a later commit does not hide it. Local hooks work offline after installation; missing/wrong-version tools and scanner failures block the operation.
- `.github/workflows/secret-scanning.yml` uses the standalone binary with pinned archive checksums, a full checkout and the same history scan. It also runs the disposable-repository hook tests. This avoids the separately licensed Gitleaks Action. GitHub Actions usage still follows the account's normal allowance/billing. CI runs after upload and cannot replace local or GitHub push blocking.

The scanner uses explicit repository configuration, ignores inherited Gitleaks config overrides, disables inline suppression comments and fingerprint-ignore files, and fully redacts reports. The wrapper prints only finding metadata (rule/file/line/commit), never matched source or secret values; temporary reports are held in a private temporary directory and removed afterwards. Do not paste credentials or raw scanner output into issues/chat.

## Checks and handling failures

```sh
python3 .security/secrets.py staged
python3 .security/secrets.py history
python3 .security/test_secrets.py
```

Tests use disposable repositories and fabricated tokens: staged/worktree mismatch, forced ignored files, missing scanner and a historical secret removed from the latest commit. They do not send test tokens to GitHub or a provider. The installer downloads only during explicit setup; commits/pushes never download tools.

A blocked finding needs inspection and correction; do not bypass hooks or blanket-allowlist a directory. If it is a real exposed credential, revoke/rotate it and assess where it went before considering history remediation. A false positive needs a narrow, reviewed configuration change. Generic install/configuration failures intentionally suppress raw subprocess output; first check the pinned binary is installed and `.gitleaks.toml` parses correctly.

## Limits

Local hooks can be bypassed or removed and apply only to configured clones. Detection covers recognised patterns, not every possible password or private document. Binary/PDF content is not comprehensively extracted; review attachments before committing. Ignored local secrets are not scanned by Git-history checks. The cloud build archive and app bundle are separate boundaries: these hooks do not run for a direct EAS upload. Review its exclusions/archive and never put secrets in public client config.

GitHub server-side scanning/push protection is configured separately. Do not infer it is enabled from this file or turn on a paid add-on without approval. Source: [Gitleaks](https://github.com/gitleaks/gitleaks), [release](https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1).
