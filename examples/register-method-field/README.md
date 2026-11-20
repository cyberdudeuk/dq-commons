# Worked example: a field can be valid and still incomplete

This example measures a real register, read on 20 November 2026: the
[Register of information sharing agreements](https://www.digital-economy-act-register.data.gov.uk) under the Digital
Economy Act 2017, Part 5. It shows a quality problem that the usual completeness and validity checks pass straight
over.

## What the register records

Each of its 667 agreements records exactly one *information sharing method*, from nine values. 194 agreements are
active; 11 record "API", 6 of them active.

## What the checks found

| Rule | What it asks | Result |
|---|---|---|
| R1 to R2 | The fields are there, and each agreement is recorded once | Met |
| R3 | Every agreement has a method (completeness) | Met: 667 of 667 |
| R4 | The method is one of the nine values (validity) | Met: 667 of 667 |
| R5 | Every agreement is active or ended | Met |
| **R6** | **When an agreement's own text says data moves through an API, its method says so too (consistency)** | **Not met: 664 of 667 (99.55% against a 99.8% target), High priority** |

The three agreements that fail R6 are 205, 284 and 663, all for the Warm Home Discount helpline. Their methods are
trusted partner transfer, encrypted hardware and secure file transfer. Yet each one's disclosed-information text says
electronic access to DWP's Citizen Application Programming Interface (CAPI) will also be enabled.

## Why it matters

- **Every value is valid, and the field is still incomplete.** A field that holds one value can't record a second
  route. So any count of "agreements that use an API" taken from it is a floor, not a measure.
- **R6 only catches the cases where the text happens to say so.** Others may exist, so this finding is the minimum.
- **Fixing the records alone won't do it, because the model is the cause.** The fix belongs at the source: the
  register's owner could let an agreement record more than one method and link the API catalogue entry it uses. A
  matching change to DCAT-AP-UK is proposed in
  [cyberdudeuk/dcat-ap-uk#34](https://github.com/cyberdudeuk/dcat-ap-uk/issues/34).
- **The register counts agreements, not volume.** The largest flows, such as payroll earnings for Universal Credit,
  run under other legal gateways and aren't in it.

The kit's suggested trust level and Q-FAIR ratings in `out/` are its own automated suggestions for an external
source the Commons can't influence. They are not a judgement of the register's publisher.

## Re-create it

```
mkdir -p pages && for i in $(seq 1 667); do
  curl -sS -o pages/$i.html https://www.digital-economy-act-register.data.gov.uk/agreements/$i
done
python3 -I scripts/read_dea_register.py --pages pages --out examples/register-method-field/data/dea-agreements.csv
python -m dqkit check examples/register-method-field/data/dea-agreements.csv \
  examples/register-method-field/rules/dea-register.yaml --as-of 2026-11-20 \
  --out examples/register-method-field/out --workbook --case-study
```

The data isn't kept in this repository, which holds no Open Government Licence content (decision D-LIC-01). Run
the commands to read it again. The reader prints the CSV's SHA-256. For the 20 November 2026 read it was
`7245d4cfb92f2eef533a215017b54e3f33005a2268cd90716760c255ad64f388`. The register changes over time, so a later read
will differ.

## Files

- `data/dea-agreements.csv` (made by the commands above, not committed): the register's own fields, with two derived
  0/1 columns, `method_is_api` and `text_mentions_api`. Contact details are not copied.
- `rules/dea-register.yaml`: the six rules.
- `out/`: results, W3C DQV metadata, DQAP rows, the DQAP workbook and a draft case study.

## Licence and attribution

The register is published under the
[Open Government Licence v3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/). Its data
isn't copied here. The results in `out/` record only counts, row numbers and the two derived 0/1 values, and this
example is the Commons' own content under CC BY 4.0.

## Where else this appears

- [NDL PubSec MCP](https://cyberdudeuk.github.io/ndl-pubsec-mcp/#exchanges) maps data exchanges by journey, and
  explains the register's figures and their limits.
- The [GitHub Repos Asset Catalogue](https://cyberdudeuk.github.io/github-repos-asset-catalogue/) API view links
  government APIs to those exchanges.
