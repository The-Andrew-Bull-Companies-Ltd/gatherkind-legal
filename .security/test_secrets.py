"""Exercise real Git hooks using disposable repos and fabricated, non-working tokens."""
# Fixed executable/argument lists, no shell; push input is restricted to hex object IDs.
# ruff: noqa: S603, S607

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1]


class HookTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gatherkind-hook-test-")
        self.root = Path(self.temp.name)
        self.env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull)
        for key in list(self.env):
            if key.startswith("GIT_") and key not in {"GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL"}:
                del self.env[key]
        for directory in (".security", ".githooks"):
            shutil.copytree(SOURCE / directory, self.root / directory)
        shutil.copy2(SOURCE / ".gitleaks.toml", self.root / ".gitleaks.toml")
        (self.root / ".tools/gitleaks").mkdir(parents=True)
        shutil.copy2(SOURCE / ".tools/gitleaks/gitleaks", self.root / ".tools/gitleaks/gitleaks")
        (self.root / ".gitignore").write_text(".tools/\n.env\n")
        self.git("init", "--quiet")
        self.git("config", "user.name", "Synthetic hook test")
        self.git("config", "user.email", "hook-test@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        result = self.run_command(sys.executable, ".security/secrets.py", "install-hooks")
        self.assertEqual(result.returncode, 0)
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "Clean baseline")
        self.secret = "sb_" + "secret_" + "h7Qk9Vb2Nt6Zp4Lx8Wm3Yc5Rd1Fs0AeU"

    def tearDown(self):
        self.temp.cleanup()

    def run_command(self, *args, input=None):
        return subprocess.run(
            args, cwd=self.root, env=self.env, input=input, capture_output=True, text=True
        )

    def git(self, *args):
        result = self.run_command("git", *args)
        self.assertEqual(result.returncode, 0, "Temporary Git command failed")
        return result.stdout.strip()

    def assert_blocked(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn(self.secret, result.stdout + result.stderr)

    def test_commit_checks_staged_content_even_when_worktree_is_clean(self):
        p = self.root / "settings.txt"
        p.write_text(self.secret)
        self.git("add", "settings.txt")
        p.write_text("clean worktree masking the staged token")
        self.assert_blocked(self.run_command("git", "commit", "-m", "Must block"))
        self.git("add", "settings.txt")
        self.git("commit", "--quiet", "-m", "Clean content passes")

    def test_forced_ignored_file_is_blocked(self):
        (self.root / ".env").write_text("EXAMPLE=nonsecret")
        self.git("add", "-f", ".env")
        self.assert_blocked(self.run_command("git", "commit", "-m", "Must block ignored file"))

    def test_missing_scanner_blocks_commit(self):
        (self.root / ".tools/gitleaks/gitleaks").unlink()
        (self.root / "safe.txt").write_text("safe")
        self.git("add", "safe.txt")
        self.assert_blocked(self.run_command("git", "commit", "-m", "Must block without scanner"))

    def test_push_blocks_secret_deleted_from_latest_commit(self):
        (self.root / "old.txt").write_text(self.secret)
        self.git("add", "old.txt")
        # Only in this disposable fixture: simulate someone bypassing the commit hook.
        self.git(
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "--quiet",
            "-m",
            "Synthetic historical secret",
        )
        self.git("rm", "old.txt")
        self.git("commit", "--quiet", "-m", "Remove synthetic secret")
        tip = self.git("rev-parse", "HEAD")
        data = f"refs/heads/main {tip} refs/heads/main {'0' * 40}\n"
        self.assert_blocked(self.run_command(".githooks/pre-push", input=data))


if __name__ == "__main__":
    unittest.main()
