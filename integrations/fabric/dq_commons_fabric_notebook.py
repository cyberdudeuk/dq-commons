# Microsoft Fabric (or Azure Synapse / Databricks) notebook: run Commons data quality rules on a lakehouse table.
# Backlog BL-09, issue #9. Paste into a notebook cell by cell (each "# %%" is a cell), or upload as a .py notebook.
#
# What it does, in plain English:
#   1. Installs the open Commons toolkit (dqkit) into the notebook session.
#   2. Reads a table from your lakehouse and a rules file (YAML) from the lakehouse Files area.
#   3. Runs the rules. Your data stays in your tenant: nothing is sent to the Commons.
#   4. Writes one row per rule per run to a results table, ready for a Power BI report or a Data Activator alert.
#
# Before you start: a lakehouse attached to the notebook, a table to check, and a rules file. Draft the rules on
# https://cyberdudeuk.github.io/dq-commons/check.html or start from rules/library/*.yaml.
# Not yet tested in a live Fabric tenant: tell us how it goes through the contact form.

# %% 1. Install the toolkit (pin a released version for repeatable results)
# %pip install "git+https://github.com/cyberdudeuk/dq-commons@main"

# %% 2. Settings: change these
TABLE = "claims_monthly"                       # lakehouse table to check
RULES_PATH = "/lakehouse/default/Files/dq/rules/claims_monthly.yaml"
RESULTS_TABLE = "dq_results"                   # created on first run, appended after
MAX_ROWS = 2_000_000                           # sample above this size; the toolkit runs in memory

# %% 3. Run
import datetime as dt

import pandas as pd
import yaml
from dqkit import rules

spark_df = spark.table(TABLE)  # noqa: F821 - "spark" is provided by the notebook
n = spark_df.count()
if n > MAX_ROWS:
    spark_df = spark_df.sample(fraction=MAX_ROWS / n, seed=42)
df = spark_df.toPandas().astype("string").astype(object).where(lambda d: d.notna(), None)  # the toolkit reads text, like a CSV

with open(RULES_PATH, encoding="utf-8") as f:
    spec = yaml.safe_load(f)
res = rules.run(df, spec, dt.date.today())
print(f"{res['rules_met']} of {res['rules_total']} rules met on {res['rows']} rows" + (" (sampled)" if n > MAX_ROWS else ""))

# %% 4. Save results (one row per rule per run)
rows = [{"run_at": dt.datetime.utcnow().isoformat(timespec="seconds"), "table": TABLE, "asset": res["asset"].get("id", TABLE),
         "rule": r["id"], "check": r["check"], "dimension": r["dimension"], "issue_type": r["issue_type"],
         "checked": r["checked"], "passed": r["passed"], "performance": r["performance"],
         "target": r["assessment"]["target"], "meets_target": r["assessment"]["meets_target"],
         "priority": r["assessment"]["priority"] or "", "sampled": n > MAX_ROWS} for r in res["results"]]
spark.createDataFrame(pd.DataFrame(rows)).write.mode("append").saveAsTable(RESULTS_TABLE)  # noqa: F821
# Examples of failing values are NOT saved, because they may contain personal data. Look at them in the notebook only:
# [r["examples"] for r in res["results"] if not r["assessment"]["meets_target"]]
