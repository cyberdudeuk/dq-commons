# Integrations

Ways to run the Commons checks where teams already work. Every option runs inside your own environment:
your data is never sent to the Commons.

| Folder | For | Status |
|---|---|---|
| `fabric/` | A Microsoft Fabric, Synapse or Databricks notebook that checks a lakehouse table and appends results to a table for Power BI or alerts | Written and unit-tested logic; not yet run in a live tenant |
| `http-api/` | A small HTTP service (Azure Function) that Power Automate, Logic Apps or any workflow tool can call with a CSV and a rules file | Written; the `check()` logic is tested in `tests/test_integrations.py`; not yet deployed |
| `config.yaml` | Where the Commons repository, Jira and Confluence connect (secrets live in GitHub, never here) | In use |
| `ndl-mcp-domain.json` | The Commons as a domain for Model Context Protocol (MCP) clients | In use |

Neither integration returns example failing values, because they may contain personal data. Look at examples
only where the data already lives.

Tell us how an integration works for you, or what is missing, through the
[contact form](https://github.com/cyberdudeuk/dq-commons/issues/new?template=0-contact.yml).
