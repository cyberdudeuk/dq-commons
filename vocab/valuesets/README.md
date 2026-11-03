# Value sets

Lists of allowed values for the `in_valueset` check. Each CSV has `code`, `label` and `source`.

| File | What it is | Note |
|---|---|---|
| `uk_nations.csv` | The four UK nations with their GSS country codes | |
| `ethnic_group_ew_2021_high_level.csv` | The 5 high-level ethnic groups used in Census 2021 for England and Wales | Scotland and Northern Ireland use different classifications. Don't apply this list to UK-wide data. The codes A to E are local to this file, not official codes. |

Use in a rules file:

```yaml
- {id: R7, check: in_valueset, column: ethnic_group, valueset: ethnic_group_ew_2021_high_level, match: label}
```

`match` is `label` (default) or `code`. Add a value set by adding a CSV here. Prefer published
GSS harmonised standards, and always record the source.
