"""A Model Context Protocol (MCP) server for the data quality kit, so AI agents can use it.

Run:   python -m dqkit.mcp_server            (speaks MCP over standard input and output)
Add it to an MCP-capable assistant as a local (stdio) server with that command.

Design choices for safe agent use:
- Read-only. No tool writes files, changes data or calls the network.
- Files are only read from inside one folder: the folder the server starts in, or DQKIT_MCP_ROOT.
- Every tool is declarative: the agent passes rules (YAML) and data, the kit decides the result.
  Answers are the kit's deterministic outputs, so they can be checked and repeated.
- Data can be passed inline (csv_text) so nothing needs to be saved to disk.

Implements the parts of MCP a tools-only server needs: initialize, tools/list, tools/call, ping.
No third-party library is required.
"""
from __future__ import annotations

import io
import json
import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd
import yaml

from . import framework, packs, profile, rules, sources, trust, pathway

PROTOCOL_VERSION = "2025-06-18"
def _version() -> str:
    try:
        rel = yaml.safe_load((Path(__file__).resolve().parent.parent / "knowledge" / "releases.yaml").read_text(encoding="utf-8"))
        return str(rel["releases"][0]["version"])
    except (OSError, KeyError, IndexError, yaml.YAMLError):
        return "unknown"


SERVER_INFO = {"name": "dqkit", "title": "Public Sector Data Quality Commons kit", "version": _version()}
ROOT = Path(os.environ.get("DQKIT_MCP_ROOT", os.getcwd())).resolve()

