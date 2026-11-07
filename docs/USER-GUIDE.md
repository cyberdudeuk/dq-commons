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
| Start: Get started | Home, New to GitHub?, About the Commons, User guide, Site map, Ask the Commons, For your role, Accessibility and privacy | Find your way, ask a question, see what the Commons is for and what each role needs |
| Learn: Learn and build skills | Learn, Across the professions, Governance boards and forums, Skills and training, Knowledge map, Library and knowledge base, Media centre, Events | Learn, check your skills, explore concepts and how they connect, read and watch |
| Check: Check and assess | Check your data, Maturity self-assessment, Data management wheel, Issues framework, Rules assistant, Critical data asset baseline | Measure quality in your browser, assess maturity, see your whole data capability, prioritise issues, draft rules, size a baseline |
| Improve: Manage and improve | Data quality management playbook, Frameworks and standards, Tooling, Catalogues and quality tools, AI for data quality, Buying and suppliers, Legacy and modernisation, Interoperability and standards, Metadata Weaver, Capability and data models, Pipeline status | Follow the playbook, compare frameworks, choose and connect catalogues and quality tools, use AI safely, write contracts, migrate, join data up, publish metadata, see the capability model and workflows |
| Apply: Apply to your context | All scenarios, UK and the world, National Data Library, Three portals one journey, Use the Commons your way | Work through a policy, sector, nation or platform; bring the Commons into your organisation, systems and AI assistants |
| Contribute: Contribute and get help | Community, Get involved, Case studies, Surveys and commissions, Take part in user research, Help us build this, Open roadmap and priorities, Operating model and support | Contribute, run surveys, ask for help, vote on the roadmap, co-design, contact us |

On a wide screen each group opens a panel under its tab. On smaller screens, and when zoomed in, press **Menu** to see every group in one list. The **Site map** shows every page on one screen, by group and level, with suggested routes.

## Finding your way

- **Colours.** Each menu group has its own colour: Start teal, Learn purple, Check blue, Improve orange, Apply green, Contribute pink. It appears on the menu, the label above each page title and the previous and next links. Sections on a page take turns with other colours, matched in the **On this page** list. Colour is always backed up by words.
- **Tables.** Columns are sized to what they hold: short codes and numbers stay narrow, long descriptions get more room. Rows are striped and highlight when you point at them. On large screens wide tables use the space beside the page. If a table is still wider than the screen, a shadow shows at its edge and a note says to scroll sideways (or hold Shift and use the mouse wheel). Long tables keep their headings in view.
- **Tooltips.** The first time an acronym appears on a page it has a dotted underline: hover over or tap it to see what it means. Icon-only buttons explain themselves when you hover over or tab to them. Escape closes a tooltip.
- **Progress, Top, previous and next.** A thin bar under the menu shows how far down the page you are. **Top** (bottom right) returns to the start of the page. The end of every page links to the previous and next page in menu order, with dots showing where you are in that group.
- **Share this page.** Under every page title: copy a link to the page or to the section you are reading, share with your device, by email, to Microsoft Teams or LinkedIn, copy code to embed the page, or print. The Commons itself sends nothing.
- **Ask the Commons.** Ask a question in plain English and get the best-matching passages from across the portal, with links. It runs in your browser and is not generative AI.

## Tutorials

The user guide page in the portal has six short tutorials: find anything in under a minute; share a page or section; put a Commons page on your intranet; use the Commons from an AI assistant; read a big table comfortably; make your own branded copy. Each ends with a link that opens the right page with its guided tour. Every guided tour now ends with the shared aids (tables, tooltips, previous and next) where the page has them.

## Common tasks

### See where you fit in data quality management
Go to **Capability and data models** (or **Find your way by capability** on the home page). Choose a capability to see what it involves and where to do it in the Commons. Under **Workflows**, press **Play** to walk through a workflow, or highlight your role to see just your steps; each step links to the page where you do it. Under **Records**, choose a record to see its fields and how it links to others. Downloads for Visio, ArchiMate, UML, BPMN and database tools are on the same page.

