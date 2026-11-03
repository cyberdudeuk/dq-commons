"""A small HTTP service that runs Commons rules, for Power Automate, Logic Apps or any workflow tool (issue #9).

POST /api/check   body: {"csv": "<CSV text>", "rules": "<rules YAML text>", "as_of": "2026-11-03" (optional)}
                  reply: the toolkit summary (rules met, issues by priority, results per rule) without example
                  values, so no personal data comes back through the workflow tool.

Runs as an Azure Function (Python v2 programming model). Deploy it inside your own tenant so data never leaves it.
Power Automate: add an "HTTP" action (premium) after "Get file content", POST to the function URL with the file
text and your rules, then use "Parse JSON" on the reply and branch on rules_met / issues.
Not yet tested in a live tenant: tell us how it goes through the contact form.
"""
from __future__ import annotations

import datetime as dt
import io
import json

import azure.functions as func  # pip install azure-functions
import pandas as pd
import yaml
from dqkit import rules

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)  # needs a function key: keep it in a connection, not in a flow


def check(payload: dict) -> dict:
    """The logic, separate from Azure so it can be tested anywhere."""
    df = pd.read_csv(io.StringIO(payload["csv"]), dtype=str, keep_default_na=False).replace({"": None})
    spec = yaml.safe_load(payload["rules"])
    rules.validate_spec(spec)
    as_of = dt.date.fromisoformat(payload["as_of"]) if payload.get("as_of") else dt.date.today()
    res = rules.run(df, spec, as_of)
    for r in res["results"]:
        r.pop("examples", None)  # may contain personal data
    return res


@app.route(route="check", methods=["POST"])
def http_check(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        if len(body.get("csv", "")) > 50_000_000:
            return func.HttpResponse(json.dumps({"error": "File over 50 MB: use the Fabric notebook instead"}), status_code=413, mimetype="application/json")
        return func.HttpResponse(json.dumps(check(body)), mimetype="application/json")
    except (ValueError, KeyError, yaml.YAMLError) as e:
        return func.HttpResponse(json.dumps({"error": str(e)}), status_code=400, mimetype="application/json")
