# Public sector rule library

Starting rules for the kinds of data that turn up across government and the wider public sector.
Copy a file, rename the columns to match your data, delete what doesn't apply, and set
`importance` for your asset. Every rule is a normal dqkit rule, so it also runs in the browser
checker and exports to Great Expectations and R `validate`.

| File | For | Checks it uses |
|---|---|---|
| `person.yaml` | Records about people (health, benefits, education, justice) | NHS number and National Insurance number check rules, date of birth, postcode, ethnic group value set, defaulted characteristics, quality by group |
| `address.yaml` | Addresses and property | UPRN, postcode, completeness |
| `organisation.yaml` | Companies, charities, schools, NHS organisations | Company number, charity number, school URN, ODS code, LEI |
| `geography.yaml` | Statistics by area | GSS area codes, UK nation names, one row per area and period |
| `publication.yaml` | Published statistics and open data files | Measure labelled with unit, freshness, gaps in the series, totals |

## Identifier schemes (`check: identifier`)

| Scheme | What is checked | Strength |
|---|---|---|
| `nhs_number` | 10 digits and the modulus 11 check digit; spaces and hyphens allowed | Check digit |
| `nino` | National Insurance number format, with HMRC's excluded letters and prefixes; spaces allowed | Format |
| `uk_postcode` | Royal Mail postcode format, upper case, with or without the space | Format |
| `uprn` | Unique Property Reference Number: 1 to 12 digits, above zero | Format |
| `gss_code` | ONS GSS geography code: a nation letter and 8 digits | Format |
| `company_number` | Companies House: 8 digits, or 2 letters and 6 digits | Format |
| `charity_number` | England and Wales (6 or 7 digits), Scotland (SC + 6 digits), Northern Ireland (NIC + 6 digits) | Format |
| `school_urn` | DfE unique reference number: 6 digits | Format |
| `ods_code` | NHS Organisation Data Service code: 3 to 6 capital letters or digits | Format |
| `lei` | Legal Entity Identifier (ISO 17442): 20 characters and the ISO 7064 check digits | Check digit |

"Format" means the value looks right. It can't prove the identifier exists or belongs to the
right person, place or organisation. To prove that, match against the reference register (for
example AddressBase, the ONS Code History Database, or Companies House) as an `accuracy` rule.