DATA_PROPS = {
    "data_path": {"type": "string", "description": "Path to a data file inside the server's folder (CSV, TSV, XLSX, ODS, JSON, JSONL, SQLite)"},
    "csv_text": {"type": "string", "description": "The data itself, as CSV text with a header row (use instead of data_path)"},
    "sheet": {"type": "string", "description": "Spreadsheet sheet name, if data_path is a spreadsheet"},
}
RULE_PROPS = {
    "rules_path": {"type": "string", "description": "Path to a rules file (YAML) inside the server's folder"},
    "rules_yaml": {"type": "string", "description": "The rules file itself, as YAML (use instead of rules_path)"},
}
TOOLS = [
    {"name": "check_data", "title": "Check data against rules",
     "description": "Run a rules file on a dataset. Returns rules met, issues with GOV.UK issues framework priorities, "
                    "a suggested trust level and the DQAP route.",
     "inputSchema": {"type": "object", "properties": {**DATA_PROPS, **RULE_PROPS,
                     "as_of": {"type": "string", "description": "Measure as if on this date (YYYY-MM-DD). Default: today"}}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "suggest_rules", "title": "Suggest starter rules",
     "description": "Profile a dataset and draft a starter rules file (YAML). A data steward must review every rule.",
     "inputSchema": {"type": "object", "properties": {**DATA_PROPS, "asset_id": {"type": "string"}}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "validate_rules", "title": "Validate a rules file",
     "description": "Check a rules file (YAML) is well formed: known checks, identifier schemes, value sets, unique ids.",
     "inputSchema": {"type": "object", "properties": {**RULE_PROPS}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "assess_pack", "title": "Assess against a framework pack",
     "description": "Check data and rules, then report which requirements of a framework or scenario pack are met "
                    "(for example uk-dam-cda, uk-gdqf, ai-ml-readiness, iso-iec-25012).",
     "inputSchema": {"type": "object", "required": ["pack"], "properties": {**DATA_PROPS, **RULE_PROPS, "pack": {"type": "string"},
                     "as_of": {"type": "string"}}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "crosswalk", "title": "Translate results into another framework",
     "description": "Check data and rules, then restate the dimension scores in another framework's terms "
                    "(for example iso-iec-25012, ess-qaf, canada-gc-dq).",
     "inputSchema": {"type": "object", "required": ["to"], "properties": {**DATA_PROPS, **RULE_PROPS, "to": {"type": "string"},
                     "as_of": {"type": "string"}}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "score_issue", "title": "Score an issue with the issues framework",
     "description": "Given importance (1-4), impact (1-4) and measured performance (%), return the target, band, priority "
                    "and resolution timescale from the GOV.UK data quality issues framework.",
     "inputSchema": {"type": "object", "required": ["importance", "impact", "performance"], "properties": {
         "importance": {"type": "integer", "minimum": 1, "maximum": 4}, "impact": {"type": "integer", "minimum": 1, "maximum": 4},
         "performance": {"type": "number"}, "target": {"type": "number"}, "target_policy": {"type": "string", "enum": ["low", "mid", "high"]}}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "list_frameworks", "title": "List frameworks and standards",
     "description": "The registry of data quality frameworks, standards and policies (UK, devolved, sector and international), "
                    "optionally filtered by text.",
     "inputSchema": {"type": "object", "properties": {"filter": {"type": "string"}}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "list_packs", "title": "List framework packs", "description": "The packs that apply frameworks to results.",
     "inputSchema": {"type": "object", "properties": {}}, "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "explore_knowledge", "title": "Explore the data quality knowledge graph",
     "description": "Search the Commons knowledge graph (glossary, thesaurus, frameworks, packs, checks, dimensions, issue types, "
                    "metadata standards, roles, skills, courses, events and jurisdictions). Give 'query' to find concepts, 'node' to list "
                    "its relationships, or 'from' and 'to' to trace the shortest chain of relationships between two concepts.",
     "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}, "node": {"type": "string"},
                     "from": {"type": "string"}, "to": {"type": "string"}}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "weave_metadata", "title": "Weave a metadata record into every catalogue standard",
     "description": "Read one dataset record (DCAT or schema.org JSON-LD, a CKAN package or an ODCS contract) and return it as "
                    "DCAT v3, schema.org, CKAN and an ODCS skeleton, with the gaps for each and the 13 CDA metadata properties.",
     "inputSchema": {"type": "object", "required": ["record"], "properties": {"record": {"type": "object"},
                     "from": {"type": "string", "enum": ["dcat", "schema", "ckan", "odcs"]}}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "check_contract", "title": "Check an ODCS data contract",
     "description": "Validate an ODCS v3 contract; with 'previous', list the changes, which ones break consumers, and the version to use.",
     "inputSchema": {"type": "object", "required": ["contract"], "properties": {"contract": {"type": "object"}, "previous": {"type": "object"}}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "playbook", "title": "Data quality management playbook",
     "description": "The eight-stage playbook for managing the quality of critical data assets (UK DAM policy, usable anywhere). "
                    "With no arguments: the stages. With 'stage' (1-8 or an id such as 'prioritise'): its steps, checklist, roles, "
                    "DAM policy clauses and inclusion check. With 'workspace' (a folder made by 'dqkit playbook init'): which stages "
                    "have evidence and what to do next.",
     "inputSchema": {"type": "object", "properties": {"stage": {"type": "string"}, "workspace": {"type": "string"}}},
     "annotations": {"readOnlyHint": True, "openWorldHint": False}},
    {"name": "list_checks", "title": "List checks, identifier schemes and value sets",
     "description": "What the rules language supports: check types, identifier schemes and value sets.",
     "inputSchema": {"type": "object", "properties": {}}, "annotations": {"readOnlyHint": True, "openWorldHint": False}},
]


class ToolError(Exception):
    """A problem the agent can fix: returned as a tool result with isError true."""


def _inside(path: str) -> Path:
    p = (ROOT / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if p != ROOT and ROOT not in p.parents:
        raise ToolError(f"For safety the server only reads files inside {ROOT}")
    return p


def _data(args: dict) -> pd.DataFrame:
    if args.get("csv_text"):
        return pd.read_csv(io.StringIO(args["csv_text"]), dtype=str, keep_default_na=False, na_values=[""])
    if args.get("data_path"):
        src = sources.normalise(str(_inside(args["data_path"])))
        if src["type"] in ("sql", "ckan"):
            raise ToolError("This server reads local files only")
        if args.get("sheet"):
            src["sheet"] = int(args["sheet"]) if str(args["sheet"]).isdigit() else args["sheet"]
        try:
            return sources.read(src)
        except sources.SourceError as e:
            raise ToolError(str(e)) from None
    raise ToolError("Give data_path or csv_text")


def _spec(args: dict) -> dict:
    if args.get("rules_yaml"):
        text = args["rules_yaml"]
    elif args.get("rules_path"):
        text = _inside(args["rules_path"]).read_text(encoding="utf-8")
    else:
        raise ToolError("Give rules_path or rules_yaml")
    try:
        spec = yaml.safe_load(text)
        rules.validate_spec(spec)
    except (yaml.YAMLError, ValueError, KeyError, TypeError, AttributeError) as e:
        raise ToolError(f"The rules file has a problem: {e}") from None
    return spec


def _run(args: dict) -> tuple[dict, dict]:
    spec = _spec(args)
    df = _data(args)
    as_of = date.fromisoformat(args["as_of"]) if args.get("as_of") else date.today()
    try:
        res = rules.run(df, spec, as_of)
    except KeyError as e:
        raise ToolError(f"A rule refers to a column that isn't in the data: {e}") from None
    res["trust"] = trust.classify(res, spec["asset"].get("personal_data_columns"))
    res["route"] = pathway.route(spec["asset"])
    return spec, res


def _summary(res: dict) -> dict:
    return {"asset": res["asset"].get("id"), "as_of": res["as_of"], "rows": res["rows"],
            "rules_met": res["rules_met"], "rules_total": res["rules_total"],
            "trust_level": res["trust"]["level"], "sharing": res["trust"]["sharing"], "route": res["route"]["route"],
            "issues": res["issues"],
            "rules": [{"id": r["id"], "description": r["description"], "dimension": r["dimension"], "performance": r["performance"],
                       "target": r["assessment"]["target"], "priority": r["assessment"]["priority"],
                       "failing_examples": r.get("examples", [])[:3]} for r in res["results"]],
            "dimensions": {k: v["mean_performance"] for k, v in res["dimensions"].items()}}


def call_tool(name: str, args: dict) -> dict:
    args = args or {}
    if name == "check_data":
        return _summary(_run(args)[1])
    if name == "suggest_rules":
        df = _data(args)
        spec = profile.suggest(df, {"id": args.get("asset_id") or "my-asset"})
        return {"rules_yaml": profile.to_yaml(spec, args.get("data_path") or "the data"), "note": "Draft only: review every rule."}
    if name == "validate_rules":
        spec = _spec(args)
        return {"valid": True, "rules": len(spec["rules"]), "asset": spec["asset"].get("id")}
    if name == "assess_pack":
        try:
            return packs.assess(args["pack"], _run(args)[1])
        except ValueError as e:
            raise ToolError(str(e)) from None
    if name == "crosswalk":
        try:
            return packs.convert(_run(args)[1], args["to"])
        except ValueError as e:
            raise ToolError(str(e)) from None
    if name == "score_issue":
        try:
            return framework.assess(int(args["importance"]), int(args["impact"]), float(args["performance"]),
                                    args.get("target"), args.get("target_policy", "low")).to_dict()
        except (ValueError, TypeError) as e:
            raise ToolError(str(e)) from None
    if name == "list_frameworks":
        f = (args.get("filter") or "").lower()
        return [{k: x.get(k) for k in ("id", "name", "publisher", "jurisdiction", "sector", "type", "year", "url", "dimensions")}
                for x in packs.registry() if not f or f in json.dumps(x).lower()]
    if name == "list_packs":
        return [{"id": p["id"], "name": p["name"], "summary": p.get("summary", "")} for p in packs.list_packs()]
    if name == "explore_knowledge":
        from . import graph
        g = graph.build()
        ids = {n["id"] for n in g["nodes"]}
        pick = lambda v: v if v in ids else ((graph.find(g, v, 1) or [{}])[0].get("id"))
        if args.get("from") and args.get("to"):
            a, b = pick(args["from"]), pick(args["to"])
            if not (a and b):
                raise ToolError("Couldn't find one of those concepts. Try 'query' first.")
            return {"from": a, "to": b, "path": graph.path(g, a, b)}
        if args.get("node"):
            n = pick(args["node"])
            if not n:
                raise ToolError("No concept matches that node.")
            return {"node": next(x for x in g["nodes"] if x["id"] == n),
                    "relationships": [{"property": r["property"], "direction": r["direction"], "id": r["node"]["id"], "label": r["node"]["label"]}
                                      for r in graph.neighbours(g, n)]}
        if args.get("query"):
            return [{"id": n["id"], "type": n["type"], "label": n["label"], "definition": n.get("definition", "")} for n in graph.find(g, args["query"])]
        return {"stats": g["stats"] | {"dangling": None}}
    if name == "weave_metadata":
        from . import weaver
        try:
            return weaver.weave(args["record"], args.get("from"))
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            raise ToolError(f"Couldn't read the record: {e}") from None
    if name == "check_contract":
        from . import contracts
        out = {"problems": contracts.validate_odcs(args.get("contract"))}
        if isinstance(args.get("previous"), dict):
            out["diff"] = contracts.diff_odcs(args["previous"], args["contract"])
        return out
    if name == "playbook":
        from . import playbook
        if args.get("workspace"):
            ws = _inside(args["workspace"])
            if not ws.is_dir():
                raise ToolError("workspace must be a folder made by 'dqkit playbook init'")
            return playbook.status(ws)
        try:
            return playbook.guide(args.get("stage"))
        except ValueError as e:
            raise ToolError(str(e)) from None
    if name == "list_checks":
        return {"checks": sorted(rules.CHECKS) + ["in_valueset"], "identifier_schemes": list(rules.IDENTIFIER_SCHEMES),
                "value_sets": sorted(p.stem for p in rules.VALUESET_DIR.glob("*.csv"))}
    raise ToolError(f"Unknown tool {name!r}")


def handle(msg: dict):
    """Handle one JSON-RPC message. Returns the response, or None for notifications."""
    mid, method = msg.get("id"), msg.get("method")
    if mid is None:
        return None  # notifications (for example notifications/initialized) need no reply
    def ok(result):
        return {"jsonrpc": "2.0", "id": mid, "result": result}
    if method == "initialize":
        return ok({"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}},
                   "serverInfo": SERVER_INFO,
                   "instructions": "Read-only data quality tools. Pass rules as YAML and data as a path or CSV text. "
                                   "Results are deterministic; present them to a person, who decides what to do."})
    if method == "ping":
        return ok({})
    if method == "tools/list":
        return ok({"tools": TOOLS})
    if method == "tools/call":
        p = msg.get("params") or {}
        try:
            out = call_tool(p.get("name"), p.get("arguments") or {})
            return ok({"content": [{"type": "text", "text": json.dumps(out, ensure_ascii=False, default=str)}],
                       "structuredContent": out if isinstance(out, dict) else {"items": out}, "isError": False})
        except ToolError as e:
            return ok({"content": [{"type": "text", "text": str(e)}], "isError": True})
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {method}"}}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}}) + "\n")
            sys.stdout.flush()
            continue
        resp = handle(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False, default=str) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
