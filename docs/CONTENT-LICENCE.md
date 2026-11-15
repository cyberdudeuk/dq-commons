# Content licence

**Code** in this repository (Python, JavaScript, workflows, scripts) is under the
[MIT Licence](../LICENSE).

**Documentation and content** in this repository (the portal's pages and knowledge base, the
guidance, playbook, vocabulary, models, rules files, templates, and the Commons' own assessment
results and reports) are licensed under the
[Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).
You may share and adapt them for any purpose, including commercially, as long as you give
appropriate credit, link to the licence and say if you made changes. Credit: "Public Sector Data
Quality Commons, Emanuel Silva and contributors, CC BY 4.0".

The owner's decision is recorded as D-LIC-01 in [`DECISIONS.md`](DECISIONS.md) (15 November 2026).

## Third-party data keeps its source's licence

Some files hold data copied from other publishers, so they are **not** relicensed by this
repository. They keep the licence their source publishes them under:

- `assessments/ndl/harvest.jsonl`: page metadata harvested from the National Data Library's
  curated pages on data.gov.uk (14 October 2026).
- `assessments/ndl/chart-data/`: the NDL's own chart data downloads, sampled.
- `knowledge/code-evidence.yaml`: counts imported from the GitHub Repos Asset Catalogue, under the
  licence that catalogue states in its `source` block.

The rules, results, scores, reports and DQAP workbooks the Commons produces from them
(`assessments/ndl/results/`, `assessments/ndl/REPORT.md`, `assessments/portfolio/`) are the
Commons' own work and are under CC BY 4.0. Check each source's terms before reusing its data.

## Why two files

GitHub reads the root `LICENSE` file to label the repository's licence. It only recognises
that file when it holds the exact standard licence text. Keeping the content licence statement
here means GitHub, package indexes and code-search tools correctly show the code as MIT, while
the content licence stays clear and visible.
