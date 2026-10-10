#!/usr/bin/env python3
"""Pinned, local-only secret checks. Never print scanner payloads or secret values."""
# Fixed executable/argument lists, no shell; push input is restricted to hex object IDs.
# ruff: noqa: S603, S607

import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

VERSION = "8.30.1"
ARCHIVES = {
    ("Darwin", "arm64"): (
        "darwin_arm64",
        "b40ab0ae55c505963e365f271a8d3846efbc170aa17f2607f13df610a9aeb6a5",
    ),
    ("Darwin", "x86_64"): (
        "darwin_x64",
        "dfe101a4db2255fc85120ac7f3d25e4342c3c20cf749f2c20a18081af1952709",
    ),
    ("Linux", "x86_64"): (
        "linux_x64",
        "551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb",
    ),
    ("Linux", "aarch64"): (
        "linux_arm64",
        "e4a487ee7ccd7d3a7f7ec08657610aa3606637dab924210b3aee62570fb4b080",
    ),
}
ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / ".tools/gitleaks/gitleaks"


def git(*args, input=None):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], input=input, capture_output=True, check=True
    ).stdout


def install():
    target = ARCHIVES.get((platform.system(), platform.machine()))
    if target is None:
        raise RuntimeError("Unsupported platform; add a reviewed official archive/checksum.")
    name, digest = target
    url = f"https://github.com/gitleaks/gitleaks/releases/download/v{VERSION}/gitleaks_{VERSION}_{name}.tar.gz"
    result = subprocess.run(
        [
            "curl",
            "--fail",
            "--silent",
            "--show-error",
            "--location",
            "--proto",
            "=https",
            "--tlsv1.2",
            url,
        ],
        capture_output=True,
        check=True,
    )
    if hashlib.sha256(result.stdout).hexdigest() != digest:
        raise RuntimeError("Gitleaks archive checksum mismatch; installation refused.")
    with tarfile.open(fileobj=io.BytesIO(result.stdout), mode="r:gz") as archive:
        member = archive.getmember("gitleaks")
        if not member.isfile():
            raise RuntimeError("Unexpected Gitleaks archive entry.")
        data = archive.extractfile(member).read()
    BINARY.parent.mkdir(parents=True, exist_ok=True)
    BINARY.write_bytes(data)
    BINARY.chmod(0o755)
    print(f"Installed checksum-verified Gitleaks {VERSION} in this repository only.")


def install_hooks():
    if not BINARY.is_file():
        raise RuntimeError("Run python3 .security/secrets.py install first.")
    current = subprocess.run(
        ["git", "-C", str(ROOT), "config", "--get", "core.hooksPath"],
        capture_output=True,
        text=True,
    )
    if current.returncode not in (0, 1):
        raise RuntimeError("Could not inspect existing Git hook configuration.")
    if current.stdout.strip() not in ("", ".githooks"):
        raise RuntimeError("Existing hooksPath is preserved; integrate hooks explicitly.")
    hooks = Path(os.fsdecode(git("rev-parse", "--git-path", "hooks")).strip())
    if not hooks.is_absolute():
        hooks = ROOT / hooks
    if not current.stdout.strip() and any(
        p.is_file() and not p.name.endswith(".sample") for p in hooks.glob("*")
    ):
        raise RuntimeError("Existing Git hooks are preserved; integrate them explicitly.")
    for name in ("pre-commit", "pre-push"):
        (ROOT / ".githooks" / name).chmod(0o755)
    git("config", "--local", "core.hooksPath", ".githooks")
    print("Enabled repository-local pre-commit and pre-push checks.")


def scan(mode):
    if not BINARY.is_file():
        raise RuntimeError(
            "Scanner missing: run python3 .security/secrets.py install. Operation blocked."
        )
    version = subprocess.run([str(BINARY), "version"], capture_output=True, text=True, check=True)
    if version.stdout.strip() != VERSION:
        raise RuntimeError(
            "Scanner version mismatch; reinstall the pinned version. Operation blocked."
        )
    if mode == "staged":
        names = git("diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
        if names:
            ignored = subprocess.run(
                ["git", "-C", str(ROOT), "check-ignore", "--no-index", "-z", "--stdin"],
                input=names,
                capture_output=True,
            )
            if ignored.returncode not in (0, 1):
                raise RuntimeError("Could not validate staged file exclusions.")
            if ignored.stdout:
                print(
                    "Blocked: staged files match ignore rules. Remove them from the index.",
                    file=sys.stderr,
                )
                return 1
        options = ["--pre-commit", "--staged"]
    else:
        tips = []
        if mode == "push":
            for line in sys.stdin:
                fields = line.split()
                if len(fields) != 4 or not re.fullmatch(r"[0-9a-fA-F]{40,64}", fields[1]):
                    raise RuntimeError("Invalid pre-push input; operation blocked.")
                if set(fields[1]) != {"0"}:
                    tips.append(fields[1])
        # Include all available history, plus explicitly pushed tips not yet on a ref.
        options = ["--log-opts=--all --full-history " + " ".join(tips)]
    env = {key: value for key, value in os.environ.items() if not key.startswith("GITLEAKS_")}
    with tempfile.TemporaryDirectory(prefix="gatherkind-secret-check-") as temp:
        report = Path(temp) / "report.json"
        args = [
            str(BINARY),
            "git",
            *options,
            str(ROOT),
            "--config",
            str(ROOT / ".gitleaks.toml"),
            "--redact=100",
            "--timeout=120",
            "--no-banner",
            "--no-color",
            "--log-level=error",
            "--ignore-gitleaks-allow",
            "--gitleaks-ignore-path",
            os.devnull,
            "--report-format=json",
            "--report-path",
            str(report),
        ]
        result = subprocess.run(args, cwd=ROOT, env=env, capture_output=True)
        if result.returncode:
            findings = json.loads(report.read_text()) if report.exists() else []
            if not isinstance(findings, list) or not findings:
                raise RuntimeError("Secret scanner failed; operation blocked.")
            print(
                f"Blocked: {len(findings)} potential secret(s). Values suppressed.",
                file=sys.stderr,
            )
            for finding in findings:
                # Escape metadata too; never print Secret, Match, commit messages or source content.
                safe = {key: finding.get(key) for key in ("RuleID", "File", "StartLine", "Commit")}
                print(json.dumps(safe, ensure_ascii=True), file=sys.stderr)
            return 1
    print(f"Secret scan passed ({mode}, Gitleaks {VERSION}).")
    return 0


def main():
    commands = {"install", "install-hooks", "staged", "history", "push"}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        print(
            "Usage: python3 .security/secrets.py install|install-hooks|staged|history|push",
            file=sys.stderr,
        )
        return 2
    try:
        command = sys.argv[1]
        if command == "install":
            install()
        elif command == "install-hooks":
            install_hooks()
        else:
            return scan(command)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError, tarfile.TarError):
        # Exceptions from subprocesses may contain commands/input. Do not expose them.
        print(
            "Secret protection could not complete; operation blocked. "
            "Check installation/configuration and .security/README.md.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
