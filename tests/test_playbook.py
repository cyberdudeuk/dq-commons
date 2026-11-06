"""The playbook works from the toolkit: workspaces, evidence-based status, the MCP tool and release housekeeping."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dqkit import mcp_server, playbook  # noqa: E402


class Workspace(unittest.TestCase):
    def test_init_status_and_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            ws = Path(d) / "ws"
            files = playbook.init(ws, "births-register", "Births register")
            self.assertEqual(len(files), 8)
            self.assertEqual(playbook.init(ws, "births-register"), [], "init must not overwrite existing files")
            st = playbook.status(ws)
            self.assertEqual(st["done"], 0)
            self.assertEqual(st["next"]["stage"], 1)
            # stage 1 evidence: a register row; ticking every checklist item makes it done
            with (ws / "01-register.csv").open("a", encoding="utf-8") as fh:
                fh.write("Births register,br-1" + "," * 13 + "\n")
            readme = (ws / "README.md").read_text(encoding="utf-8")
            head, rest = readme.split("## Stage 2:", 1)
            (ws / "README.md").write_text(head.replace("- [ ] ", "- [x] ") + "## Stage 2:" + rest, encoding="utf-8")
            st = playbook.status(ws)
            self.assertEqual(st["stages"][0]["state"], "done")
            self.assertEqual(st["stages"][1]["state"], "to do")
            self.assertEqual(st["next"]["stage"], 2)
            # stage 3 evidence comes from a real dqkit check run
            data = Path(d) / "data.csv"
            data.write_text("id,name\n1,Ann\n2,\n", encoding="utf-8")
            run = lambda *a: subprocess.run([sys.executable, "-m", "dqkit", *a], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(run("suggest", str(data), "--id", "births-register", "--out", str(ws / "births-register.rules.yaml")).returncode, 0)
            self.assertEqual(run("check", str(data), str(ws / "births-register.rules.yaml"), "--out", str(ws / "results"), "--history", str(ws / "history")).returncode, 0)
            st = playbook.status(ws)
            ev = {s["n"]: s["evidence"] for s in st["stages"]}
            self.assertTrue(ev[2] and ev[3] and ev[6] and ev[7])
            self.assertIn("latest_result", st)
            out = run("playbook", "status", str(ws))
            self.assertIn("Playbook status for births-register", out.stdout)

    def test_issue_actions_need_owners(self):
        with tempfile.TemporaryDirectory() as d:
            playbook.init(d, "a")
            p = Path(d) / "04-issues.csv"
            header = p.read_text(encoding="utf-8")
            n = len(header.strip().split(","))
            p.write_text(header + ",".join(["I1"] + [""] * (n - 1)) + "\r\n", encoding="utf-8")
            self.assertFalse(playbook.status(d)["stages"][4]["evidence"])

    def test_guide(self):
        self.assertEqual(len(playbook.guide()["stages"]), 8)
        self.assertEqual(playbook.guide("prioritise")["n"], 4)
        self.assertEqual(playbook.guide(6)["id"], "report")
        with self.assertRaises(ValueError):
            playbook.guide("nine")


class Mcp(unittest.TestCase):
    def test_playbook_tool(self):
        self.assertIn("playbook", {t["name"] for t in mcp_server.TOOLS})
        self.assertEqual(mcp_server.call_tool("playbook", {"stage": "1"})["id"], "identify")
        with self.assertRaises(mcp_server.ToolError):
            mcp_server.call_tool("playbook", {"workspace": "/etc"})


class Versions(unittest.TestCase):
    def test_versions_agree(self):
        latest = str(yaml.safe_load((ROOT / "knowledge" / "releases.yaml").read_text(encoding="utf-8"))["releases"][0]["version"])
        self.assertIn(f'version = "{latest}"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        self.assertIn(f'__version__ = "{latest}"', (ROOT / "dqkit" / "__init__.py").read_text(encoding="utf-8"))
        self.assertEqual(mcp_server.SERVER_INFO["version"], latest)
        notes = subprocess.run([sys.executable, str(ROOT / "scripts" / "release_notes.py"), latest], capture_output=True, text=True)
        self.assertEqual(notes.returncode, 0, notes.stderr)
        self.assertRegex(notes.stdout, r"### (New|Changed|Fixed)")  # a patch release may only fix things


if __name__ == "__main__":
    unittest.main()
