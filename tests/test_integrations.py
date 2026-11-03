"""GitHub, Jira and Confluence provisioning: config, dry runs, payloads and Markdown conversion."""
import io
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import publish_confluence as pc  # noqa: E402
import sync_backlog as sb  # noqa: E402


class Integrations(unittest.TestCase):
    def test_config_and_templates(self):
        cfg = sb.config()
        self.assertEqual(cfg["jira"]["epic"], "XDMH-210")
        for f in (ROOT / ".github" / "ISSUE_TEMPLATE").glob("*.yml"):
            yaml.safe_load(f.read_text(encoding="utf-8"))
        for w in ("backlog-sync.yml", "docs-to-confluence.yml"):
            wf = yaml.safe_load((ROOT / ".github" / "workflows" / w).read_text(encoding="utf-8"))
            self.assertIn("jobs", wf)

    def test_jira_payload_and_create(self):
        p = sb.jira_payload(sb.config(), "Add a value set", "Detail", "https://github.com/x/y/issues/1")
        self.assertEqual(p["fields"]["parent"]["key"], "XDMH-210")
        self.assertEqual(p["fields"]["project"]["key"], "XDMH")
        seen = {}

        class Resp(io.BytesIO):
            def __enter__(self): return self
            def __exit__(self, *a): return False

        def opener(req, timeout=None):
            seen["url"], seen["auth"] = req.full_url, req.headers["Authorization"]
            return Resp(json.dumps({"key": "XDMH-999"}).encode())

        env = {"JIRA_BASE_URL": "https://example.atlassian.net", "JIRA_EMAIL": "a@example.org", "JIRA_API_TOKEN": "t"}
        old = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            self.assertEqual(sb.create(p, opener), "XDMH-999")
        finally:
            for k, v in old.items():
                os.environ.pop(k, None) if v is None else os.environ.__setitem__(k, v)
        self.assertEqual(seen["url"], "https://example.atlassian.net/rest/api/3/issue")
        self.assertTrue(seen["auth"].startswith("Basic "))

    def test_dry_runs_without_secrets(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith(("JIRA_", "CONFLUENCE_"))}
        r = subprocess.run([sys.executable, "scripts/sync_backlog.py", "--title", "t"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("Dry run", r.stdout)
        r = subprocess.run([sys.executable, "scripts/publish_confluence.py"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_markdown_to_storage(self):
        s = pc.md_to_storage("# Title\n\nSome **bold** and `code` and [link](https://x.org).\n\n- a\n- b\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n```\nx < y\n```\n")
        for frag in ("<h1>Title</h1>", "<strong>bold</strong>", "<code>code</code>", '<a href="https://x.org">link</a>',
                     "<ul><li>a</li><li>b</li></ul>", "<th>A</th>", "<td>2</td>", "CDATA[x < y]"):
            self.assertIn(frag, s)


if __name__ == "__main__":
    unittest.main()
