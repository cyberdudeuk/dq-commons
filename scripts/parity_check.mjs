// Node runner for the JavaScript/Python parity check (driven by scripts/parity_check.py).
//
// Usage: node scripts/parity_check.mjs <case.json>
// Loads portal/src/js/engine.js exactly as a browser would (one global, no imports), runs the case,
// and prints the JavaScript outputs as JSON on stdout. Errors are reported as {"error": message}.
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const DQ = createRequire(import.meta.url)(join(here, '..', 'portal', 'src', 'js', 'engine.js'));
const c = JSON.parse(readFileSync(process.argv[2], 'utf8'));
DQ.setVocab(c.vocab.issue_types, c.vocab.dimensions);

// Run fn and return its value, or {error} when it throws (so both sides can be compared).
const attempt = (fn) => { try { return fn(); } catch (e) { return { error: String(e && e.message || e) }; } };

const out = {};
if (c.kind === 'run' || c.kind === 'ops') {
  const table = c.csv !== undefined ? DQ.parseCSV(c.csv) : c.table;
  if (c.csv !== undefined) out.parsed = table;
  const result = DQ.run(table, c.spec, c.as_of);
  out.result = result;
  if (c.kind === 'run') {
    out.trust = DQ.trust(result, c.personal || null);
    out.route = DQ.route(c.spec.asset);
    out.dqv = DQ.toDQV(result, c.asset_iri || null, c.dqap_iri || null);
    out.dqap = DQ.toDqapCsv(result);
    out.validate = attempt(() => { DQ.validateSpec(c.spec); return 'ok'; });
  } else {
    out.ops = DQ.operations(result, c.history);
  }
} else if (c.kind === 'grid') {
  out.assess = c.items.map(([imp, impact, perf, target, policy]) => attempt(() => DQ.assess(imp, impact, perf, target, policy)));
} else if (c.kind === 'micro') {
  const P = DQ._py;
  out.numbers = c.numbers.map((s) => P.pdNumber(s).v);
  out.types = c.types.map(([v, kind]) => attempt(() => P.isType(v, kind)));
  out.dates = c.dates.map((s) => attempt(() => { const d = P.parseDate(s); return d ? d.iso : null; }));
  out.regex = c.regex.map(([pat, s]) => attempt(() => P.translateRegex(pat).test(s)));
  out.rounds = c.rounds.map(([x, n]) => P.pyRound(x, n));
  out.reprs = c.reprs.map((x) => P.pyFloatRepr(x));
  out.error_rates = c.error_rates.map((x) => DQ.errorRate(x));
  out.pairwise = c.sums.map((xs) => P.pairwiseSum(xs, 0, xs.length));
  out.pysum = c.sums.map((xs) => P.pySum(xs));
  out.durations = c.durations.map((s) => attempt(() => P.isoDurationDays(s)));
  out.csvs = c.csvs.map((t) => attempt(() => DQ.parseCSV(t)));
  out.validate = c.validate.map((spec) => attempt(() => { DQ.validateSpec(spec); return 'ok'; }));
  out.identifiers = c.identifiers.map(([v, scheme]) => attempt(() => DQ.identifierOk(v, scheme)));
  out.valuesets = c.valueset_specs.map((spec) => attempt(() => DQ.expandValuesets(spec, c.valuesets_data)));
  out.contracts = c.contract_specs.map((spec) => attempt(() => {
    const C = DQ.contracts, o = C.toOdcs(spec), t = C.toTableSchema(spec);
    return { odcs: o, ts: t, csvw: C.toCsvw(spec), back: C.fromOdcs(o), backTs: C.fromTableSchema(t), unsupported: C.unsupported(o),
      gx: DQ.exporters.toGreatExpectations(spec), rv: DQ.exporters.rValidateRules(spec) };
  }));
  out.misc = {
    targets: [3, 6, 9, 16].map((s) => DQ.defaultTarget(s)), mid4: DQ.defaultTarget(4, 'mid'),
    bands: [75, 90, 95, 97.5, 99.9, 100].map((t) => DQ.bands(t)),
    route: c.routes.map((a) => DQ.route(a)),
    trust: c.trusts.map(([res, personal]) => DQ.trust(res, personal)),
  };
}

// JSON has no NaN or Infinity, so mark them explicitly.
const enc = (k, v) => (typeof v === 'number' && !Number.isFinite(v)) ? { __float__: Number.isNaN(v) ? 'nan' : (v > 0 ? 'inf' : '-inf') } : v;
process.stdout.write(JSON.stringify(out, enc));
