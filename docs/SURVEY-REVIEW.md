# Review of the Cross-Government Data Quality Solutions Survey (before launch)

Source: GDS Data Management Team, Microsoft Forms design, October 2026 (crosswalk source S11).
This review checks the survey against the aims of the tooling review it supports (S10), the DAM
policy, UK GDPR and good survey practice. The survey is well structured: organisation questions
are asked once, the solution section repeats, and branching keeps it short for one-tool users.
The fixes below are small and are best made before launch, because answers collected now can't be
re-segmented later.

## Must fix before launch

| # | Issue | Fix |
|---|---|---|
| 1 | Q2, Q3 and Q5 collect name, role and email with no privacy notice, lawful basis or retention period (UK GDPR Articles 13–14) | Add a short privacy notice at the start. Make name and email optional, and ask for them only if Q108 = Yes (may we contact you). Turn off Forms' automatic name and email capture if contact isn't needed. |
| 2 | No organisation type or size. The tooling review wants to know "how tooling usage differs according to organisational needs, scale and maturity". | Add organisation type (ministerial department, non-ministerial department, ALB, local authority, NHS body, devolved administration, other) and headcount band. Use a dropdown for organisation name, so answers can be joined to the CDA register. |
| 3 | No link to the DAM policy outcomes. Nothing asks how many CDAs the tool covers, which DQAP steps it supports, or whether it produces the CDA return. | Add 3 questions per solution: number of CDAs covered (bands); DQAP steps supported (the 7 steps, multi-select); does it produce evidence for the CDA return (yes, partly, no). |
| 4 | The review says it will cover "how widely the solution is used", but no question asks this | Add: number of users (bands) and share of the organisation's critical data covered (bands) |
| 5 | Q12 and Q37 use a maturity scale (Very early … Mature) that doesn't match the Data Maturity Assessment for Government (Beginning, Emerging, Learning, Developing, Mastering) | Use the DMA levels, so answers can be compared with departments' DMA results |
| 6 | Q32 runs 1 = very easy to 5 = very difficult. Q23 and Q31 run 1 = worst to 5 = best. | Reverse Q32 (1 = very difficult, 5 = very easy), or label it clearly in the results. `dqkit survey` marks it as reversed. |

## Should fix

| # | Issue | Fix |
|---|---|---|
| 7 | The Q6 tool list has no open-source or in-house options, except Soda. The review itself says many organisations start with SQL, Python, R, Excel or Power BI. | Add: Great Expectations, Soda Core (open source), dbt tests, R (validate, pointblank), in-house scripts (SQL, Python, R), Excel, Power BI, Databricks data quality, Microsoft Fabric data quality |
| 8 | No questions on accessibility, open standards or exit | Add: usable with assistive technology (yes, partly, no, don't know); can export results in an open format (DQV, CSV, JSON); how hard leaving would be (1–5) |
| 9 | Q15 "prerequisites" mixes in features ("AI-assisted functionality", "Data enrichment") | Replace them with prerequisites: data ownership in place; critical data assets identified; agreed rules; supplier support |
| 10 | Q20 ranks "least value" over all 10 features, which forces a full ranking | Make it a multi-select of up to 3 |
| 11 | Q30 lists cost categories but gives no cost scale, so value for money can't be compared | Add annual cost bands (none; under £10k; £10k–£50k; £50k–£250k; £250k–£1m; over £1m; prefer not to say) |
| 12 | Q13 lists "Data Quality Action Plan" after "Other" | Move it before "Other" |

## Respondent burden

109 questions if three solutions are assessed. A rough estimate (not tested): 25–40 minutes for one solution, more for
three. Consider a short form (Q6 inventory plus Q8, Q16, Q25, Q31, Q36 per solution) for people
who can't spare the time, and say how long it takes at the start.

## Publishing results safely

Counts under 5 for a solution, or for an organisation type, can identify the organisation.
Suppress or group them before sharing results with the Data Management Community. `dqkit survey`
puts this warning in its summary.

## Analysing the results

```
python -m dqkit survey "Cross-Government Data Quality Solutions Survey.xlsx" --out survey-results
```

This writes `solutions_long.csv` (one row per organisation and solution), `organisations.csv`,
`summary.json` and `summary.md`. Name, role and email are removed on load and never written out.
It works with or without S1, S2 and S3 prefixes on the repeated questions.
