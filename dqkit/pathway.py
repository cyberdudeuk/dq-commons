"""Which DQAP route fits this asset? A coded version of the 2023 Data Quality Assessment Decision Tree.

The route separates data you produce from data you receive, and asks whether you can change its
structure. It codes a decision tree used in the government data quality community (2023). The answers decide
whether you fix gaps at source, enrich the data yourself, or record and communicate limitations.

Asset fields used (all optional):
  source: internal | external
  influence: true | false          # can you influence the data structure? (external only)
  fields_adequate: true | false    # does the data have the fields the quality use cases need?
  can_enrich: true | false         # can you add, generate or enrich fields yourself?
"""
from __future__ import annotations


def route(asset: dict) -> dict:
    source = asset.get("source", "internal")
    influence = bool(asset.get("influence", source == "internal"))
    adequate = asset.get("fields_adequate", True)
    can_enrich = asset.get("can_enrich", False)
    steps = ["Determine and define the use cases and stakeholders", "Assess the data structure"]
    if adequate is False:
        if source == "internal" or influence:
            steps += ["Tell stakeholders or suppliers what fields the quality use cases need",
                      "Work with them to add the fields, or understand and record the limitations",
                      "Record any additions in the provenance information"]
        elif can_enrich:
            steps += ["Add the fields the quality use cases need", "Record the additions in the provenance information"]
        else:
            steps += ["Communicate the limitations to stakeholders, and record them in the metadata and the DQAP"]
    steps += ["Define domain-appropriate data quality assessment parameters (the rules file)",
              "Record them in the DQAP", "Measure data quality against the planned parameters",
              "Store and visualise the results in an accessible format",
              "Check the assessment meets its stated aims; if not, revise the parameters",
              "Communicate the results to stakeholders", "Make changes to improve data quality where appropriate",
              "Repeat at a frequency that meets the original requirements"]
    if source == "external" and not influence:
        label = "External data, no influence: assess, caveat and communicate"
        responsibility = "Fixes sit with the supplier. Your job is to measure, record limitations and tell users."
    elif source == "external":
        label = "External data, some influence: assess and work with the supplier"
        responsibility = "Agree fixes with the supplier and record them in the DQAP actions."
    else:
        label = "Internal data: assess and fix at source"
        responsibility = "Fix root causes in your own processes and systems."
    return {"route": label, "responsibility": responsibility, "steps": steps,
            "source": source, "influence": influence,
            "basis": "Data Quality Assessment Decision Tree (government data quality community, July 2023)"}