### Use your rules in another platform
Go to **Connectors, weaves and AI** (menu 5 Apply). Load an example or paste your rules, then choose a platform: the page writes the same rules in that platform's own format, ready to copy or download. Anything that can't be translated is listed at the end. From the toolkit: `python3 -m dqkit export rules.yaml --to glue`. The same page lists each vendor's open-source code, AI agents and MCP servers, with a source for every fact.

### Check a dataset
Go to **Check data**. Open your file, add rules (or press **Suggest rules**), then **Run**. Identifier checks cover NHS numbers, National Insurance numbers, postcodes, UPRNs, GSS codes and more. Nothing is uploaded.

### See how a framework applies to you
Go to **Frameworks**. Filter by nation, sector or type. Each entry shows its dimensions and how they map to the kit's dimensions. The clause table breaks policies down line by line and shows where devolved and international equivalents agree or differ.

### Assess your organisation's maturity
Go to **Maturity**. Choose the statement that best fits you for each of 8 themes. You get a level per theme (Beginning to Mastering) and next steps with links. Results stay in your browser unless you choose to download them.

### Share rules as a data contract
On **Check your data**, under "Share the rules as a data contract", choose ODCS, Table Schema, CSVW, Great Expectations or R validate. You can also load a contract as rules.

### Buy or connect a data catalogue and a quality tool
Go to **Catalogues and quality tools**. See how products connect and which integration pattern fits you. Use the **lock-in checker** on a bundle or supplier you are considering, then the **question builder** to download RFI or RFP questions. Run the **proof-of-concept** tests with your own data, and keep the **exit checklist** up to date. The checker can add the matching clauses to the clause builder on **Buying and suppliers**.

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

### Bring the Commons into your organisation
Go to **Use the Commons your way**. Answer three questions to see which routes suit you: link, embed in your intranet (with your accent colour), feeds for channels, the open data API (`api/index.json`), a white-label copy, an offline copy, the toolkit in your pipelines, or enterprise content and records. The embed code builder writes the code for you and checks your colour's contrast.

### Use the Commons with an AI assistant
Try **Ask the Commons** first. To use your organisation's own approved assistant, follow the MCP set-up steps on **Use the Commons your way** (`python -m dqkit.mcp_server`), or give it `api/passages.json` as a knowledge source. Follow the guardrails on that page: approved tools only, no personal data, cite and check sources.

### See your whole data capability on the data management wheel
Go to **Data management wheel**. Choose your role, then an area of the wheel (data governance sits at the centre, ten knowledge areas around it). You see what it means for you, what to do for the DAM policy, where it surfaces in the maturity themes and the government's Data Maturity Assessment, its lifecycle stages, and how records and information management overlaps. Tick **Colour by my maturity results** to shade the wheel with your answers. Further down: one lifecycle for data and records, records frameworks side by side, ten join-up actions you can tick and download as a plan, and the communities where the professions meet.

