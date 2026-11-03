# Illustrative example: issue ageing and escalation

This example is **illustrative**. It re-measures today's NDL air quality chart file as if on three
dates (14 April, 14 July and 14 October 2026), to show how the kit tracks issues over time.

- April: the file is up to date, so every rule meets its target.
- July: 2025 statistics would normally be out, so the freshness rule (R4) fails: a High issue,
  to fix within 1 measurement cycle.
- October: R4 has been open for 2 cycles, longer than the issues framework allows, so the
  workbook's Issues log says "Overdue: escalate to data owner and governance board".

Re-create it:

```
for d in 2026-04-14 2026-07-14 2026-10-14; do
  python -m dqkit check assessments/ndl/chart-data/environment__air-quality.csv rules/ndl/air-quality.yaml \
    --as-of $d --out examples/illustrative-escalation/out --history examples/illustrative-escalation/history \
    --workbook --case-study
done
```

Files: `out/*.DQAP.xlsx` (see the Issues log and Operations tabs) and `out/*.case-study.md` / `.docx`
(a draft with the before-and-after table).
