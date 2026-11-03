"""Write integrations/ndl-mcp-domain.json: the toolkit's MCP tools as a 'data quality' domain for other
MCP platforms (for example the NDL Civic Tech MCP platform). Generated from dqkit/mcp_server.py so it
always matches the server. Run: python scripts/mcp_manifest.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dqkit import mcp_server  # noqa: E402

manifest = {
    "domain": "data-quality",
    "title": "Public Sector Data Quality Commons",
    "description": "Check data against quality rules, draft rules, assess against framework packs, translate results between frameworks and score issues with the UK government issues framework.",
    "server": {"command": "python", "args": ["-m", "dqkit.mcp_server"], "env": {"DQKIT_MCP_ROOT": "<folder the agent may read>"},
               "protocol": mcp_server.PROTOCOL_VERSION if hasattr(mcp_server, "PROTOCOL_VERSION") else "2025-06-18", "transport": "stdio"},
    "safety": {"read_only": True, "file_access": "limited to DQKIT_MCP_ROOT", "personal_data": "results contain examples of failing rows; keep the root folder free of data the agent should not see",
               "human_in_loop": "rules drafted by an agent must be reviewed before use"},
    "licence": "MIT",
    "tools": [{"name": t["name"], "title": t.get("title", t["name"]), "description": t.get("description", "")} for t in mcp_server.TOOLS],
}
out = ROOT / "integrations" / "ndl-mcp-domain.json"
out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {out.relative_to(ROOT)} with {len(manifest['tools'])} tools")
