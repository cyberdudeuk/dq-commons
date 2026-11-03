"""The MCP server speaks the protocol over stdio and its tools give the kit's answers."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def session(msgs):
    p = subprocess.run([sys.executable, "-m", "dqkit.mcp_server"], input="\n".join(json.dumps(m) for m in msgs) + "\n",
                       capture_output=True, text=True, cwd=ROOT, timeout=120)
    return [json.loads(l) for l in p.stdout.splitlines() if l.strip()]


class MCP(unittest.TestCase):
    def test_handshake_list_and_call(self):
        out = session([
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "check_data", "arguments": {
                "data_path": "assessments/ndl/chart-data/environment__air-quality.csv", "rules_path": "rules/ndl/air-quality.yaml", "as_of": "2026-10-14"}}},
            {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "check_data", "arguments": {
                "csv_text": "nhs\n9434765919\n9434765918\n", "rules_yaml": "asset: {id: t}\nrules:\n- {id: R1, check: identifier, column: nhs, scheme: nhs_number}\n"}}},
            {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "check_data", "arguments": {"data_path": "/etc/passwd", "rules_yaml": "asset: {id: t}\nrules: []"}}},
            {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "score_issue", "arguments": {"importance": 3, "impact": 3, "performance": 96.5}}},
            {"jsonrpc": "2.0", "id": 7, "method": "nope"},
        ])
        by = {m["id"]: m for m in out}
        self.assertEqual(by[1]["result"]["serverInfo"]["name"], "dqkit")
        names = {t["name"] for t in by[2]["result"]["tools"]}
        self.assertTrue({"check_data", "suggest_rules", "assess_pack", "crosswalk", "score_issue"} <= names)
        r3 = by[3]["result"]["structuredContent"]
        self.assertEqual((r3["rules_met"], r3["rules_total"]), (5, 6))
        self.assertEqual(by[4]["result"]["structuredContent"]["rules"][0]["performance"], 50.0)
        self.assertTrue(by[5]["result"]["isError"])
        self.assertEqual(by[6]["result"]["structuredContent"]["priority"], "Medium")
        self.assertEqual(by[7]["error"]["code"], -32601)
        self.assertNotIn(None, by)  # the notification got no reply


if __name__ == "__main__":
    unittest.main()
