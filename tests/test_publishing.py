"""Edits the owner can make in the admin must still pass the checks that run before publishing."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.helpers import ROOT

NESTED = "MP_NESTED_TEST_RUN"
SKIP = shutil.ignore_patterns(".git", ".superpowers", ".impeccable", "__pycache__", "photo-originals", "node_modules")


@unittest.skipIf(os.environ.get(NESTED), "already inside the copied site")
class OwnerEditsPublish(unittest.TestCase):
    def test_ordinary_edits_pass_ci_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "site"
            shutil.copytree(ROOT, copy, ignore=SKIP)
            content = copy / "content"
            site = json.loads((content / "site.json").read_text(encoding="utf-8"))
            site["contact"]["email"] = "hello@example.com"
            site["contact"]["whatsapp"] = "https://wa.me/+8801700000000"
            site["home"]["video"] = "I also cut short films for friends."
            site["about"]["sections"] = [{"heading": "Now", "text": "A short about page."}]
            (content / "site.json").write_text(json.dumps(site, indent=2) + "\n", encoding="utf-8")
            projects = json.loads((content / "projects.json").read_text(encoding="utf-8"))
            # Delete a project that isn't on the home page, whichever the owner has picked.
            gone = next(p for p in projects if not p["featured"])
            projects = [p for p in projects if p is not gone]
            (content / "projects.json").write_text(json.dumps(projects, indent=2) + "\n", encoding="utf-8")

            env = {**os.environ, NESTED: "1", "GITHUB_ACTIONS": "true"}
            run = lambda *args: subprocess.run([sys.executable, *args], cwd=copy, env=env, capture_output=True, text=True)
            build = run("-m", "scripts.build_site")
            self.assertEqual(build.returncode, 0, build.stderr)
            tests = run("-m", "unittest", "discover", "-s", "tests", "-t", ".")
            self.assertEqual(tests.returncode, 0, tests.stderr[-3000:])


if __name__ == "__main__":
    unittest.main()
