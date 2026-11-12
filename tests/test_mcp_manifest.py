"""The MCP domain manifest (integrations/ndl-mcp-domain.json) must list exactly the tools the server registers.
It drifted once: three tools (playbook, estimate_effort, weave_rules) were added to dqkit/mcp_server.py and the
manifest was not regenerated, so MCP platforms reading it saw 12 of 15 tools."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dqkit import mcp_server  # noqa: E402


def drift(manifest_tools, server_tools):
    """Differences between the manifest's tools and the server's, as readable lines (empty when they match)."""
    want = {t["name"]: (t.get("title", t["name"]), t.get("description", "")) for t in server_tools}
    have = {t["name"]: (t.get("title"), t.get("description")) for t in manifest_tools}
    out = [f"missing from manifest: {n}" for n in sorted(set(want) - set(have))]
    out += [f"in manifest but not served: {n}" for n in sorted(set(have) - set(want))]
    out += [f"title or description differs: {n}" for n in sorted(set(want) & set(have)) if want[n] != have[n]]
    if not out and [t["name"] for t in manifest_tools] != [t["name"] for t in server_tools]:
        out.append("tool order differs from the server")
    return out


class McpManifest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / "integrations" / "ndl-mcp-domain.json").read_text(encoding="utf-8"))

    def test_manifest_matches_server(self):
        self.assertEqual(drift(self.manifest["tools"], mcp_server.TOOLS), [],
                         "run: python scripts/mcp_manifest.py")

    def test_catches_a_missing_tool(self):
        self.assertIn("missing from manifest: playbook",
                      drift([t for t in self.manifest["tools"] if t["name"] != "playbook"], mcp_server.TOOLS))

    def test_catches_an_extra_tool(self):
        extra = self.manifest["tools"] + [{"name": "delete_data", "title": "x", "description": "x"}]
        self.assertIn("in manifest but not served: delete_data", drift(extra, mcp_server.TOOLS))

    def test_catches_a_stale_description(self):
        stale = [dict(t, description="old") if t["name"] == "check_data" else t for t in self.manifest["tools"]]
        self.assertIn("title or description differs: check_data", drift(stale, mcp_server.TOOLS))


if __name__ == "__main__":
    unittest.main()
