# Value sets

Lists of allowed values for the `in_valueset` check. Each CSV has `code`, `label` and `source`.

| File | What it is | Note |
|---|---|---|
| `uk_nations.csv` | The four UK nations with their GSS country codes | |
| `gss_uk_groupings.csv` | GSS codes for the United Kingdom, Great Britain, and England and Wales | |
| `english_regions.csv` | The 9 regions of England (E12) with their GSS codes | Regions apply to England only. |
| `gss_entity_codes.csv` | The first 3 characters of a GSS code (the entity code) for the most-used geographies in the 4 nations | Use with a column holding the first 3 characters of each area code, to check that every code is the expected kind of area (for example only E06, E07, E08, E09 and W06 for local authorities). Check the ONS Register of Geographic Codes for the full and current list. |
| `ethnic_group_ew_2021_high_level.csv` | The 5 high-level ethnic groups used in Census 2021 for England and Wales | Scotland and Northern Ireland use different classifications. Don't apply this list to UK-wide data. The codes A to E are local to this file, not official codes. |

Use in a rules file:

```yaml
- {id: R7, check: in_valueset, column: ethnic_group, valueset: ethnic_group_ew_2021_high_level, match: label}
```

`match` is `label` (default) or `code`. Add a value set by adding a CSV here. Prefer published
GSS harmonised standards, and always record the source.

Geography codes change (boundary reviews, new authorities). Lists of individual areas, such as local
authorities, are better downloaded fresh from the ONS Open Geography Portal than kept here, so this
folder holds only lists that rarely change. The weekly maintenance task checks the source notes.