### Find a standard and its status in government
Open the [standards catalogue](https://cyberdudeuk.github.io/dq-commons/interop.html#catalogue) on the interoperability page. Type a name (for example DQV) or filter by domain (data, digital, cyber, technology) and status. Each row links to the specification, the GOV.UK list, the Rosetta concepts it expresses, whether the Metadata Weaver reads or writes it, and where it appears in public code.

### Publish how complete your metadata is (DQV)
In the [Metadata Weaver](https://cyberdudeuk.github.io/dq-commons/weaver.html), paste a record and open the **DQV (metadata quality)** tab. It gives coverage, critical data asset properties and profile conformance as W3C DQV you can publish next to your DCAT record. From the command line: `dqkit weave record.json --to dqv`.

### Continue in a sister portal
Open [Three portals, one journey](https://cyberdudeuk.github.io/dq-commons/ecosystem.html). Compare what DQ Commons, the DAM capability playbooks and the GitHub repos asset catalogue each offer; choose a box on the lineage map to see where it leads; or use **Trace one thing** to follow a DAMA area, a role or a standard through all three. Many pages also end with **Continue in a sister portal**.

### Run data quality through a programme or project
On **For your role**, choose a change and delivery role (SRO, programme or delivery manager, PMO, business change lead, business analyst, product or service owner, architect, data migration lead, test lead, or records and information manager). Under **Data quality in change programmes and projects** you'll find why each role was added, the lifecycle with gate questions, a RACI you can filter by phase or role, a service blueprint and example journeys.

### Take part in user research, or invite your team
Open **Take part in user research**. Read what the Commons offers each role, then sign up for the research panel. To introduce colleagues, use **Research bundle for your team**: copy the invitation email or download the bundle (invitation, email file, consent, sign-up questions, session guides).

### See what's coming and why
Open **Open roadmap and priorities**. Choose an item on the roadmap to see its evidence, score, the government strategy it supports and its objective. Move the sliders under **How we prioritise** to try your own weights. Suggest an idea or vote through **Help us build this**.

### Get involved, champion the Commons or get a badge
Open **Get involved**. Pick a route: contribute directly, join a working group, or become a champion or ambassador. Under **Communications kit**, choose a message for email, Teams, Slack, Viva Engage, your intranet or a team meeting and copy it. Under **Badges**, choose a badge to get the code for your GitHub profile, email signature or social media, then claim it on GitHub.

### Find which board or forum deals with something
Open **Governance boards and forums** and choose a question under **Where should my question go?**. Open any body for its aims, outcomes, rules of engagement and terms of reference.

### Make pages easier to read
Select **Aa** in the top bar: text size, spacing, an easier-to-read font, high contrast, reduced movement and source labels.

### Give feedback
Every page ends with a feedback link. Use the **Microsoft Form** (no sign-in, no names or emails), the **GitHub contact form**, a survey, or the accessibility route. All of them are on **Help us build this** under Give feedback.

### See what's new
Press **What's new** in the top bar. Each release lists what's new, changed and fixed. New and updated pages are flagged in the menus.

### Contact the team
Go to **Help us build this** and use the contact form. We never show an email address and you don't need to give yours. The form opens a pre-filled GitHub contact issue; we reply there, and GitHub notifies you.

### Learn
Go to **Learn**. Pick your role to see a pathway. Tutorials take 10 to 30 minutes each. The glossary explains every term used in the Commons.

### Start from your role
Open **1 Start > For your role** and choose your role. You'll see what you need, decisions coming up, what to watch, measures to ask for and the gaps that affect you. The CDO Council brief and the gap register are on the same page.

### Run a data quality cycle on a critical data asset
Open **4 Improve > Data quality management playbook**. Work through the eight stages in order; tick the checklist as you go (ticks stay in your browser). Download the CSV templates for your register, rules, issue log, action plan, quality statement and annual review. You can download a progress report, or run the same playbook from the toolkit with `python -m dqkit playbook init`. Outside UK central government, use the "Use it anywhere" table to swap in your own terms, and "Where it applies" to see your framework.

### Use AI to improve data quality
Read the **AI for data quality** section on the Learn page: principles, use cases, questions to ask vendors, worked examples and how AI tools become part of the shared toolkit. The **Rules assistant** drafts rules from plain English with fixed patterns, in your browser, with no AI service or licence needed; always check what it drafts. It can also copy your request as a prompt for an AI tool your organisation has approved.

### Contribute or ask for help
Go to **Community**. Add a case study or insight, take or run a survey, or request help (a commission). To vote on the wishlist or see the roadmap, go to **Help us build this**. Every form finishes on GitHub: it opens a GitHub issue form already filled in, you check it and submit. You need a free GitHub account (or ask a colleague to submit for you). Moderators publish contributions by labelling them, and the portal shows them, with survey totals and votes, after its daily update.

## Accessibility

The portal aims to meet WCAG 2.2 AA. It works with keyboard only, screen readers and up to 400% zoom, and respects reduced motion settings. If something doesn't work for you, tell us through the contact form on Help us build this and we'll reply within 1 working day.

## Privacy

- Data you check stays in your browser.
- Surveys never ask for your name or email. Results are shown as totals only, and totals under 5 are hidden.
- Contributions appear on the portal only after a moderator publishes them. GitHub issues themselves are public as soon as they are submitted, and show the GitHub username of whoever submits.

## Getting help

See the **Operating model** page for support tiers. Short version: try the guide and tours first, then the community, then the service desk.
