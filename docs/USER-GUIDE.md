# Public Sector Data Quality Commons: portal user guide

The Commons is a free, open place to check, improve and talk about the quality of public sector data. You don't need to install anything or know how to code. Your data never leaves your browser.

## Getting started in 5 minutes

1. Open the **Home** page and choose the task closest to yours.
2. Press **Take the tour** on any page for a guided walk-through. You can leave the tour at any time with Escape.
3. Try **Check data**: open a CSV file (the Python toolkit also reads Excel, ODS, JSON, Parquet, SQL and CKAN), choose rules from the library, and press Run.
4. Read your results: each rule shows a pass rate, its target, and what to do next.
5. Save your rules file so you can run the same checks again next month.

## The menu

| Group | Pages | Use it to |
|---|---|---|
| Start | Home (news, spotlight, latest), About, User guide, Accessibility and privacy | Find your way, see what the Commons is for |
| Do | Check your data, Maturity, AI assistant, Metadata Weaver, Pipeline | Measure quality, export data contracts, assess and benchmark maturity, draft rules, publish metadata in every standard, automate |
| Know | Frameworks and standards, Learn, Skills and training, Knowledge map, AI for data quality, Issues framework, Tooling, Library and knowledge base | Compare frameworks, learn, check your skills and find training, explore every concept and how it connects, use AI safely, prioritise, choose tools, read and publish resources |
| Govern | Buying and suppliers, Legacy and modernisation, Interoperability and standards | Put data quality into contracts, migrate without data debt, join data up |
| Scenarios | All scenarios, UK and the world, National Data Library, Critical data asset baseline | Work through a specific policy, sector, nation, jurisdiction or platform |
| Community | Community, Media centre, Events, Surveys and commissions, Case studies, Help us build this, Operating model | Contribute, share posts and podcasts, run surveys, ask for help, vote on the roadmap, co-design, contact us |

## Common tasks

### Check a dataset
Go to **Check data**. Open your file, add rules (or press **Suggest rules**), then **Run**. Identifier checks cover NHS numbers, National Insurance numbers, postcodes, UPRNs, GSS codes and more. Nothing is uploaded.

### See how a framework applies to you
Go to **Frameworks**. Filter by nation, sector or type. Each entry shows its dimensions and how they map to the kit's dimensions. The clause table breaks policies down line by line and shows where devolved and international equivalents agree or differ.

### Assess your organisation's maturity
Go to **Maturity**. Choose the statement that best fits you for each of 8 themes. You get a level per theme (Beginning to Mastering) and next steps with links. Results stay in your browser unless you choose to download them.

### Share rules as a data contract
On **Check your data**, under "Share the rules as a data contract", choose ODCS, Table Schema, CSVW, Great Expectations or R validate. You can also load a contract as rules.

### Put data quality into a supplier contract
Go to **Buying and suppliers**. Choose clauses in the builder (the "must" clauses are a sensible floor), add your organisation's name, and copy the schedule for your commercial and legal teams. It is illustrative drafting, not legal advice.

### Check a migration
Go to **Legacy and modernisation**: assess your data debt, follow the migration gates, and use **Reconcile** to compare the data before and after.

### Publish metadata in every standard
Go to **Metadata Weaver**. Paste a DCAT, schema.org, CKAN or ODCS record. You get all four back, the gaps for each, and the 13 critical data asset properties. Fill gaps in the table and the outputs update.

### Check a data contract change
On **Metadata Weaver**, under "Contract change check", paste the old and new ODCS contracts. You see what changed, what breaks consumers, and the version number to use.

### Explore concepts and how they connect
Go to **Knowledge map**. Search for any concept: it appears in the middle, with everything it links to around it. Choose any one to move there; your trail lets you step back. Use **Trace the path** to see how two concepts connect, or the tabs for the glossary, thesaurus, data dictionary, taxonomies, ontology and lineage.

### Find events and training
**Events** lists conferences, workshops and courses, as a list or a month calendar; add any to your calendar. **Skills and training** lets you rate your skills against your role and download a development plan.

### See what's new
Press **What's new** in the top bar. Each release lists what's new, changed and fixed. New and updated pages are flagged in the menus.

### Contact the team
Go to **Help us build this** and use the contact form. We never show an email address and you don't need to give yours. Replies appear on the same page when you return signed in.

### Learn
Go to **Learn**. Pick your role to see a pathway. Tutorials take 10 to 30 minutes each. The glossary explains every term used in the Commons.

### Start from your role
Open **Start > For your role** and choose your role. You'll see what you need, decisions coming up, what to watch, measures to ask for and the gaps that affect you. The CDO Council brief and the gap register are on the same page.

### Run a data quality cycle on a critical data asset
Open **Govern > Data quality management playbook**. Work through the eight stages in order; tick the checklist as you go (ticks stay in your browser). Download the CSV templates for your register, rules, issue log, action plan, quality statement and annual review. You can download a progress report, or run the same playbook from the toolkit with `python -m dqkit playbook init`. Outside UK central government, use the "Use it anywhere" table to swap in your own terms, and "Where it applies" to see your framework.

### Use AI to improve data quality
Read the **AI for data quality** section on the Learn page: principles, use cases, questions to ask vendors, worked examples and how AI tools become part of the shared toolkit. The **AI assistant** drafts rules from plain English; always check what it drafts.

### Contribute or ask for help
Go to **Community**. Add a case study or insight, take or run a survey, or request help (a commission). To vote on the wishlist or see the roadmap, go to **Help us build this**. If a page can't save in your browser, use the linked GitHub forms instead.

## Accessibility

The portal aims to meet WCAG 2.2 AA. It works with keyboard only, screen readers and up to 400% zoom, and respects reduced motion settings. If something doesn't work for you, tell us through the contact form on Help us build this and we'll reply within 1 working day.

## Privacy

- Data you check stays in your browser.
- Surveys never ask for your name or email. Results are shown as totals only, and totals under 5 are hidden.
- Contributions are moderated before they are public.

## Getting help

See the **Operating model** page for support tiers. Short version: try the guide and tours first, then the community, then the service desk.
