# Metadata Weaver: assessment and design

## Should the metadata crosswalk become a "weaver"?

**Yes.** The Metadata Rosetta (61 concepts across 8 standards) explains how standards line up. That's useful for
specialists, but people still retype the same record into each catalogue, and they only find gaps after publishing.

| Question | Crosswalk (Rosetta) | Weaver |
|---|---|---|
| What does it give you? | A table: concept X is `dct:title` here and `name` there | The record itself, written in every standard |
| Who can use it? | Metadata specialists | Anyone who can paste a record |
| When do gaps show? | Never, unless someone compares by hand | Before publishing, per standard, plus the 13 CDA properties |
| Source of truth | None: copies drift | One canonical record, re-woven on every change |
| Can others replicate it? | Copy the table | Run the same open code: CLI, Python, browser, GitHub Actions or an AI agent (MCP) |

## What it does now (v1.2)

- **Reads:** W3C DCAT (JSON-LD), schema.org Dataset (JSON-LD), CKAN packages (including API responses), ODCS v3 contracts,
  CSV on the Web (CSVW) table metadata and Frictionless Data Packages (`datapackage.json`).
- **Writes:** DCAT v3, schema.org, CKAN, an ODCS contract skeleton, GeoDCAT-AP and StatDCAT-AP.
- **Profile checks:** simplified must/should shapes for DCAT-AP 3, GeoDCAT-AP, StatDCAT-AP and the UK critical data asset
  properties, plus ISO 8601 dates (`profiles` in the result). Validate with the official SHACL shapes before publishing (D-WV-02).
- **Reports:** filled and missing fields for each standard, fields a standard can't carry ("not carried"), and the 13
  critical data asset metadata properties with pass, partial or missing.
- **Contract change check:** validates an ODCS contract and lists changes between versions, which ones break consumers,
  and the semantic version to use.
- **Never invents:** missing fields stay missing. ODCS needs an id and version, so the skeleton uses visible placeholders.
- **Same answer everywhere:** the Python and browser versions are checked case by case (`scripts/parity_check.py`).

## Run it

```
python -m dqkit weave record.json --report       # gaps and CDA coverage
python -m dqkit weave record.json --to dcat      # one output
python -m dqkit contract-check new.yaml --against old.yaml   # exits 1 if the version bump is too small
```

From an AI agent: the MCP tools `weave_metadata` and `check_contract` (read-only).

## Design

- One canonical record of 22 fields. Each field names its Metadata Rosetta concept and, where relevant, its CDA property.
- Security classification and expiry have no DCAT property, so DCAT output uses the Commons vocabulary (`dqc:`).
- Contact points should be a team or role. The portal warns against personal data.

## Roadmap (vote on Help us build this)

1. UK metadata standard profile, aligned with the cross-government metadata exchange model.
2. GeoDCAT-AP and StatDCAT-AP outputs.
3. CSVW and Frictionless Data Package inputs.
4. SHACL validation of outputs against published application profiles.
5. Batch weaving of a whole catalogue, with a gap report per publisher.
