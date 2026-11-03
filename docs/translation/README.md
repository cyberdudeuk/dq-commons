# Translation pack: Welsh and community languages (BL-06 issue #6, BL-23 issue #23)

Ready for a translator. Translation itself needs qualified people, so both issues stay open until a reviewed
translation is in.

## What to translate first

1. **Welsh (cy).** Welsh public bodies have duties under the Welsh Language Standards, and the Welsh Language
   (Wales) Measure 2011 gives Welsh equal status in Wales. Start with: the menu, the Home page, Check your data, the
   accessibility statement and privacy notice, the contact form, and every page's "In short" summary.
2. **Community languages.** Choose from evidence, not guesswork: the most-spoken main languages other than English
   and Welsh in Census 2021 (England and Wales), Scotland's Census 2022 and the Northern Ireland Census 2021, and
   requests through the contact form. The "In short" summaries are the best first step: short, plain and high value.

## How

```bash
python scripts/export_strings.py --lang cy --stats   # words to quote for
python scripts/export_strings.py --lang cy           # writes translation/cy.csv
```

The CSV has one row per piece of visible text from the page sources, the menu and the plain English summaries
(about 1,550 strings and 14,400 words today). Lists drawn from the knowledge base (frameworks, glossary, courses) are
not included yet: translate pages first, then the glossary in `knowledge/ontology.yaml`.

Translators fill the language column and add notes. Keep the meaning, not the word order; keep the plain English
style. Don't translate names of standards, organisations or code. Use the Welsh Government's terminology resources and
the Welsh Language Commissioner's guidance for Welsh, and an agreed glossary for data terms in every language.

## Rules

- No machine translation is published without review by a qualified translator.
- Every translated page says when it was last checked against the English, and links to the English.
- The language switch uses `lang` attributes so screen readers pronounce text correctly.
- Users can ask for a page in their language through the contact form.
