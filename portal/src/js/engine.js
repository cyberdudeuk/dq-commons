/*
 * NDL data quality engine: a browser port of the Python kit (dqkit).
 *
 * It runs a rules file against a CSV file entirely in the page, with no server, and gives the
 * same answers as the Python kit. scripts/parity_check.py proves that, case by case.
 *
 * Mirrors: framework.py (GOV.UK issues framework scoring), rules.py (the 15 checks), trust.py,
 * pathway.py, operations.py, dqv.py (result_to_dqv) and exporters.py (to_dqap_csv).
 *
 * Usage:   DQ.setVocab(issueTypes, dimensions);  var t = DQ.parseCSV(text);
 *          var result = DQ.run(t, spec, "2026-10-14");
 *
 * Matching Python closely means copying some of its quirks on purpose. Each one is marked
 * "Python:" in a comment. The engine follows pandas 3 (blanks stay missing; they never match
 * a pattern or a list of allowed values).
 *
 * Known differences, documented rather than hidden:
 * 1. JSON cannot tell 1.0 from 1, so a whole-number float in a rules file prints as "1" here
 *    and "1.0" in Python. This only shows in in_set values and compare expressions.
 * 2. Integers above 2^53 (16+ digits) lose precision in JavaScript numbers.
 * 3. A CSV row with more fields than the header is an error here; pandas would quietly
 *    turn the first column into the row index.
 * 4. Regex: Python features JavaScript lacks (possessive quantifiers, atomic groups,
 *    conditionals, scoped flags, \N{...}, \W or \S inside [...]) raise an error instead of
 *    running differently. Everything else is translated to behave like Python's re.
 */
(function (g) {
  'use strict';
  var DQ = {};
  var ISSUE_TYPES = null, DIMENSIONS = null;

  // ---------------------------------------------------------------------------------------
  // 1. Python-compatible helpers (whitespace, digits, numbers, rounding, printing)
  // ---------------------------------------------------------------------------------------

  // Python's str.isspace() characters, as a regex class body.
  var PY_WS = '\\t\\n\\v\\f\\r\\x1c-\\x1f \\x85\\xa0\\u1680\\u2000-\\u200a\\u2028\\u2029\\u202f\\u205f\\u3000';
  var WS_CHAR = new RegExp('^[' + PY_WS + ']$');
  var STRIP = new RegExp('^[' + PY_WS + ']+|[' + PY_WS + ']+$', 'g');
  var ND = /^\p{Nd}$/u;                       // Python's \d: any Unicode decimal digit

  function pyStrip(s) { return s.replace(STRIP, ''); }
  function put(o, k, v) {                                     // o[k] = v, safe even for a key "__proto__"
    Object.defineProperty(o, k, { value: v, enumerable: true, writable: true, configurable: true });
  }
  function has(o, k) { return o !== null && typeof o === 'object' && Object.prototype.hasOwnProperty.call(o, k); }
  function get(o, k, d) { return has(o, k) ? o[k] : d; }     // Python dict.get
  function req(o, k) {                                         // Python o[k] (KeyError when absent)
    if (!has(o, k)) throw new Error("'" + k + "'");
    return o[k];
  }
  function truthy(v) {                                         // Python truthiness
    if (Array.isArray(v)) return v.length > 0;
    if (v !== null && typeof v === 'object') return Object.keys(v).length > 0;
    return !!v;
  }
  function cpCompare(a, b) {                                  // Python string order (code points)
    var A = Array.from(a), B = Array.from(b);
    for (var i = 0; i < Math.min(A.length, B.length); i++) {
      var x = A[i].codePointAt(0), y = B[i].codePointAt(0);
      if (x !== y) return x < y ? -1 : 1;
    }
    return A.length - B.length;
  }
  function pySorted(arr) { return arr.slice().sort(cpCompare); }

  // Value of a Unicode decimal digit. Digits come in runs of ten starting at zero.
  function digitValue(ch) {
    var cp = ch.codePointAt(0), k = 0;
    while (ND.test(String.fromCodePoint(cp - k - 1))) k++;
    return k % 10;
  }

  // Python float()/int() first turn Unicode digits and spaces into ASCII, strip, and check underscores.
  function cleanNumberText(v) {
    var t = Array.from(v).map(function (ch) {
      if (ch >= '0' && ch <= '9') return ch;
      if (ND.test(ch)) return String(digitValue(ch));
      if (WS_CHAR.test(ch)) return ' ';
      return ch;
    }).join('').replace(/^[ \t\n\v\f\r]+|[ \t\n\v\f\r]+$/g, '');
    if (/[^\x00-\x7f]/.test(t)) return null;
    if (t.indexOf('_') >= 0) {                                 // underscores only between digits
      var prev = '', out = '';
      for (var i = 0; i < t.length; i++) {
        var c = t[i];
        if (c === '_') { if (!(prev >= '0' && prev <= '9')) return null; }
        else { if (prev === '_' && !(c >= '0' && c <= '9')) return null; out += c; }
        prev = c;
      }
      if (prev === '_') return null;
      t = out;
    }
    return t;
  }

  // Python float(v). Returns undefined where Python raises ValueError.
  function pyFloat(v) {
    if (typeof v === 'number') return v;
    if (typeof v === 'boolean') return v ? 1 : 0;
    if (typeof v !== 'string') return undefined;
    var s = cleanNumberText(v);
    if (s === null) return undefined;
    if (/^[+-]?inf(inity)?$/i.test(s)) return s[0] === '-' ? -Infinity : Infinity;
    if (/^[+-]?nan$/i.test(s)) return NaN;
    if (!/^[+-]?(\d+\.?\d*|\.\d+)(e[+-]?\d+)?$/i.test(s)) return undefined;
    return Number(s);
  }
  function floatOrThrow(v) {
    var f = pyFloat(v);
    if (f === undefined) throw new Error('could not convert string to float: ' + pyRepr(v));
    return f;
  }

  // Python int(v).
  function pyInt(v) {
    if (typeof v === 'boolean') return v ? 1 : 0;
    if (typeof v === 'number') {
      if (!isFinite(v)) throw new Error('cannot convert float ' + pyStr(v) + ' to integer');
      return Math.trunc(v);
    }
    var s = typeof v === 'string' ? cleanNumberText(v) : null;
    if (s === null || !/^[+-]?\d+$/.test(s)) throw new Error('invalid literal for int() with base 10: ' + pyRepr(v));
    return Number(s);
  }

  // Reading a number from text: the same rule as dqkit/numbers.py (issue #25, D-TK-02), so results
  // no longer depend on the pandas version. Spaces, optional sign, digits with an optional point,
  // optional exponent, spaces; "inf"/"infinity" any case. The value is the correctly rounded double.
  function isDig(c) { return c >= '0' && c <= '9'; }
  var NUM_RX = /^[ \t\n\r\v\f]*([+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+))([eE][+-]?[0-9]+)?[ \t\n\r\v\f]*$/;
  function pdNumber(s) {
    if (s === null || s === undefined) return { v: NaN, isInt: false };
    s = String(s);
    var m = NUM_RX.exec(s);
    if (m) return { v: Number(m[1] + (m[2] || '')), isInt: !m[2] && m[1].indexOf('.') < 0, text: m[1] };
    if (/^[+-]?inf(inity)?$/i.test(s)) return { v: s[0] === '-' ? -Infinity : Infinity, isInt: false };
    return { v: NaN, isInt: false };
  }
  // A whole column. pandas gives an integer column (exact values) when every value is a plain integer.
  function pdNumericColumn(values) {
    var parsed = values.map(pdNumber);
    var allInt = parsed.length > 0 && parsed.every(function (x) { return x.isInt; });
    if (!allInt) return { vals: parsed.map(function (x) { return x.v; }), ints: null };
    var ints = parsed.map(function (x) { return BigInt(x.text.replace(/^\+/, '')); });
    var lo = -(BigInt(2) ** BigInt(63)), hi = BigInt(2) ** BigInt(63);
    if (!ints.every(function (i) { return i >= lo && i < hi; })) return { vals: parsed.map(function (x) { return x.v; }), ints: null };
    return { vals: ints.map(Number), ints: ints };
  }

  // numpy's pairwise summation (used by pandas Series.sum on floats). Blanks count as 0.
  function pairwiseSum(a, lo, n) {
    var i, res;
    if (n < 8) { res = -0; for (i = 0; i < n; i++) res += a[lo + i]; return res; }
    if (n <= 128) {
      var r = a.slice(lo, lo + 8);
      for (i = 8; i < n - (n % 8); i += 8) for (var j = 0; j < 8; j++) r[j] += a[lo + i + j];
      res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
      for (; i < n; i++) res += a[lo + i];
      return res;
    }
    var n2 = Math.floor(n / 2); n2 -= n2 % 8;
    return pairwiseSum(a, lo, n2) + pairwiseSum(a, lo + n2, n - n2);
  }

  // Python's built-in sum() of floats (Neumaier compensated summation, Python 3.12+).
  function pySum(xs) {
    var f = 0, c = 0;
    xs.forEach(function (x) {
      var t = f + x;
      c += Math.abs(f) >= Math.abs(x) ? (f - t) + x : (x - t) + f;
      f = t;
    });
    return (c !== 0 && isFinite(c)) ? f + c : f;
  }

  // Exact decimal form of a double: |x| = N / 10^s. Used for Python-exact rounding.
  function exactDec(x) {
    var dv = new DataView(new ArrayBuffer(8));
    dv.setFloat64(0, Math.abs(x));
    var hi = dv.getUint32(0), lo = dv.getUint32(4), e = (hi >>> 20) & 0x7ff;
    var m = (BigInt(hi & 0xfffff) << BigInt(32)) | BigInt(lo), e2;
    if (e === 0) e2 = -1074; else { m |= BigInt(1) << BigInt(52); e2 = e - 1075; }
    if (e2 >= 0) return { N: m << BigInt(e2), s: 0 };
    return { N: m * (BigInt(5) ** BigInt(-e2)), s: -e2 };
  }
  function roundHalfEven(N, drop) {                           // N / 10^drop, ties to even
    if (drop <= 0) return N * (BigInt(10) ** BigInt(-drop));
    var d = BigInt(10) ** BigInt(drop), q = N / d, r = N % d, half = d / BigInt(2);
    if (r > half || (r === half && q % BigInt(2) === BigInt(1))) q += BigInt(1);
    return q;
  }
  // Python round(x, nd): exact, ties to even ("banker's rounding").
  function pyRound(x, nd) {
    if (!isFinite(x) || x === 0) return x;
    var d = exactDec(x);
    if (d.s <= nd) return x;
    var v = Number(roundHalfEven(d.N, d.s - nd).toString() + 'e-' + nd);
    return x < 0 ? -v : v;
  }
  function withCommas(digits) { return digits.replace(/\B(?=(\d{3})+(?!\d))/g, ','); }
  function fmtThousands0(x) {                                 // Python f"{x:,.0f}"
    var d = exactDec(x);
    return (x < 0 ? '-' : '') + withCommas(roundHalfEven(d.N, d.s).toString());
  }
  function fmtG(x, p) {                                       // Python f"{x:.{p}g}" (x > 0)
    var d = exactDec(x), ns = d.N.toString(), E = ns.length - 1 - d.s;
    var q = roundHalfEven(d.N, ns.length - p), digits = q.toString();
    if (digits.length > p) { digits = digits.slice(0, p); E += 1; }
    var strip = function (t) { return t.indexOf('.') >= 0 ? t.replace(/0+$/, '').replace(/\.$/, '') : t; };
    if (E < -4 || E >= p) {
      var mant = strip(digits[0] + '.' + digits.slice(1));
      return mant + 'e' + (E < 0 ? '-' : '+') + (Math.abs(E) < 10 ? '0' : '') + Math.abs(E);
    }
    var t = E >= 0 ? digits.slice(0, E + 1) + '.' + digits.slice(E + 1) : '0.' + '0'.repeat(-E - 1) + digits;
    return strip(t);
  }

  // Python repr() of a float: shortest round-trip digits, ".0" on whole numbers.
  function pyFloatRepr(x) {
    if (isNaN(x)) return 'nan';
    if (!isFinite(x)) return x > 0 ? 'inf' : '-inf';
    if (x === 0) return 1 / x < 0 ? '-0.0' : '0.0';
    var m = /^(\d)(?:\.(\d+))?e([+-]\d+)$/.exec(Math.abs(x).toExponential());
    var digits = m[1] + (m[2] || ''), e10 = parseInt(m[3], 10), dp = e10 + 1, sign = x < 0 ? '-' : '', t;
    if (dp > -4 && dp <= 16) {                                // otherwise Python writes 1e+16 style
      if (dp <= 0) t = '0.' + '0'.repeat(-dp) + digits;
      else if (dp >= digits.length) t = digits + '0'.repeat(dp - digits.length) + '.0';
      else t = digits.slice(0, dp) + '.' + digits.slice(dp);
    } else {
      t = digits[0] + (digits.length > 1 ? '.' + digits.slice(1) : '') + 'e' + (e10 < 0 ? '-' : '+') +
        (Math.abs(e10) < 10 ? '0' : '') + Math.abs(e10);
    }
    return sign + t;
  }
  // Python str(). JSON cannot say whether a whole number was an int or a float: ints are assumed.
  function pyStr(v) {
    if (v === null || v === undefined) return 'None';
    if (typeof v === 'boolean') return v ? 'True' : 'False';
    if (typeof v === 'number') return Number.isInteger(v) && Math.abs(v) < 1e16 ? String(v) : pyFloatRepr(v);
    if (typeof v === 'string') return v;
    return pyRepr(v);
  }
  // Python repr(), as used in error messages.
  function pyRepr(v) {
    if (typeof v === 'string') {
      var q = (v.indexOf("'") >= 0 && v.indexOf('"') < 0) ? '"' : "'";
      var body = Array.from(v).map(function (ch) {
        var c = ch.codePointAt(0);
        if (ch === '\\' || ch === q) return '\\' + ch;
        if (ch === '\n') return '\\n';
        if (ch === '\r') return '\\r';
        if (ch === '\t') return '\\t';
        if (c < 0x20 || (c >= 0x7f && c <= 0xa0) || (c !== 0x20 && /[\p{C}\p{Z}]/u.test(ch))) {
          var h = c.toString(16);
          return c <= 0xff ? '\\x' + h.padStart(2, '0') : c <= 0xffff ? '\\u' + h.padStart(4, '0') : '\\U' + h.padStart(8, '0');
        }
        return ch;
      }).join('');
      return q + body + q;
    }
    if (Array.isArray(v)) return '[' + v.map(pyRepr).join(', ') + ']';
    if (v !== null && typeof v === 'object') {
      return '{' + Object.keys(v).map(function (k) { return pyRepr(k) + ': ' + pyRepr(v[k]); }).join(', ') + '}';
    }
    return pyStr(v);
  }

  // ---------------------------------------------------------------------------------------
  // 2. Dates (Python datetime.strptime and the kit's _parse_date)
  // ---------------------------------------------------------------------------------------

  var DBM = [0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334];
  function leap(y) { return y % 4 === 0 && (y % 100 !== 0 || y % 400 === 0); }
  function dim(y, m) { return [31, leap(y) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]; }
  function mkDate(y, m, d) {                                  // null when Python would reject the date
    if (y < 1 || y > 9999 || m < 1 || m > 12 || d < 1 || d > dim(y, m)) return null;
    var y1 = y - 1;
    var ord = y1 * 365 + Math.floor(y1 / 4) - Math.floor(y1 / 100) + Math.floor(y1 / 400) + DBM[m] + (m > 2 && leap(y) ? 1 : 0) + d;
    var iso = String(y).padStart(4, '0') + '-' + String(m).padStart(2, '0') + '-' + String(d).padStart(2, '0');
    return { y: y, m: m, d: d, ord: ord, iso: iso };
  }
  // strptime pieces, copied from CPython's _strptime (\d there is any Unicode digit).
  var P = { Y: '(\\p{Nd}{4})', y: '(\\p{Nd}{2})', m: '(1[0-2]|0[1-9]|[1-9])', d: '(3[0-1]|[1-2]\\p{Nd}|0[1-9]|[1-9]| [1-9])' };
  var FORMATS = [                                             // same order as rules._parse_date
    { re: new RegExp('^' + P.Y + '-' + P.m + '-' + P.d, 'iu'), f: function (g) { return [pyInt(g[1]), pyInt(g[2]), pyInt(g[3])]; } },
    { re: new RegExp('^' + P.d + '/' + P.m + '/' + P.Y, 'iu'), f: function (g) { return [pyInt(g[3]), pyInt(g[2]), pyInt(g[1])]; } },
    { re: new RegExp('^' + P.Y + '-' + P.m, 'iu'), f: function (g) { return [pyInt(g[1]), pyInt(g[2]), 1]; } },
    { re: new RegExp('^' + P.Y, 'iu'), f: function (g) { return [pyInt(g[1]), 1, 1]; } },
    { re: new RegExp('^' + P.d + '/' + P.m + '/' + P.y, 'iu'), f: function (g) {
      var y = pyInt(g[3]); return [y <= 68 ? 2000 + y : 1900 + y, pyInt(g[2]), pyInt(g[1])];
    } }
  ];
  var FIN_YEAR = new RegExp('^(\\p{Nd}{4})[' + PY_WS + ']*[-/][' + PY_WS + ']*(\\p{Nd}{2}|\\p{Nd}{4})$', 'u');

  function parseDate(value) {
    if (value === null || value === undefined) return null;
    var s = pyStrip(pyStr(value));
    for (var i = 0; i < FORMATS.length; i++) {
      var m = FORMATS[i].re.exec(s);
      if (!m || m[0].length !== s.length) continue;          // Python: "unconverted data remains"
      var ymd = FORMATS[i].f(m), d = mkDate(ymd[0], ymd[1], ymd[2]);
      if (d) return d;
    }
    var fy = FIN_YEAR.exec(s);                                // 2023-24 or 2023/2024 financial years
    if (fy) {
      var d2 = mkDate(pyInt(fy[1]), 4, 1);
      if (!d2) throw new Error('year ' + pyInt(fy[1]) + ' is out of range');
      return d2;
    }
    return null;
  }
  function parseAsOf(iso) {
    if (iso === undefined || iso === null) {
      var t = new Date();
      return mkDate(t.getFullYear(), t.getMonth() + 1, t.getDate());
    }
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(iso));
    var d = m && mkDate(+m[1], +m[2], +m[3]);
    if (!d) throw new Error('as_of must be a date written YYYY-MM-DD');
    return d;
  }
  function isoDurationDays(period) {
    var s = truthy(period) ? period : '';                     // Python: period or ""
    if (typeof s !== 'string') throw new Error('expected string or bytes-like object, got ' + pyRepr(s));
    var m = /^P(?:(\p{Nd}+)Y)?(?:(\p{Nd}+)M)?(?:(\p{Nd}+)W)?(?:(\p{Nd}+)D)?$/u.exec(s);
    if (!m || !(m[1] || m[2] || m[3] || m[4])) throw new Error('not an ISO 8601 duration: ' + pyRepr(period));
    var n = function (x) { return x ? pyInt(x) : 0; };
    return n(m[1]) * 365.25 + n(m[2]) * 30.44 + n(m[3]) * 7 + n(m[4]);
  }

  function isType(value, kind) {
    if (value === null || value === undefined || pyStrip(pyStr(value)) === '') return false;
    var s = pyStrip(pyStr(value)).replace(/,/g, '');
    if (kind === 'integer') return /^[-+]?\p{Nd}+$/u.test(s);
    if (kind === 'number') return pyFloat(s) !== undefined;
    if (kind === 'year') return /^\p{Nd}{4}$/u.test(s) && pyInt(s) >= 1000 && pyInt(s) <= 2999;
    if (kind === 'date') return parseDate(s) !== null;
    throw new Error('unknown type ' + pyRepr(kind));
  }

  // ---------------------------------------------------------------------------------------
  // 3. Python regular expressions in JavaScript (for re.fullmatch)
  // ---------------------------------------------------------------------------------------

  function translateRegex(pat) {
    var flags = 'u', dotall = false, multi = false, ascii = false, m;
    while ((m = /^\(\?([aiLmsux]+)\)/.exec(pat))) {          // leading global flags, e.g. (?i)
      m[1].split('').forEach(function (f) {
        if (f === 'i') flags += 'i'; else if (f === 's') dotall = true; else if (f === 'm') multi = true;
        else if (f === 'a') ascii = true; else if (f !== 'u') throw new Error('regex flag (?' + f + ') is not supported in the browser');
      });
      pat = pat.slice(m[0].length);
    }
    var W = ascii ? 'A-Za-z0-9_' : '\\p{L}\\p{N}_', D = ascii ? '0-9' : '\\p{Nd}', S = ascii ? ' \\t\\n\\r\\f\\v' : PY_WS;
    var BOUND = '(?:(?<=[' + W + '])(?![' + W + '])|(?<![' + W + '])(?=[' + W + ']))';
    var NOBOUND = '(?:(?<=[' + W + '])(?=[' + W + '])|(?<![' + W + '])(?![' + W + ']))';
    var SYNTAX = '^$\\.*+?()[]{}|/';
    var out = '', i = 0, inClass = false, n = pat.length;
    function hex(h) { return '\\u{' + h.toString(16) + '}'; }
    function unsupported(what) { throw new Error('regex feature ' + what + ' is not supported in the browser'); }
    function escape(cls) {                                      // handles the text after a backslash
      var c = pat[i + 1], mm;
      if (c === undefined) throw new Error('bad escape (end of pattern)');
      i += 2;
      if (c === 'd') return cls ? D : '[' + D + ']';
      if (c === 'D') return ascii ? (cls ? unsupported('\\D in [...]') : '[^0-9]') : '\\P{Nd}';
      if (c === 'w') return cls ? W : '[' + W + ']';
      if (c === 's') return cls ? S : '[' + S + ']';
      if (c === 'W' || c === 'S') return cls ? unsupported('\\' + c + ' in [...]') : '[^' + (c === 'W' ? W : S) + ']';
      if (c === 'b') return cls ? hex(8) : BOUND;
      if (c === 'B' && !cls) return NOBOUND;
      if (c === 'A' && !cls) return '(?<![\\s\\S])';
      if (c === 'Z' && !cls) return '(?![\\s\\S])';
      var simple = { n: 10, t: 9, r: 13, f: 12, v: 11, a: 7 };
      if (has(simple, c)) return hex(simple[c]);
      if (c === 'x' && (mm = /^[0-9a-fA-F]{2}/.exec(pat.slice(i)))) { i += 2; return hex(parseInt(mm[0], 16)); }
      if (c === 'u' && (mm = /^[0-9a-fA-F]{4}/.exec(pat.slice(i)))) { i += 4; return hex(parseInt(mm[0], 16)); }
      if (c === 'U' && (mm = /^[0-9a-fA-F]{8}/.exec(pat.slice(i)))) { i += 8; return hex(parseInt(mm[0], 16)); }
      if (c >= '0' && c <= '9') {
        mm = /^[0-7]{0,2}/.exec(pat.slice(i));
        if (c === '0' || (c <= '7' && mm[0].length === 2)) {   // octal escape
          var oct = c === '0' ? /^[0-7]{0,2}/.exec(pat.slice(i))[0] : mm[0];
          i += oct.length; return hex(parseInt(c + oct, 8));
        }
        if (cls) throw new Error('bad escape \\' + c);
        var ref = c; if (isDig(pat[i] || '')) { ref += pat[i]; i++; }
        return '\\' + ref;
      }
      if (/[A-Za-z]/.test(c)) unsupported('\\' + c);
      return (SYNTAX.indexOf(c) >= 0 || (cls && c === '-')) ? '\\' + c : c;
    }
    var quant = false;                                          // was the last token a quantifier?
    while (i < n) {
      var c = pat[i];
      if (!inClass && quant && c === '+') unsupported('possessive quantifier');
      quant = !inClass && (c === '*' || c === '+' || c === '?');
      if (inClass) {
        if (c === ']') { out += ']'; inClass = false; i++; }
        else if (c === '\\') out += escape(true);
        else if (c === '[') { out += '\\['; i++; }
        else { out += c; i++; }
        continue;
      }
      if (c === '\\') { out += escape(false); }
      else if (c === '[') {
        out += '['; i++; inClass = true;
        if (pat[i] === '^') { out += '^'; i++; }
        if (pat[i] === ']') { out += '\\]'; i++; }               // Python: ']' first is literal
      } else if (c === '(') {
        var rest = pat.slice(i);
        if ((m = /^\(\?P<([A-Za-z_]\w*)>/.exec(rest))) { out += '(?<' + m[1] + '>'; i += m[0].length; }
        else if ((m = /^\(\?P=([A-Za-z_]\w*)\)/.exec(rest))) { out += '\\k<' + m[1] + '>'; i += m[0].length; }
        else if (/^\(\?#/.test(rest)) { var end = pat.indexOf(')', i); i = end < 0 ? n : end + 1; }
        else if (/^\(\?(:|=|!|<=|<!)/.test(rest) || rest[1] !== '?') { out += '('; i++; }
        else unsupported(rest.slice(0, 4));
      } else if (c === '.') { out += dotall ? '[\\s\\S]' : '[^\\n]'; i++; }
      else if (c === '$') { out += multi ? '(?=\\n|(?![\\s\\S]))' : '(?=\\n?(?![\\s\\S]))'; i++; }
      else if (c === '^') { out += multi ? '(?:(?<![\\s\\S])|(?<=\\n))' : '(?<![\\s\\S])'; i++; }
      else if (c === '{') {
        m = /^\{(\d*)(?:(,)(\d*))?\}/.exec(pat.slice(i));
        if (m && pat[i + 1] !== '}') {
          var lo = m[1] || '0', hi = m[2] ? m[3] : m[1];
          out += '{' + lo + (m[2] ? ',' + hi : '') + '}'; i += m[0].length; quant = true;
        } else { out += '\\{'; i++; }
      } else if (c === '}' || c === ']') { out += '\\' + c; i++; }
      else { out += c; i++; }
    }
    if (inClass) throw new Error('unterminated character set');
    return new RegExp('^(?:' + out + ')$', flags);
  }

  // ---------------------------------------------------------------------------------------
  // 4. CSV reading: pandas.read_csv(dtype=str, keep_default_na=False, na_values=[""], encoding="utf-8-sig")
  // ---------------------------------------------------------------------------------------

  DQ.parseCSV = function (text) {
    var s = String(text);
    if (s.charCodeAt(0) === 0xfeff) s = s.slice(1);
    var records = [], i = 0, n = s.length, line = 1;
    while (i < n) {
      var j = i;                                                // pandas skips blank and space-only lines
      while (j < n && (s[j] === ' ' || s[j] === '\t')) j++;
      if (j >= n || s[j] === '\n' || s[j] === '\r') {
        i = j + (s[j] === '\r' && s[j + 1] === '\n' ? 2 : 1); line++; continue;
      }
      var rec = [], field = '', startLine = line;
      for (;;) {
        if (s[i] === '"') {                                     // quoted field
          i++;
          for (;;) {
            if (i >= n) throw new Error('Error tokenizing data. EOF inside string starting at row ' + startLine);
            if (s[i] === '"') { if (s[i + 1] === '"') { field += '"'; i += 2; continue; } i++; break; }
            if (s[i] === '\n') line++;
            field += s[i++];
          }
        }
        while (i < n && s[i] !== ',' && s[i] !== '\n' && s[i] !== '\r') field += s[i++];  // quotes here are literal
        rec.push(field === '' ? null : field); field = '';
        if (s[i] === ',') { i++; continue; }
        if (s[i] === '\r') i += s[i + 1] === '\n' ? 2 : 1; else if (s[i] === '\n') i++;
        line++;
        break;
      }
      records.push({ fields: rec, line: startLine });
    }
    if (!records.length) throw new Error('No columns to parse from file');
    var header = records[0].fields.map(function (h, idx) { return h === null ? 'Unnamed: ' + idx : h; });
    var counts = Object.create(null);                           // pandas renames duplicate headers: a, a.1, a.2
    header.forEach(function (col, idx) {
      var cur = counts[col] || 0;
      if (cur > 0) {
        var old = col;
        while (cur > 0) {
          counts[old] = cur + 1;
          col = old + '.' + cur;
          cur = header.indexOf(col) >= 0 ? cur + 1 : (counts[col] || 0);
        }
      }
      header[idx] = col;
      counts[col] = cur + 1;
    });
    var rows = records.slice(1).map(function (r) {
      if (r.fields.length > header.length) {
        throw new Error('Expected ' + header.length + ' fields in line ' + r.line + ', saw ' + r.fields.length);
      }
      var o = {};
      header.forEach(function (h, k) { put(o, h, k < r.fields.length ? r.fields[k] : null); });
      return o;
    });
    return { columns: header, rows: rows };
  };

  // Internal column store: { columns, data: {name: [values]}, n }.
  function frame(table) {
    if (table.data) return table;
    var data = Object.create(null);
    table.columns.forEach(function (c) { data[c] = table.rows.map(function (r) { return r[c] === undefined ? null : r[c]; }); });
    return { columns: table.columns.slice(), data: data, n: table.rows.length };
  }
  function subset(f, idx) {
    var data = Object.create(null);
    f.columns.forEach(function (c) { data[c] = idx.map(function (i) { return f.data[c][i]; }); });
    return { columns: f.columns, data: data, n: idx.length };
  }
  function column(f, name) {
    if (f.columns.indexOf(name) < 0) throw new Error("KeyError: '" + pyStr(name) + "'");
    return f.data[name];
  }

  // ---------------------------------------------------------------------------------------
  // 5. GOV.UK Data Quality Issues Framework (framework.py)
  // ---------------------------------------------------------------------------------------

  var LEVELS = { 1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical' };
  var TARGET_RANGES = [[1, 3, [75.0, 90.0]], [4, 6, [90.0, 97.5]], [8, 9, [97.5, 99.9]], [12, 16, [99.9, 100.0]]];
  // Default target for each suggested range ("lo-hi"), per policy (decision D-021).
  DQ.TARGET_POLICIES = {
    low: { '75-90': 75.0, '90-97.5': 90.0, '97.5-99.9': 97.5, '99.9-100': 99.9 },
    mid: { '75-90': 85.0, '90-97.5': 95.0, '97.5-99.9': 99.0, '99.9-100': 100.0 },
    high: { '75-90': 89.9, '90-97.5': 97.4, '97.5-99.9': 99.8, '99.9-100': 100.0 }
  };
  DQ.DEFAULT_POLICY = 'low';
  var RESOLUTION = { Critical: 'Immediately', High: 'Within 1 measurement cycle',
    Medium: 'Within 3 measurement cycles', Low: 'Within 6 measurement cycles' };

  function checkLevel(name, value) {
    var v = typeof value === 'boolean' ? (value ? 1 : 0) : value;
    if (typeof v !== 'number' || !has(LEVELS, v)) throw new Error(name + ' must be 1, 2, 3 or 4 (got ' + pyRepr(value) + ')');
    return v;
  }
  DQ.combinedScore = function (importance, impact) { return checkLevel('importance', importance) * checkLevel('impact', impact); };
  DQ.targetRange = function (combined) {
    for (var i = 0; i < TARGET_RANGES.length; i++) {
      var t = TARGET_RANGES[i];
      if (Number.isInteger(combined) && combined >= t[0] && combined <= t[1]) return t[2].slice();
    }
    throw new Error('combined score ' + pyStr(combined) + ' is not a product of two 1-4 scores');
  };
  DQ.defaultTarget = function (combined, policy) {
    var p = policy === undefined ? DQ.DEFAULT_POLICY : policy;
    if (typeof p !== 'string' || !has(DQ.TARGET_POLICIES, p)) throw new Error('target policy must be low, mid or high, not ' + pyRepr(p));
    var r = DQ.targetRange(combined);
    return DQ.TARGET_POLICIES[p][r[0] + '-' + r[1]];
  };
  // Plain-English error rate: 95% -> "1 in 20 records".
  DQ.errorRate = function (percent) {
    var err = 100.0 - percent;
    if (err <= 0) return '0 records';
    var n = 100.0 / err;
    return '1 in ' + (n >= 10 ? fmtThousands0(n) : fmtG(n, 2)) + ' records';
  };
  // Performance bands below target (Table 4 method). null when the target is 100%.
  DQ.bands = function (target) {
    if (target >= 100.0) return null;
    var allowed = 100.0 - target, middle = Math.max(0.0, 100.0 - 2 * allowed), high = (middle + target) / 2;
    return { low: [0.0, middle], middle: [middle, high], high: [high, target] };
  };
  function bandFor(performance, target) {
    if (performance >= target) return [null, 0];
    var b = DQ.bands(target);
    if (b === null) return ['critical', 4];
    if (performance < b.middle[0]) return ['low', 3];
    if (performance < b.high[0]) return ['middle', 2];
    return ['high', 1];
  }
  function priorityFor(score) {
    if (score <= 0) return null;
    return score <= 7 ? 'Low' : score <= 16 ? 'Medium' : score <= 32 ? 'High' : 'Critical';
  }
  // Score one rule result. Returns the same keys and values as Python Assessment.to_dict().
  DQ.assess = function (importance, impact, performance, target, policy) {
    if (!(performance >= 0.0 && performance <= 100.0)) throw new Error('performance is a percentage between 0 and 100');
    var combined = DQ.combinedScore(importance, impact), rng = DQ.targetRange(combined);
    var tgt = (target === null || target === undefined) ? DQ.defaultTarget(combined, policy) : floatOrThrow(target);
    var b = bandFor(performance, tgt), score = checkLevel('importance', importance) * checkLevel('impact', impact) * b[1];
    var pr = priorityFor(score);
    return { importance: importance, impact: impact, combined: combined, target: tgt, target_range: rng,
      performance: pyRound(performance, 3), meets_target: b[0] === null, band: b[0], band_score: b[1],
      priority_score: score, priority: pr, resolution: pr ? RESOLUTION[pr] : null,
      error_rate_target: DQ.errorRate(tgt), error_rate_actual: DQ.errorRate(performance) };
  };

  // ---------------------------------------------------------------------------------------
  // 6. The 16 checks (rules.py). Each returns [checked, passed, examples, detail].
  // ---------------------------------------------------------------------------------------

  DQ.DEFAULT_ISSUE = { not_null: 'missing-value', required_columns: 'missing-field', unique: 'duplicate-reference',
    type: 'invalid-type', regex: 'pattern-mismatch', in_set: 'invalid-category', range: 'out-of-range',
    not_future: 'future-date', compare: 'cross-field-inconsistency', sum_max: 'totals-mismatch',
    freshness: 'stale-data', no_gaps: 'unexplained-gap', header_has_unit: 'undocumented-measure',
    not_unknown: 'characteristic-defaulted', group_disparity: 'group-disparity', identifier: 'invalid-identifier', outlier: 'implausible-value' };
  DQ.CONTROL_POINTS = ['source', 'pipeline', 'reporting'];
  DQ.DEFAULT_CONTROL = { not_null: 'source', required_columns: 'pipeline', unique: 'pipeline', type: 'source',
    outlier: 'source', regex: 'source', in_set: 'source', range: 'source', not_future: 'source', compare: 'source',
    sum_max: 'pipeline', freshness: 'pipeline', no_gaps: 'pipeline', header_has_unit: 'reporting',
    not_unknown: 'source', group_disparity: 'reporting', identifier: 'source' };
  var UNIT_TOKENS = ['%', 'percent', 'per cent', 'number', 'count', 'millions', 'million', 'billion',
    'thousand', '£', 'gbp', 'days', 'rate', 'miles', 'index', 'share', 'mean', 'average'];
  var UNKNOWN = ['unknown', 'not stated', 'not known', 'prefer not to say', 'z', 'x', 'u', ''];

  // Up to 5 failing rows, numbered as in the file (+2: header row, and counting from 1).
  function examples(f, mask, cols) {
    var out = [];
    for (var i = 0; i < f.n && out.length < 5; i++) {
      if (mask[i]) continue;
      var e = { row: i + 2 };
      cols.forEach(function (c) { var v = f.data[c][i]; put(e, c, v === null ? null : pyStr(v)); });
      out.push(e);
    }
    return out;
  }
  // numpy's default ("linear") quantile of sorted numbers (rules.py quantile), step for step.
  function quantile(xs, q) {
    var n = xs.length, v = n * q + (1 + q * -1) - 1, lo = Math.floor(v), g = v - lo;
    lo = Math.min(Math.max(lo, 0), n - 1);
    var hi = Math.min(lo + 1, n - 1), a = xs[lo], b = xs[hi], d = b - a;
    return g >= 0.5 ? b - d * (1 - g) : a + d * g;
  }
  function rowwise(f, cols, mask, detail) {
    return [mask.length, mask.filter(Boolean).length, examples(f, mask, cols), detail || {}];
  }
  function list(v) { return typeof v === 'string' ? [v] : v; }

  // Public sector identifiers (rules.py identifier_ok): format rules, plus check digits where the scheme has one.
  var POSTCODE_RE = /^(?:GIR ?0AA|[A-PR-UWYZ](?:[0-9]{1,2}|[A-HK-Y][0-9]{1,2}|[0-9][A-HJKPS-UW]|[A-HK-Y][0-9][ABEHMNPRV-Y]) ?[0-9][ABD-HJLNP-UW-Z]{2})$/;
  var NINO_RE = /^(?!BG|GB|KN|NK|NT|TN|ZZ)[A-CEGHJ-PR-TW-Z][A-CEGHJ-NPR-TW-Z][0-9]{6}[A-D]$/;
  var ID_FORMATS = { uprn: /^[0-9]{1,12}$/, gss_code: /^[EKLMNSW][0-9]{8}$/, company_number: /^(?:[0-9]{8}|[A-Z]{2}[0-9]{6})$/,
    charity_number: /^(?:[0-9]{6,7}|SC[0-9]{6}|NIC[0-9]{6})$/, school_urn: /^[0-9]{6}$/, ods_code: /^[A-Z0-9]{3,6}$/ };
  DQ.IDENTIFIER_SCHEMES = ['nhs_number', 'nino', 'uk_postcode', 'lei'].concat(Object.keys(ID_FORMATS));
  function nhsNumberOk(s) {
    s = s.replace(/ /g, '').replace(/-/g, '');
    if (!/^[0-9]{10}$/.test(s)) return false;
    var total = 0;
    for (var i = 0; i < 9; i++) total += Number(s[i]) * (10 - i);
    var check = 11 - (total % 11);
    if (check === 11) check = 0;
    return check !== 10 && check === Number(s[9]);
  }
  function leiOk(s) {
    if (!/^[A-Z0-9]{18}[0-9]{2}$/.test(s)) return false;
    var digits = s.split('').map(function (c) { return String(parseInt(c, 36)); }).join('');
    return BigInt(digits) % 97n === 1n;
  }
  DQ.identifierOk = function (value, scheme) {
    if (value === null || value === undefined) return false;
    var s = pyStrip(pyStr(value));
    if (s === '') return false;
    if (scheme === 'nhs_number') return nhsNumberOk(s);
    if (scheme === 'nino') return NINO_RE.test(s.replace(/ /g, ''));
    if (scheme === 'uk_postcode') return POSTCODE_RE.test(s);
    if (scheme === 'lei') return leiOk(s);
    if (scheme === 'uprn') return ID_FORMATS.uprn.test(s) && Number(s) > 0;
    if (has(ID_FORMATS, scheme)) return ID_FORMATS[scheme].test(s);
    throw new Error('unknown identifier scheme ' + pyRepr(scheme));
  };
  // Turn every in_valueset rule into an in_set rule (rules.py expand_valuesets). valuesets: {name: [{code, label}]}.
  DQ.expandValuesets = function (spec, valuesets) {
    (spec.rules || []).forEach(function (r) {
      if (r.check !== 'in_valueset') return;
      var rows = (valuesets || {})[r.valueset];
      if (!rows) throw new Error('unknown value set ' + pyRepr(r.valueset) + '; see vocab/valuesets/');
      var key = has(r, 'match') ? r.match : 'label';
      if (key !== 'label' && key !== 'code') throw new Error('rule ' + pyStr(r.id) + ': match must be label or code');
      r.check = 'in_set';
      r.values = rows.map(function (row) { return row[key]; });
      if (!has(r, 'description')) r.description = 'Value is in the ' + r.valueset + ' list';
    });
    return spec;
  };

  DQ.CHECKS = {
    identifier: function (f, r) {
      var c = req(r, 'column'), scheme = req(r, 'scheme');
      if (DQ.IDENTIFIER_SCHEMES.indexOf(scheme) < 0) throw new Error('unknown identifier scheme ' + pyRepr(scheme));
      return rowwise(f, [c], column(f, c).map(function (v) { return DQ.identifierOk(v, scheme); }), { scheme: scheme });
    },
    not_null: function (f, r) {
      var c = req(r, 'column');
      return rowwise(f, [c], column(f, c).map(function (v) { return v !== null && pyStrip(pyStr(v)) !== ''; }));
    },
    required_columns: function (f, r) {
      var want = req(r, 'columns');
      var missing = want.filter(function (c) { return f.columns.indexOf(c) < 0; });
      return [want.length, want.length - missing.length, missing.map(function (c) { return { missing_column: c }; }), {}];
    },
    unique: function (f, r) {
      var cols = list(req(r, 'columns')), data = cols.map(function (c) { return column(f, c); });
      var keys = [], seen = new Map();                          // blanks count as equal, as in pandas
      for (var i = 0; i < f.n; i++) {
        var key = JSON.stringify(data.map(function (d) { return d[i]; }));
        keys.push(key); seen.set(key, (seen.get(key) || 0) + 1);
      }
      return rowwise(f, cols, keys.map(function (k) { return seen.get(k) === 1; }));
    },
    type: function (f, r) {
      var c = req(r, 'column'), kind = req(r, 'kind');
      return rowwise(f, [c], column(f, c).map(function (v) { return isType(v, kind); }), { kind: kind });
    },
    regex: function (f, r) {
      var c = req(r, 'column'), re = translateRegex(req(r, 'pattern'));
      return rowwise(f, [c], column(f, c).map(function (v) { return v !== null && re.test(pyStr(v)); }));
    },
    in_set: function (f, r) {
      var c = req(r, 'column'), allowed = new Set(req(r, 'values').map(pyStr));
      return rowwise(f, [c], column(f, c).map(function (v) { return v !== null && allowed.has(pyStr(v)); }));
    },
    // Valid but implausible numbers (rules.py check_outlier): only numbers count.
    outlier: function (f, r) {
      var c = req(r, 'column'), method = get(r, 'method', 'iqr');
      var num = pdNumericColumn(column(f, c).map(function (v) { return pyStr(v === null ? NaN : v).replace(/,/g, ''); })).vals;
      var okNum = num.map(function (x) { return !isNaN(x) && Math.abs(x) !== Infinity; });
      var vals = num.filter(function (x, i) { return okNum[i]; });
      if (vals.length < 4) return [vals.length, vals.length, [], { method: method, note: 'fewer than 4 numbers, nothing to compare' }];
      var lo, hi, detail;
      if (method === 'zscore') {
        var t = get(r, 'threshold', 3), mean = pySum(vals) / vals.length;
        var sd = Math.sqrt(pySum(vals.map(function (x) { return (x - mean) * (x - mean); })) / (vals.length - 1));
        if (sd > 0) { lo = mean - t * sd; hi = mean + t * sd; } else { lo = mean; hi = mean; }
        detail = { method: 'zscore', threshold: t, mean: pyRound(mean, 4), sd: pyRound(sd, 4) };
      } else if (method === 'iqr') {
        var k = get(r, 'k', 1.5), xs = vals.slice().sort(function (a, b) { return a - b; });
        var q1 = quantile(xs, 0.25), q3 = quantile(xs, 0.75);
        lo = q1 - k * (q3 - q1); hi = q3 + k * (q3 - q1);
        detail = { method: 'iqr', k: k, q1: pyRound(q1, 4), q3: pyRound(q3, 4) };
      } else throw new Error('outlier method must be iqr or zscore, not ' + pyRepr(method));
      detail.low = pyRound(lo, 4); detail.high = pyRound(hi, 4);
      var mask = num.map(function (x, i) { return !okNum[i] || (x >= lo && x <= hi); });
      return [vals.length, mask.filter(function (m, i) { return m && okNum[i]; }).length, examples(f, mask, [c]), detail];
    },
    range: function (f, r) {
      var c = req(r, 'column');
      var num = pdNumericColumn(column(f, c).map(function (v) { return v === null ? null : pyStr(v).replace(/,/g, ''); })).vals;
      var mask = num.map(function (x) {
        return !isNaN(x) && (!has(r, 'min') || x >= r.min) && (!has(r, 'max') || x <= r.max);
      });
      return rowwise(f, [c], mask, { min: get(r, 'min', null), max: get(r, 'max', null) });
    },
    not_future: function (f, r, asOf) {
      var c = req(r, 'column');
      var mask = column(f, c).map(function (v) { var d = parseDate(v); return d !== null && d.ord <= asOf.ord; });
      return rowwise(f, [c], mask, { as_of: asOf.iso });
    },
    compare: function (f, r) {
      var left = req(r, 'left'), op = req(r, 'op'), right = req(r, 'right');
      var OPS = { '<': function (a, b) { return a < b; }, '<=': function (a, b) { return a <= b; },
        '>': function (a, b) { return a > b; }, '>=': function (a, b) { return a >= b; },
        '==': function (a, b) { return a === b; }, '!=': function (a, b) { return a !== b; } };
      if (!has(OPS, op)) throw new Error("KeyError: " + pyRepr(op));
      var a = pdNumericColumn(column(f, left)).vals, isCol = f.columns.indexOf(right) >= 0;
      var b = isCol ? pdNumericColumn(column(f, right)).vals : floatOrThrow(right);
      var mask = a.map(function (x, i) { return OPS[op](x, isCol ? b[i] : b); });
      return rowwise(f, [left].concat(isCol ? [right] : []), mask,
        { expression: pyStr(left) + ' ' + pyStr(op) + ' ' + pyStr(right) });
    },
    sum_max: function (f, r) {
      var nc = pdNumericColumn(column(f, req(r, 'column')));
      var total = nc.ints ? Number(nc.ints.reduce(function (s, x) { return s + x; }, BigInt(0)))
        : pairwiseSum(nc.vals.map(function (x) { return isNaN(x) ? 0 : x; }), 0, nc.vals.length);
      var ok = total <= req(r, 'max') + get(r, 'tolerance', 0), s = pyRound(total, 4);
      return [1, ok ? 1 : 0, ok ? [] : [{ sum: s, max: r.max }], { sum: s }];
    },
    // Dataset level: is the latest period recent enough for the stated update frequency?
    freshness: function (f, r, asOf) {
      var vals = column(f, req(r, 'column')).filter(function (v) { return v !== null; })
        .map(function (v) { return pyStrip(pyStr(v)); }).filter(function (v) { return v !== ''; });
      var latest = null;
      if (vals.length && vals.every(function (v) { return /^\p{Nd}{4}$/u.test(v); })) {
        var y = Math.max.apply(null, vals.map(pyInt));
        latest = mkDate(y, 12, 31);                             // a year label covers the whole year
        if (!latest) throw new Error('year ' + y + ' is out of range');
      } else {
        vals.forEach(function (v) { var d = parseDate(v); if (d && (!latest || d.ord > latest.ord)) latest = d; });
        if (!latest) return [1, 0, [{ reason: 'no readable dates' }], {}];
      }
      var lag = get(r, 'lag', 'P0D'), allowed = isoDurationDays(req(r, 'expected')) + isoDurationDays(lag);
      var age = asOf.ord - latest.ord, ok = age <= allowed;
      var detail = { latest_period: latest.iso, age_days: age, allowed_days: pyRound(allowed, 0),
        expected: r.expected, lag: lag, as_of: asOf.iso };
      return [1, ok ? 1 : 0, ok ? [] : [detail], detail];
    },
    no_gaps: function (f, r) {
      var set = new Set();
      column(f, req(r, 'column')).forEach(function (v) {
        var s4 = Array.from(v === null ? 'nan' : pyStr(v)).slice(0, 4).join('');
        if (isType(s4, 'year')) set.add(pyInt(s4));
      });
      var years = Array.from(set).sort(function (a, b) { return a - b; });
      if (!years.length) return [1, 0, [{ reason: 'no years found' }], {}];
      var step = get(r, 'step', 1), expected = [], y;
      if (step === 0) throw new Error('range() arg 3 must not be zero');
      for (y = years[0]; step > 0 ? y < years[years.length - 1] + 1 : y > years[years.length - 1] + 1; y += step) expected.push(y);
      var missing = expected.filter(function (x) { return !set.has(x); });
      return [expected.length, expected.length - missing.length,
        missing.slice(0, 5).map(function (x) { return { missing_period: x }; }),
        { first: years[0], last: years[years.length - 1] }];
    },
    header_has_unit: function (f, r) {
      var ignore = get(r, 'ignore', []);
      var cols = truthy(get(r, 'columns', null)) ? r.columns : f.columns.filter(function (c) { return ignore.indexOf(c) < 0; });
      var tokens = get(r, 'tokens', UNIT_TOKENS).map(function (t) { return t.toLowerCase(); });
      var flags = new Map();                                    // Python: a dict, so repeats count once
      cols.forEach(function (c) {
        var name = pyStr(c).toLowerCase();
        flags.set(c, tokens.some(function (t) { return name.indexOf(t) >= 0; }));
      });
      var bad = [], ok = 0;
      flags.forEach(function (v, c) { if (v) ok++; else bad.push({ column: c }); });
      return [cols.length, ok, bad, {}];
    },
    not_unknown: function (f, r) {
      var c = req(r, 'column');
      var unknown = new Set(get(r, 'values', UNKNOWN).map(function (v) { return pyStrip(pyStr(v)).toLowerCase(); }));
      return rowwise(f, [c], column(f, c).map(function (v) { return v !== null && !unknown.has(pyStrip(pyStr(v)).toLowerCase()); }));
    },
    // Run an inner check per group; pass if the gap between best and worst group is within tolerance.
    group_disparity: function (f, r, asOf) {
      var inner = Object.assign({}, req(r, 'inner')), gcol = column(f, req(r, 'group'));
      var groups = new Map(), nan = [];
      gcol.forEach(function (v, i) {
        if (v === null) { nan.push(i); return; }
        var k = pyStr(v); if (!groups.has(k)) groups.set(k, []); groups.get(k).push(i);
      });
      var keys = pySorted(Array.from(groups.keys())), parts = keys.map(function (k) { return [k, groups.get(k)]; });
      if (nan.length) parts.push(['nan', nan]);                 // pandas puts the blank group last
      var check = req(inner, 'check');
      if (!has(DQ.CHECKS, check)) throw new Error('KeyError: ' + pyRepr(check));
      var rates = {};
      parts.forEach(function (p) {
        var res = DQ.CHECKS[check](subset(f, p[1]), inner, asOf);
        put(rates, p[0], res[0] ? pyRound(100.0 * res[1] / res[0], 3) : 100.0);
      });
      var vals = Object.keys(rates).map(function (k) { return rates[k]; });
      var gap = vals.length ? Math.max.apply(null, vals) - Math.min.apply(null, vals) : 0.0;
      var ok = gap <= get(r, 'tolerance', 5.0), gp = pyRound(gap, 3);
      return [1, ok ? 1 : 0, ok ? [] : [{ gap_points: gp, by_group: rates }], { by_group: rates, gap_points: gp }];
    }
  };

  // ---------------------------------------------------------------------------------------
  // 7. Running a rules file (rules.validate_spec, rules.run, rules.summarise)
  // ---------------------------------------------------------------------------------------

  DQ.setVocab = function (issueTypes, dimensions) {
    ISSUE_TYPES = {};
    Object.keys(issueTypes).forEach(function (k) {
      var t = Object.assign({}, issueTypes[k]);
      t.default_impact = Number(t.default_impact);
      ISSUE_TYPES[k] = t;
    });
    if (dimensions) DIMENSIONS = dimensions;
  };
  DQ.setDimensions = function (dimensions) { DIMENSIONS = dimensions; };
  function vocab() {
    if (!ISSUE_TYPES) throw new Error('Call DQ.setVocab(issueTypes) first');
    return ISSUE_TYPES;
  }

  DQ.validateSpec = function (spec) {
    if (!has(spec, 'asset') || !has(spec, 'rules')) throw new Error("a rules file needs 'asset' and 'rules'");
    checkLevel('asset.importance', get(spec.asset, 'importance', 3));
    var pol = get(spec.asset, 'target_policy', DQ.DEFAULT_POLICY);
    if (typeof pol !== 'string' || !has(DQ.TARGET_POLICIES, pol)) throw new Error('asset.target_policy must be low, mid or high');
    var seen = new Set();
    spec.rules.forEach(function (r) {
      var check = get(r, 'check', null);
      if (typeof check !== 'string' || !has(DQ.CHECKS, check)) {
        throw new Error('rule ' + pyStr(get(r, 'id', null)) + ': unknown check ' + pyRepr(check));
      }
      var id = req(r, 'id'), key = typeof id + ':' + pyStr(id);
      if (seen.has(key)) throw new Error('duplicate rule id ' + pyStr(id));
      seen.add(key);
      if (check === 'identifier' && DQ.IDENTIFIER_SCHEMES.indexOf(get(r, 'scheme', null)) < 0) {
        throw new Error('rule ' + pyStr(id) + ': scheme must be one of ' + DQ.IDENTIFIER_SCHEMES.join(', '));
      }
      if (DQ.CONTROL_POINTS.indexOf(get(r, 'control_point', 'source')) < 0) {
        throw new Error('rule ' + pyStr(id) + ': control_point must be source, pipeline or reporting');
      }
      var it = get(r, 'issue_type', DQ.DEFAULT_ISSUE[check]);
      if (typeof it !== 'string' || !has(vocab(), it)) throw new Error('rule ' + pyStr(id) + ': unknown issue type ' + pyRepr(it));
    });
  };

  DQ.run = function (table, spec, asOfISO) {
    var f = frame(table), asOf = parseAsOf(asOfISO), asset = spec.asset, IT = vocab();
    var importance = pyInt(get(asset, 'importance', 3)), policy = get(asset, 'target_policy', DQ.DEFAULT_POLICY);
    var results = spec.rules.map(function (r) {
      var check = req(r, 'check'), issue = get(r, 'issue_type', DQ.DEFAULT_ISSUE[check]);
      if (!has(IT, issue)) throw new Error("KeyError: " + pyRepr(issue));
      var meta = IT[issue], dimension = get(r, 'dimension', meta.dimension);
      var impact = pyInt(get(r, 'impact', meta.default_impact));
      var extra = get(r, 'columns', []);
      var cols = [get(r, 'column', null), get(r, 'left', null), get(r, 'right', null), get(r, 'group', null)]
        .filter(truthy).concat(typeof extra === 'string' ? Array.from(extra) : extra);
      var exempt = ['required_columns', 'compare', 'header_has_unit'].indexOf(check) >= 0;
      var missing = cols.filter(function (c) { return f.columns.indexOf(c) < 0 && !exempt; });
      var out;
      if (missing.length) {
        out = [1, 0, missing.map(function (c) { return { missing_column: c }; }), {}];
        issue = 'missing-field'; dimension = 'completeness';
      } else {
        if (!has(DQ.CHECKS, check)) throw new Error('KeyError: ' + pyRepr(check));
        out = DQ.CHECKS[check](f, r, asOf);
      }
      var checked = out[0], passed = out[1], perf = checked ? 100.0 * passed / checked : 100.0;
      var a = DQ.assess(importance, impact, perf, get(r, 'target', null), policy);
      var m = {};
      ['purpose', 'requirement', 'method', 'notes', 'part_of_data', 'personal_data'].forEach(function (k) { if (has(r, k)) m[k] = r[k]; });
      m.control_point = get(r, 'control_point', DQ.DEFAULT_CONTROL[check]);
      return { id: req(r, 'id'), check: check, description: get(r, 'description', check), dimension: dimension,
        issue_type: issue, columns: cols, checked: checked, passed: passed, performance: pyRound(perf, 3),
        examples: out[2], detail: out[3], assessment: a, meta: m, failed: checked - passed };
    });
    return summarise(asset, results, asOf, f.n);
  };

  function summarise(asset, results, asOf, nRows) {
    var dims = {}, perfs = {};
    results.forEach(function (r) {
      if (!has(dims, r.dimension)) { dims[r.dimension] = { rules: 0, met: 0 }; perfs[r.dimension] = []; }
      dims[r.dimension].rules += 1;
      dims[r.dimension].met += r.assessment.meets_target ? 1 : 0;
      perfs[r.dimension].push(r.performance);
    });
    Object.keys(dims).forEach(function (k) { dims[k].mean_performance = pyRound(pySum(perfs[k]) / perfs[k].length, 3); });
    var order = { Critical: 0, High: 1, Medium: 2, Low: 3 };
    var issues = results.filter(function (r) { return !r.assessment.meets_target; });
    issues.sort(function (x, y) {                              // stable, like Python's sort
      var a = has(order, x.assessment.priority) ? order[x.assessment.priority] : 9;
      var b = has(order, y.assessment.priority) ? order[y.assessment.priority] : 9;
      return a !== b ? a - b : y.assessment.priority_score - x.assessment.priority_score;
    });
    return { asset: asset, as_of: asOf.iso, rows: nRows, rules_total: results.length,
      rules_met: results.length - issues.length, dimensions: dims,
      issues: issues.map(function (r) {
        return { rule: r.id, issue_type: r.issue_type, label: ISSUE_TYPES[r.issue_type].label, dimension: r.dimension,
          priority: r.assessment.priority, resolution: r.assessment.resolution, performance: r.performance,
          target: r.assessment.target };
      }),
      results: results };
  }

  // ---------------------------------------------------------------------------------------
  // 8. Trust level, DQAP route, issue operations, DQV and DQAP exports
  // ---------------------------------------------------------------------------------------

  var TRUST_LEVELS = ['Untrustworthy', 'Requires improvement', 'Useable', 'Trustworthy'];
  var SHARING = { 'Untrustworthy': 'Internal use only', 'Requires improvement': 'Internal use only',
    'Useable': 'Can be used externally, with caveats', 'Trustworthy': 'Can be used externally' };
  var CROSSWALK = {
    'Untrustworthy': { mhclg_quality_ladder: 'none / some', ndl_rag: 'red' },
    'Requires improvement': { mhclg_quality_ladder: 'indicative / verifiable', ndl_rag: 'red' },
    'Useable': { mhclg_quality_ladder: 'authoritative / usable', ndl_rag: 'amber' },
    'Trustworthy': { mhclg_quality_ladder: 'trustworthy', ndl_rag: 'green' } };
  var CORE = ['completeness', 'uniqueness', 'consistency', 'timeliness', 'validity', 'accuracy'];

  // Suggested IOPC-style trust level with reasons (trust.classify).
  DQ.trust = function (result, personalDataColumns) {
    var personal = truthy(personalDataColumns) ? personalDataColumns : get(get(result, 'asset', {}), 'personal_data_columns', []);
    var FROM = { Critical: 0, High: 1, Medium: 2, Low: 3 }, reasons = [], level = 3, actionPlan = false;
    result.results.forEach(function (r) {
      var pr = r.assessment.priority;
      if (pr !== null && pr !== undefined && FROM[pr] < level) {
        level = FROM[pr];
        reasons.push(pr + ' priority issue on ' + pyStr(r.id) + ' (' + pyStr(r.description) + '): ' + pyFloatRepr(r.performance) +
          '% against a ' + pyFloatRepr(r.assessment.target) + '% target');
      }
    });
    result.results.forEach(function (r) {
      var isPersonal = truthy(get(get(r, 'meta', {}), 'personal_data', null)) ||
        r.columns.some(function (c) { return personal.indexOf(c) >= 0; });
      if (isPersonal && r.dimension === 'accuracy') {
        if (r.performance < 100) actionPlan = true;
        if (r.performance < 90 && level > 2) {
          level = 2;
          reasons.push('Accuracy of personal data on ' + pyStr(r.id) + ' is ' + pyFloatRepr(r.performance) +
            '%, below 90%, so the data cannot be rated Trustworthy');
        }
      }
    });
    var measured = pySorted(Array.from(new Set(result.results.map(function (r) { return r.dimension; })))
      .filter(function (d) { return CORE.indexOf(d) >= 0; }));
    if (measured.length < 3 && level > 2) {
      level = 2;
      reasons.push('Only ' + measured.length + ' of the 6 core dimensions were measured (' + (measured.join(', ') || 'none') +
        "), so there isn't enough evidence for Trustworthy");
    }
    if (!reasons.length) reasons.push('All rules meet their targets, or only Low priority issues remain');
    var name = TRUST_LEVELS[level];
    return { level: name, sharing: SHARING[name], reasons: reasons, action_plan_required: actionPlan || level < 3,
      dimensions_measured: measured, crosswalk: Object.assign({}, CROSSWALK[name]),
      note: 'Suggested level. The data owner confirms or overrides it, with reasons (IOPC approach).' };
  };

  // Which DQAP route fits the asset (pathway.route, the 2023 decision tree).
  DQ.route = function (asset) {
    var source = get(asset, 'source', 'internal'), influence = truthy(get(asset, 'influence', source === 'internal'));
    var adequate = get(asset, 'fields_adequate', true), canEnrich = get(asset, 'can_enrich', false);
    var steps = ['Determine and define the use cases and stakeholders', 'Assess the data structure'];
    if (adequate === false) {
      if (source === 'internal' || influence) {
        steps.push('Tell stakeholders or suppliers what fields the quality use cases need',
          'Work with them to add the fields, or understand and record the limitations',
          'Record any additions in the provenance information');
      } else if (truthy(canEnrich)) {
        steps.push('Add the fields the quality use cases need', 'Record the additions in the provenance information');
      } else {
        steps.push('Communicate the limitations to stakeholders, and record them in the metadata and the DQAP');
      }
    }
    steps.push('Define domain-appropriate data quality assessment parameters (the rules file)',
      'Record them in the DQAP', 'Measure data quality against the planned parameters',
      'Store and visualise the results in an accessible format',
      'Check the assessment meets its stated aims; if not, revise the parameters',
      'Communicate the results to stakeholders', 'Make changes to improve data quality where appropriate',
      'Repeat at a frequency that meets the original requirements');
    var label, resp;
    if (source === 'external' && !influence) {
      label = 'External data, no influence: assess, caveat and communicate';
      resp = 'Fixes sit with the supplier. Your job is to measure, record limitations and tell users.';
    } else if (source === 'external') {
      label = 'External data, some influence: assess and work with the supplier';
      resp = 'Agree fixes with the supplier and record them in the DQAP actions.';
    } else {
      label = 'Internal data: assess and fix at source';
      resp = 'Fix root causes in your own processes and systems.';
    }
    return { route: label, responsibility: resp, steps: steps, source: source, influence: influence,
      basis: 'Data Quality Assessment Decision Tree (government data quality community, July 2023)' };
  };

  // Issue ageing, overdue issues and recurrence (operations.assess).
  // historyRows: [{date, rule_id, value, target, meets_target}] as in the history CSV.
  var WINDOW = { Critical: 1, High: 1, Medium: 3, Low: 6 };
  DQ.operations = function (result, historyRows) {
    var runs = new Map();
    function put(id, date, ok) { if (!runs.has(id)) runs.set(id, new Map()); runs.get(id).set(date, ok); }
    (historyRows || []).forEach(function (h) { put(h.rule_id, h.date, String(h.meets_target).toLowerCase() === 'true'); });
    result.results.forEach(function (r) { put(r.id, result.as_of, !!r.assessment.meets_target); });
    var all = new Set();
    runs.forEach(function (v) { v.forEach(function (_, d) { all.add(d); }); });
    var dates = pySorted(Array.from(all)), perRule = {};
    result.results.forEach(function (r) {
      var run = runs.get(r.id), series = dates.filter(function (d) { return run.has(d); }).map(function (d) { return run.get(d); });
      var age = 0, i;
      for (i = series.length - 1; i >= 0 && !series[i]; i--) age++;
      var rec = 0, seenFail = false, prev = null;               // a failure after a pass, after an earlier failure
      series.forEach(function (ok) {
        if (ok === false && prev === true && seenFail) rec++;
        if (ok === false) seenFail = true;
        prev = ok;
      });
      var pr = r.assessment.priority, overdue = truthy(pr) && age > (has(WINDOW, pr) ? WINDOW[pr] : 99);
      perRule[r.id] = { open: age > 0, cycles_open: age, priority: pr, recurrences: rec, overdue: overdue,
        escalate_to: overdue && (pr === 'Critical' || pr === 'High') ? 'Data owner and governance board' : overdue ? 'Data owner' : '' };
    });
    var total = result.results.length || 1;
    var failing = result.results.filter(function (r) { return !r.assessment.meets_target; });
    var everFailed = [];
    runs.forEach(function (v, k) { if (Array.from(v.values()).indexOf(false) >= 0) everFailed.push(k); });
    var vals = Object.keys(perRule).map(function (k) { return perRule[k]; });
    var open = vals.filter(function (v) { return v.open; });
    return {
      cycles_measured: dates.length,
      defect_volume: failing.reduce(function (s, r) { return s + (pyInt(r.checked) - pyInt(r.passed)); }, 0),
      control_failure_rate: pyRound(100 * failing.length / total, 1),
      open_issues: open.length,
      overdue_issues: vals.filter(function (v) { return v.overdue; }).length,
      mean_cycles_open: pyRound(open.reduce(function (s, v) { return s + v.cycles_open; }, 0) / Math.max(1, open.length), 1),
      recurrence_rate: pyRound(100 * everFailed.filter(function (k) { return has(perRule, k) && truthy(perRule[k].recurrences); }).length /
        Math.max(1, everFailed.length), 1),
      rules: perRule
    };
  };

  // W3C Data Quality Vocabulary (DQV) JSON-LD (dqv.result_to_dqv).
  var BASE = 'https://cyberdudeuk.github.io/ndl-dq-assurance/vocab#';
  DQ.DQV_CONTEXT = { dcat: 'http://www.w3.org/ns/dcat#', dct: 'http://purl.org/dc/terms/', dqv: 'http://www.w3.org/ns/dqv#',
    prov: 'http://www.w3.org/ns/prov#', skos: 'http://www.w3.org/2004/02/skos/core#', xsd: 'http://www.w3.org/2001/XMLSchema#',
    oa: 'http://www.w3.org/ns/oa#', ndq: BASE, value: { '@id': 'dqv:value', '@type': 'xsd:decimal' },
    measuredOn: { '@id': 'dct:date', '@type': 'xsd:date' } };
  DQ.toDQV = function (result, assetIri, dqapIri) {
    if (!DIMENSIONS) throw new Error('Call DQ.setVocab(issueTypes, dimensions) first');
    var asset = result.asset, IT = vocab();
    var iri = truthy(assetIri) ? assetIri : truthy(get(asset, 'iri', null)) ? asset.iri : BASE + 'asset/' + pyStr(asset.id);
    var measurements = [], annotations = [], metrics = new Map();
    result.results.forEach(function (r) {
      var metricIri = BASE + 'metric/' + pyStr(asset.id) + '/' + pyStr(r.id);
      metrics.set(metricIri, { '@id': metricIri, '@type': 'dqv:Metric', 'skos:prefLabel': r.description,
        'dqv:expectedDataType': { '@id': 'xsd:decimal' }, 'dqv:inDimension': { '@id': 'ndq:' + r.dimension } });
      measurements.push({ '@id': iri + '#m-' + pyStr(r.id), '@type': 'dqv:QualityMeasurement',
        'dqv:computedOn': { '@id': iri }, 'dqv:isMeasurementOf': { '@id': metricIri },
        value: r.performance, measuredOn: result.as_of, 'ndq:target': r.assessment.target,
        'ndq:meetsTarget': r.assessment.meets_target, 'ndq:recordsChecked': r.checked });
      if (!r.assessment.meets_target) {
        var it = IT[r.issue_type];
        annotations.push({ '@id': iri + '#issue-' + pyStr(r.id), '@type': 'dqv:QualityAnnotation',
          'oa:hasTarget': { '@id': iri }, 'oa:motivatedBy': { '@id': 'dqv:qualityAssessment' },
          'oa:hasBody': { '@type': 'oa:TextualBody', 'oa:value': it.label + ': ' + it.definition },
          'ndq:issueType': { '@id': 'ndq:issue/' + r.issue_type },
          'ndq:priority': r.assessment.priority, 'ndq:resolution': r.assessment.resolution,
          'ndq:responsibility': it.responsibility });
      }
    });
    var ds = { '@id': iri, '@type': 'dcat:Dataset', 'dct:title': get(asset, 'title', asset.id) };
    if (truthy(get(asset, 'owner', null))) ds['dct:publisher'] = asset.owner;
    if (truthy(dqapIri)) ds['ndq:dataQualityActionPlan'] = { '@id': dqapIri };
    ds['dqv:hasQualityMeasurement'] = measurements.map(function (m) { return { '@id': m['@id'] }; });
    ds['dqv:hasQualityAnnotation'] = annotations.map(function (a) { return { '@id': a['@id'] }; });
    var graph = [ds].concat(measurements, annotations, Array.from(metrics.values()));
    Object.keys(DIMENSIONS).forEach(function (k) {
      if (result.results.some(function (r) { return r.dimension === k; })) {
        graph.push({ '@id': 'ndq:' + k, '@type': 'dqv:Dimension', 'skos:prefLabel': DIMENSIONS[k].label,
          'skos:definition': DIMENSIONS[k].definition, 'dqv:inCategory': { '@id': 'ndq:GovernmentDataQualityFramework' } });
      }
    });
    return { '@context': DQ.DQV_CONTEXT, '@graph': graph };
  };

  // GOV.UK DQAP template rows as CSV text (exporters.to_dqap_csv). Python csv.writer conventions.
  function csvLine(fields) {
    if (fields.length === 1 && fields[0] === '') return '""\r\n';
    return fields.map(function (v) {
      var s = v === null || v === undefined ? '' : String(v);
      return /[",\r\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
    }).join(',') + '\r\n';
  }
  DQ.toDqapCsv = function (result) {
    var asset = result.asset, IT = vocab(), n = 0;
    var rules = csvLine(['Critical data item', 'Rule ID', 'Rule description', 'Dimension', 'Measure', 'Importance (1-4)',
      'Impact (1-4)', 'Combined score', 'Target (%)', 'Baseline (%)', 'Date measured']);
    var issues = csvLine(['Issue ID', 'Rule ID', 'Issue type', 'Description', 'Dimension', 'Performance (%)', 'Target (%)',
      'Band', 'Priority score', 'Priority', 'Resolution timescale', 'Responsibility', 'Owner', 'Status']);
    result.results.forEach(function (r) {
      var a = r.assessment;
      rules += csvLine([r.columns.map(pyStr).join(', ') || '(dataset)', pyStr(r.id), pyStr(r.description), r.dimension, r.check,
        pyStr(a.importance), pyStr(a.impact), pyStr(a.combined), pyFloatRepr(a.target), pyFloatRepr(r.performance), result.as_of]);
      if (!a.meets_target) {
        n += 1;
        var it = IT[r.issue_type];
        var owner = truthy(get(asset, 'steward', null)) ? asset.steward : truthy(get(asset, 'owner', null)) ? asset.owner : '';
        issues += csvLine([pyStr(asset.id) + '-I' + String(n).padStart(3, '0'), pyStr(r.id), it.label, it.definition, r.dimension,
          pyFloatRepr(r.performance), pyFloatRepr(a.target), a.band, pyStr(a.priority_score), a.priority, a.resolution,
          it.responsibility, pyStr(owner), 'Open']);
      }
    });
    return { rules: rules, issues: issues };
  };

  // ---------- Reconciliation of two versions of a dataset (reconcile.py) ----------
  DQ.reconcile = function (source, target, keys, tolerance, maxExamples) {
    keys = typeof keys === 'string' ? [keys] : keys.slice(); tolerance = tolerance || 0; maxExamples = maxExamples === undefined ? 5 : maxExamples;
    if (!keys.length) throw new Error('choose at least one key column');
    var S = frame(source), T = frame(target), SEP = '\u001f';
    var missing = keys.filter(function (k) { return S.columns.indexOf(k) < 0 || T.columns.indexOf(k) < 0; });
    if (missing.length) throw new Error('key column(s) not in both files: ' + missing.join(', '));
    function keyList(f) { var out = []; for (var i = 0; i < f.n; i++) out.push(keys.map(function (k) { var v = f.data[k][i]; return v === null ? '' : pyStr(v); }).join(SEP)); return out; }
    var sk = keyList(S), tk = keyList(T), sset = new Set(sk), tset = new Set(tk);
    function dups(ks) { var seen = new Set(), d = [], dset = new Set(); ks.forEach(function (k) { if (seen.has(k) && !dset.has(k)) { d.push(k); dset.add(k); } seen.add(k); }); return d; }
    function only(a, b) { var out = [], seen = new Set(); a.forEach(function (k) { if (!b.has(k) && !seen.has(k)) { out.push(k); seen.add(k); } }); return out; }
    var onlyS = only(sk, tset), onlyT = only(tk, sset), dupS = dups(sk), dupT = dups(tk), split = function (k) { return k.split(SEP); };
    var colsMissing = S.columns.filter(function (c) { return T.columns.indexOf(c) < 0; }), colsExtra = T.columns.filter(function (c) { return S.columns.indexOf(c) < 0; });
    var common = S.columns.filter(function (c) { return T.columns.indexOf(c) >= 0 && keys.indexOf(c) < 0; });
    function numericTotal(vals) {
      var filled = vals.filter(function (v) { return v !== null; }).length;
      var nc = pdNumericColumn(vals), ok = nc.vals.filter(function (x) { return !isNaN(x); }).length;
      if (!(filled > 0 && ok === filled)) return null;
      return nc.ints ? Number(nc.ints.reduce(function (s, x) { return s + x; }, BigInt(0))) : pairwiseSum(nc.vals.map(function (x) { return isNaN(x) ? 0 : x; }), 0, nc.vals.length);
    }
    var totals = [];
    common.forEach(function (c) {
      var a = numericTotal(S.data[c]), b = numericTotal(T.data[c]);
      if (a === null || b === null) return;
      var s = pyRound(a, 6), t = pyRound(b, 6), d = pyRound(t - s, 6);
      totals.push({ column: c, source: s, target: t, difference: d, ok: Math.abs(d) <= tolerance });
    });
    var firstS = new Map(), firstT = new Map();
    sk.forEach(function (k, i) { if (!firstS.has(k)) firstS.set(k, i); });
    tk.forEach(function (k, i) { if (!firstT.has(k)) firstT.set(k, i); });
    var matched = []; firstS.forEach(function (_, k) { if (firstT.has(k)) matched.push(k); });
    var mismatches = [];
    common.forEach(function (c) {
      var n = 0, ex = [];
      matched.forEach(function (k) {
        var a = S.data[c][firstS.get(k)], b = T.data[c][firstT.get(k)];
        a = a === null ? null : pyStr(a); b = b === null ? null : pyStr(b);
        if (a !== b) { n++; if (ex.length < maxExamples) ex.push({ key: split(k), source: a, target: b }); }
      });
      if (n) mismatches.push({ column: c, count: n, examples: ex });
    });
    var passed = S.n === T.n && !onlyS.length && !onlyT.length && !dupS.length && !dupT.length && !colsMissing.length &&
      totals.every(function (x) { return x.ok; }) && !mismatches.length;
    return { keys: keys, rows: { source: S.n, target: T.n }, matched: matched.length,
      only_in_source: { count: onlyS.length, examples: onlyS.slice(0, maxExamples).map(split) },
      only_in_target: { count: onlyT.length, examples: onlyT.slice(0, maxExamples).map(split) },
      duplicate_keys: { source: dupS.length, target: dupT.length, examples: dupS.concat(dupT).slice(0, maxExamples).map(split) },
      columns_missing_in_target: colsMissing, columns_extra_in_target: colsExtra, totals: totals, mismatches: mismatches, passed: passed };
  };

  // ---------- Exports to Great Expectations and R validate (exporters.py) ----------
  (function () {
    var E = {};
    function issueOf(r) { return vocab()[has(r, 'issue_type') ? r.issue_type : DQ.DEFAULT_ISSUE[r.check]]; }
    function mostly(r, imp, policy) {
      var impact = pyInt(has(r, 'impact') ? r.impact : issueOf(r).default_impact);
      var target = r.target ? r.target : DQ.defaultTarget(DQ.combinedScore(imp, impact), policy);
      return pyRound(Number(target) / 100.0, 4);
    }
    // Python json.dumps (ensure_ascii) for a string
    function pyJson(s) { return JSON.stringify(String(s)).replace(/[\u007f-￿]/g, function (ch) { return '\\u' + ('000' + ch.charCodeAt(0).toString(16)).slice(-4); }); }
    function num(x) { return typeof x === 'number' && Number.isInteger(x) ? String(x) : pyStr(x); }
    function rName(c) { return '`' + String(c).replace(/`/g, '') + '`'; }
    E.toGreatExpectations = function (spec) {
      var imp = pyInt(get(spec.asset, 'importance', 3)), policy = get(spec.asset, 'target_policy', DQ.DEFAULT_POLICY), out = [], unsupported = [];
      spec.rules.forEach(function (r) {
        var c = r.check, m = mostly(r, imp, policy), et = null, kw = null;
        var meta = { rule_id: r.id, dimension: has(r, 'dimension') ? r.dimension : issueOf(r).dimension, description: get(r, 'description', '') };
        if (c === 'not_null') { et = 'expect_column_values_to_not_be_null'; kw = { column: r.column, mostly: m }; }
        else if (c === 'unique') {
          if (r.columns.length === 1) { et = 'expect_column_values_to_be_unique'; kw = { column: r.columns[0], mostly: m }; }
          else { et = 'expect_compound_columns_to_be_unique'; kw = { column_list: r.columns, mostly: m }; }
        }
        else if (c === 'regex') { et = 'expect_column_values_to_match_regex'; kw = { column: r.column, regex: r.pattern, mostly: m }; }
        else if (c === 'in_set') { et = 'expect_column_values_to_be_in_set'; kw = { column: r.column, value_set: r.values, mostly: m }; }
        else if (c === 'range') { et = 'expect_column_values_to_be_between'; kw = { column: r.column, min_value: get(r, 'min', null), max_value: get(r, 'max', null), mostly: m }; }
        else if (c === 'required_columns') { r.columns.forEach(function (col) { out.push({ expectation_type: 'expect_column_to_exist', kwargs: { column: col }, meta: meta }); }); return; }
        else if (c === 'type' && (r.kind === 'integer' || r.kind === 'year')) { et = 'expect_column_values_to_match_regex'; kw = { column: r.column, regex: '^[-+]?\\d+$', mostly: m }; }
        else if (c === 'type' && r.kind === 'number') { et = 'expect_column_values_to_match_regex'; kw = { column: r.column, regex: '^[-+]?\\d*\\.?\\d+$', mostly: m }; }
        else if (c === 'sum_max') { et = 'expect_column_sum_to_be_between'; kw = { column: r.column, max_value: r.max + get(r, 'tolerance', 0) }; }
        else if (c === 'compare' && r.right !== '') {
          et = 'expect_column_pair_values_A_to_be_greater_than_B';
          if (r.op === '>' || r.op === '>=') kw = { column_A: r.left, column_B: r.right, or_equal: r.op === '>=', mostly: m };
          else if (r.op === '<' || r.op === '<=') kw = { column_A: r.right, column_B: r.left, or_equal: r.op === '<=', mostly: m };
        }
        if (kw === null) { unsupported.push({ rule_id: r.id, check: c, note: 'no built-in GX expectation; run with dqkit or add a custom expectation' }); return; }
        out.push({ expectation_type: et, kwargs: kw, meta: meta });
      });
      return { expectation_suite_name: spec.asset.id + '.dqap', expectations: out,
        meta: { generated_by: 'ndl-dq-assurance dqkit', asset: spec.asset, not_exported: unsupported } };
    };
    E.rValidateRules = function (spec) {
      var rules = [], notes = [];
      spec.rules.forEach(function (r) {
        var c = r.check, expr = null;
        if (c === 'not_null') expr = '!is.na(' + rName(r.column) + ')';
        else if (c === 'unique') expr = 'is_unique(' + r.columns.map(rName).join(', ') + ')';
        else if (c === 'regex') expr = 'grepl(' + pyJson('^(' + r.pattern + ')$') + ', ' + rName(r.column) + ')';
        else if (c === 'in_set') expr = rName(r.column) + ' %in% c(' + r.values.map(function (v) { return pyJson(pyStr(v)); }).join(', ') + ')';
        else if (c === 'range') expr = 'in_range(' + rName(r.column) + ', min = ' + (has(r, 'min') ? num(r.min) : '-Inf') + ', max = ' + (has(r, 'max') ? num(r.max) : 'Inf') + ')';
        else if (c === 'type' && (r.kind === 'integer' || r.kind === 'number' || r.kind === 'year')) expr = 'is.numeric(' + rName(r.column) + ')';
        else if (c === 'compare') {
          var rs = pyStr(r.right), numeric = /^\d+$/.test(rs.replace('.', ''));
          expr = rName(r.left) + ' ' + r.op + ' ' + (numeric ? pyStr(r.right) : rName(r.right));
        }
        else if (c === 'sum_max') expr = 'sum(' + rName(r.column) + ', na.rm = TRUE) <= ' + num(r.max + get(r, 'tolerance', 0));
        else if (c === 'required_columns') expr = 'all(c(' + r.columns.map(pyJson).join(', ') + ') %in% names(.))';
        if (expr === null) { notes.push(pyStr(r.id) + ' (' + c + '): run with dqkit; no direct validate equivalent'); return; }
        rules.push({ expr: expr, name: r.id, label: String(get(r, 'description', c)).slice(0, 80),
          description: 'dimension: ' + (has(r, 'dimension') ? r.dimension : issueOf(r).dimension) });
      });
      return [rules, notes];
    };
    E.toRValidate = function (spec, dump) {
      var x = E.rValidateRules(spec), header = '# R validate rules for ' + spec.asset.id + ' (generated by dqkit)\n# Use: library(validate); v <- validator(.file = \'this.yaml\'); confront(dat, v)\n';
      x[1].forEach(function (n) { header += '# not exported: ' + n + '\n'; });
      return header + (dump ? dump({ rules: x[0] }) : JSON.stringify({ rules: x[0] }, null, 2));
    };
    DQ.exporters = E;
  })();

  // ---------- Data contracts (contracts.py): Frictionless Table Schema, ODCS v3 and W3C CSVW ----------
  (function () {
    var C = {};
    var TYPE_TO_TS = { integer: 'integer', number: 'number', year: 'year', date: 'date' };
    var TYPE_TO_LOGICAL = { integer: 'integer', number: 'number', year: 'integer', date: 'date' };
    var TYPE_TO_XSD = { integer: 'integer', number: 'decimal', year: 'gYear', date: 'date' };
    var DIM_TO_ODCS = { completeness: 'completeness', uniqueness: 'uniqueness', validity: 'conformity', consistency: 'consistency', timeliness: 'timeliness', accuracy: 'accuracy' };
    var ODCS_TO_DIM = { completeness: 'completeness', cp: 'completeness', uniqueness: 'uniqueness', uq: 'uniqueness', conformity: 'validity', cf: 'validity',
      consistency: 'consistency', cs: 'consistency', timeliness: 'timeliness', tm: 'timeliness', accuracy: 'accuracy', ac: 'accuracy', coverage: 'completeness', cv: 'completeness' };
    function nn(v) { return v !== undefined && v !== null; }
    function issueOf(r) { return vocab()[has(r, 'issue_type') ? r.issue_type : DQ.DEFAULT_ISSUE[r.check]]; }
    function allowedPercent(r, asset) {
      var imp = pyInt(get(asset, 'importance', 3)), impact = pyInt(has(r, 'impact') ? r.impact : issueOf(r).default_impact);
      var target = nn(r.target) ? r.target : DQ.defaultTarget(DQ.combinedScore(imp, impact), get(asset, 'target_policy', DQ.DEFAULT_POLICY));
      return pyRound(100.0 - Number(target), 4);
    }
    function dimension(r) { return r.dimension || issueOf(r).dimension; }
    function columns(spec) {
      var out = [];
      (spec.rules || []).forEach(function (r) {
        [r.column, r.left, r.group].concat(r.columns || []).forEach(function (c) { if (typeof c === 'string' && out.indexOf(c) < 0) out.push(c); });
      });
      return out;
    }
    function omit(o, keys) { var x = {}; Object.keys(o).forEach(function (k) { if (keys.indexOf(k) < 0) x[k] = o[k]; }); return x; }
    function cons(f) { return f.constraints || (f.constraints = {}); }

    C.toTableSchema = function (spec) {
      var fields = {}, order = columns(spec), extra = [], pk = null;
      order.forEach(function (c) { fields[c] = { name: c }; });
      (spec.rules || []).forEach(function (r) {
        var c = r.check, f = has(fields, r.column) ? fields[r.column] : null;
        if (c === 'type' && f) f.type = TYPE_TO_TS[r.kind];
        else if (c === 'not_null' && f) cons(f).required = true;
        else if (c === 'unique') { if (r.columns.length === 1) cons(fields[r.columns[0]]).unique = true; else pk = r.columns.slice(); }
        else if (c === 'regex' && f) cons(f).pattern = r.pattern;
        else if (c === 'in_set' && f) cons(f).enum = r.values.slice();
        else if (c === 'range' && f) { if (nn(r.min)) cons(f).minimum = r.min; if (nn(r.max)) cons(f).maximum = r.max; }
        else extra.push(r);
        if (f && r.description && !has(f, 'description')) f.description = r.description;
      });
      var out = { fields: order.map(function (c) { return fields[c]; }), missingValues: [''] };
      if (pk) out.primaryKey = pk;
      if (extra.length) out['x-dqkit'] = { asset: spec.asset || {}, rules: extra };
      return out;
    };

    C.fromTableSchema = function (ts, asset) {
      var rules = [], n = 0;
      function add(r) { n++; rules.push(Object.assign({ id: 'R' + n }, r)); }
      (ts.fields || []).forEach(function (f) {
        var name = f.name, k = f.constraints || {};
        if (has(TYPE_TO_TS, f.type)) add({ check: 'type', column: name, kind: f.type });
        if (k.required) add({ check: 'not_null', column: name });
        if (k.unique) add({ check: 'unique', columns: [name] });
        if (has(k, 'pattern')) add({ check: 'regex', column: name, pattern: k.pattern });
        if (has(k, 'enum')) add({ check: 'in_set', column: name, values: k.enum.slice() });
        if (has(k, 'minimum') || has(k, 'maximum')) { var r = { check: 'range', column: name }; if (has(k, 'minimum')) r.min = k.minimum; if (has(k, 'maximum')) r.max = k.maximum; add(r); }
      });
      if (ts.primaryKey) add({ check: 'unique', columns: typeof ts.primaryKey === 'string' ? [ts.primaryKey] : ts.primaryKey.slice() });
      var extra = ts['x-dqkit'] || {};
      (extra.rules || []).forEach(function (r) { add(omit(r, ['id'])); });
      return { asset: asset || extra.asset || { id: 'imported', importance: 3 }, rules: rules };
    };

    function odcsRule(r, asset) {
      var c = r.check, pct = allowedPercent(r, asset), q = { id: pyStr(r.id), description: has(r, 'description') ? r.description : c };
      var dim = DIM_TO_ODCS[dimension(r)];
      if (dim) q.dimension = dim;
      function lib(metric, extra) { q.type = 'library'; q.metric = metric; if (extra) q.arguments = extra; q.mustBeLessOrEqualTo = pct; q.unit = 'percent'; }
      if (c === 'not_null') lib('nullValues');
      else if (c === 'unique') lib('duplicateValues', r.columns.length > 1 ? { properties: r.columns.slice() } : null);
      else if (c === 'in_set') lib('invalidValues', { validValues: r.values.slice() });
      else if (c === 'regex') lib('invalidValues', { pattern: r.pattern });
      else if (c === 'not_unknown') lib('missingValues', r.values && r.values.length ? { missingValues: r.values.slice() } : null);
      else { q.type = 'custom'; q.engine = 'dqkit'; q.implementation = omit(r, ['id', 'description']); q.mustBeLessOrEqualTo = pct; q.unit = 'percent'; }
      return q;
    }

    C.toOdcs = function (spec, version, status) {
      var asset = spec.asset || {}, order = columns(spec), props = {}, schemaQuality = [];
      order.forEach(function (c) { props[c] = { name: c }; });
      (spec.rules || []).forEach(function (r) {
        var c = r.check, col = r.column, inProps = typeof col === 'string' && has(props, col);
        if (c === 'type' && inProps) {
          props[col].logicalType = TYPE_TO_LOGICAL[r.kind];
          props[col].customProperties = [{ property: 'dqkitTypeRuleId', value: pyStr(r.id) }];
          if (r.kind === 'year') props[col].logicalTypeOptions = { format: 'yyyy' };
          return;
        }
        if (c === 'range' && inProps) { var o = props[col].logicalTypeOptions || (props[col].logicalTypeOptions = {}); if (nn(r.min)) o.minimum = r.min; if (nn(r.max)) o.maximum = r.max; }
        if (c === 'not_null' && inProps) props[col].required = true;
        if (c === 'unique' && r.columns.length === 1) props[r.columns[0]].unique = true;
        var q = odcsRule(r, asset);
        var target = (inProps && c !== 'compare' && c !== 'group_disparity') ? col : (c === 'unique' && r.columns.length === 1 ? r.columns[0] : null);
        if (target) (props[target].quality || (props[target].quality = [])).push(q); else schemaQuality.push(q);
      });
      var id = get(asset, 'id', 'dataset'), obj = { name: id, physicalName: id, properties: order.map(function (c) { return props[c]; }) };
      if (schemaQuality.length) obj.quality = schemaQuality;
      var out = { apiVersion: 'v3.1.0', kind: 'DataContract', id: id, version: version || '1.0.0', status: status || 'draft',
        name: get(asset, 'title', id), schema: [obj],
        customProperties: [{ property: 'dqkitImportance', value: pyInt(get(asset, 'importance', 3)) },
                           { property: 'dqkitTargetPolicy', value: get(asset, 'target_policy', DQ.DEFAULT_POLICY) }] };
      if (asset.owner) out.team = { name: asset.owner };
      return out;
    };

    C.fromOdcs = function (contract) {
      var cp = {}; (contract.customProperties || []).forEach(function (p) { cp[p.property] = p.value; });
      var asset = { id: get(contract, 'id', 'imported'), title: get(contract, 'name', get(contract, 'id', 'imported')), importance: pyInt(nn(cp.dqkitImportance) ? cp.dqkitImportance : 3) };
      if (cp.dqkitTargetPolicy) asset.target_policy = cp.dqkitTargetPolicy;
      if ((contract.team || {}).name) asset.owner = contract.team.name;
      var rules = [], n = 0;
      function add(r, q) {
        n++;
        r = Object.assign({ id: q && q.id ? pyStr(q.id) : 'R' + n }, r);
        if (q) {
          if (q.description && q.description !== r.check) r.description = q.description;
          if (has(ODCS_TO_DIM, q.dimension) && ODCS_TO_DIM[q.dimension] !== dimension(r)) r.dimension = ODCS_TO_DIM[q.dimension];
          var limit = nn(q.mustBeLessOrEqualTo) ? q.mustBeLessOrEqualTo : nn(q.mustBeLessThan) ? q.mustBeLessThan : q.mustBe;
          if (nn(limit) && q.unit === 'percent') r.target = pyRound(100.0 - Number(limit), 4);
        }
        rules.push(r);
      }
      function quality(q, col) {
        var m = q.metric, a = q.arguments || {};
        if (q.type === 'custom' && q.engine === 'dqkit') add(Object.assign({}, q.implementation), q);
        else if (m === 'nullValues' && col) add({ check: 'not_null', column: col }, q);
        else if (m === 'duplicateValues') add({ check: 'unique', columns: (a.properties || [col]).slice() }, q);
        else if (m === 'invalidValues' && has(a, 'validValues') && col) add({ check: 'in_set', column: col, values: a.validValues.slice() }, q);
        else if (m === 'invalidValues' && has(a, 'pattern') && col) add({ check: 'regex', column: col, pattern: a.pattern }, q);
        else if (m === 'missingValues' && col) { var r = { check: 'not_unknown', column: col }; if (a.missingValues && a.missingValues.length) r.values = a.missingValues.slice(); add(r, q); }
      }
      (contract.schema || []).forEach(function (obj) {
        (obj.properties || []).forEach(function (p) {
          var name = p.name, lt = p.logicalType, o = p.logicalTypeOptions || {}, pcp = {};
          (p.customProperties || []).forEach(function (x) { pcp[x.property] = x.value; });
          if (lt === 'integer' || lt === 'number' || lt === 'date') add({ check: 'type', column: name, kind: o.format === 'yyyy' ? 'year' : lt }, pcp.dqkitTypeRuleId ? { id: pcp.dqkitTypeRuleId } : null);
          var qs = p.quality || [], metrics = qs.map(function (q) { return q.metric; });
          if (p.required && metrics.indexOf('nullValues') < 0) add({ check: 'not_null', column: name });
          if (p.unique && metrics.indexOf('duplicateValues') < 0) add({ check: 'unique', columns: [name] });
          var hasRange = qs.some(function (q) { return (q.implementation || {}).check === 'range'; });
          if ((has(o, 'minimum') || has(o, 'maximum')) && !hasRange) { var r = { check: 'range', column: name }; if (has(o, 'minimum')) r.min = o.minimum; if (has(o, 'maximum')) r.max = o.maximum; add(r); }
          qs.forEach(function (q) { quality(q, name); });
        });
        (obj.quality || []).forEach(function (q) { quality(q, null); });
      });
      var seen = new Set();
      rules.forEach(function (r) { while (seen.has(r.id)) r.id += 'b'; seen.add(r.id); });
      return { asset: asset, rules: rules };
    };

    C.unsupported = function (contract) {
      var out = [];
      (contract.schema || []).forEach(function (obj) {
        var items = [];
        (obj.properties || []).forEach(function (p) { (p.quality || []).forEach(function (q) { items.push([p.name, q]); }); });
        (obj.quality || []).forEach(function (q) { items.push([null, q]); });
        items.forEach(function (it) { var q = it[1];
          if (q.type === 'text' || q.type === 'sql' || (q.type === 'custom' && q.engine !== 'dqkit')) out.push({ column: it[0], id: q.id, type: q.type, description: q.description || '' }); });
      });
      return out;
    };

    function safe(n) { return n.replace(/[^A-Za-z0-9_]/g, '_'); }
    C.toCsvw = function (spec, url) {
      var ts = C.toTableSchema(spec), cols = ts.fields.map(function (f) {
        var k = f.constraints || {}, col = { name: safe(f.name), titles: f.name }, dt = { base: TYPE_TO_XSD[f.type] || 'string' };
        if (has(k, 'pattern')) dt.format = k.pattern;
        if (has(k, 'minimum')) dt.minimum = k.minimum;
        if (has(k, 'maximum')) dt.maximum = k.maximum;
        col.datatype = Object.keys(dt).length > 1 ? dt : dt.base;
        if (k.required) col.required = true;
        if (f.description) col['dc:description'] = f.description;
        return col;
      });
      var schema = { columns: cols };
      if (ts.primaryKey) schema.primaryKey = ts.primaryKey.map(safe);
      return { '@context': 'http://www.w3.org/ns/csvw', url: url || 'data.csv', 'dc:title': get(spec.asset || {}, 'title', ''), tableSchema: schema };
    };
    DQ.contracts = C;
  })();

  // ---------- ODCS checks and change control (contracts.py validate_odcs, diff_odcs) ----------
  (function () {
    var C = DQ.contracts;
    var STATUSES = ['proposed', 'draft', 'active', 'deprecated', 'retired'];
    var METRICS = ['nullValues', 'missingValues', 'invalidValues', 'duplicateValues', 'rowCount'];
    var SEMVER = /^\d+\.\d+\.\d+([-+][0-9A-Za-z.-]+)?$/;
    function truthy(v) {
      if (v === undefined || v === null || v === false || v === 0 || v === '') return false;
      if (Array.isArray(v)) return v.length > 0;
      if (typeof v === 'object') return Object.keys(v).length > 0;
      return true;
    }
    function blank(v) { return v === undefined || v === null || v === ''; }
    function str(v) { return v === undefined || v === null ? 'None' : String(v); }
    function n(v) { return String(Number(v)); }
    C.validateOdcs = function (contract) {
      var out = [];
      function err(w, m) { out.push({ level: 'error', where: w, message: m }); }
      function warn(w, m) { out.push({ level: 'warning', where: w, message: m }); }
      if (!contract || typeof contract !== 'object' || Array.isArray(contract)) return [{ level: 'error', where: 'contract', message: 'The contract must be an object.' }];
      ['apiVersion', 'kind', 'id', 'version', 'status'].forEach(function (k) { if (blank(contract[k])) err(k, 'Required field ' + k + ' is missing.'); });
      if (!blank(contract.kind) && contract.kind !== 'DataContract') err('kind', 'kind must be DataContract.');
      if (truthy(contract.apiVersion) && String(contract.apiVersion).indexOf('v3') !== 0) warn('apiVersion', 'apiVersion ' + contract.apiVersion + " isn't v3; the toolkit reads v3 contracts.");
      if (truthy(contract.status) && STATUSES.indexOf(contract.status) < 0) warn('status', 'status ' + contract.status + " isn't one of " + STATUSES.join(', ') + '.');
      if (truthy(contract.version) && !SEMVER.test(String(contract.version))) warn('version', 'version should be semantic, like 1.2.0, so changes can be classed as breaking or not.');
      if (!truthy(contract.schema)) warn('schema', "No schema: consumers can't see the columns or the quality rules.");
      (contract.schema || []).forEach(function (obj, i) {
        var w = 'schema[' + i + ']';
        if (!truthy(obj.name)) err(w, 'Every schema object needs a name.');
        var names = (obj.properties || []).map(function (p) { return p.name; });
        names.forEach(function (nm, j) { if (!truthy(nm)) err(w + '.properties[' + j + ']', 'Every property needs a name.'); });
        var dup = [];
        names.forEach(function (nm) { if (truthy(nm) && dup.indexOf(nm) < 0 && names.filter(function (x) { return x === nm; }).length > 1) dup.push(nm); });
        dup.sort(cmp);
        if (dup.length) err(w, 'Property names repeat: ' + dup.join(', ') + '.');
        var items = [];
        (obj.properties || []).forEach(function (p) { (p.quality || []).forEach(function (q) { items.push([p.name, q]); }); });
        (obj.quality || []).forEach(function (q) { items.push([null, q]); });
        items.forEach(function (it) {
          var col = it[0], q = it[1], where = w + '.' + (truthy(col) ? col : '(table)');
          var type = has(q, 'type') ? q.type : 'library';
          if (type === 'library' && truthy(q.metric) && METRICS.indexOf(q.metric) < 0) warn(where, 'Unknown library metric ' + q.metric + '.');
          if (type === 'library' && !Object.keys(q).some(function (k) { return k.indexOf('must') === 0; }))
            warn(where, ('Rule ' + (q.id || q.metric || '') + ' has no threshold (mustBe..., mustBeLessOrEqualTo...).').split('  ').join(' '));
        });
      });
      if (!truthy(contract.team)) warn('team', 'No team: say which team (a role or group, never a named person) owns the contract.');
      if (!truthy(contract.slaProperties)) warn('slaProperties', 'No service levels: add at least update frequency and availability.');
      return out;
    };
    function cmp(a, b) { return a < b ? -1 : a > b ? 1 : 0; }
    function props(c) {
      var m = {}, keys = [];
      (c.schema || []).forEach(function (o) { (o.properties || []).forEach(function (p) {
        var k = JSON.stringify([str(o.name), str(p.name)]); if (!(k in m)) keys.push(k); m[k] = p; }); });
      return { m: m, keys: keys };
    }
    function limits(p) {
      var out = {};
      (p.quality || []).forEach(function (q) { if (q.unit === 'percent') {
        var v = has(q, 'mustBeLessOrEqualTo') ? q.mustBeLessOrEqualTo : q.mustBeLessThan;
        out[str(truthy(q.id) ? q.id : q.metric)] = v === undefined ? null : v; } });
      return out;
    }
    function sortKeys(ks) { return ks.slice().sort(function (a, b) { var x = JSON.parse(a), y = JSON.parse(b); return cmp(x[0], y[0]) || cmp(x[1], y[1]); }); }
    function where(k) { var x = JSON.parse(k); return x[0] + '.' + x[1]; }
    function parts(v) { return String(v).split('-')[0].split('+')[0].split('.').map(Number); }
    function listGt(a, b) { for (var i = 0; i < Math.max(a.length, b.length); i++) { if (a[i] !== b[i]) return (a[i] || 0) > (b[i] || 0); } return false; }
    C.diffOdcs = function (oldC, newC) {
      var A = props(oldC), B = props(newC), changes = [];
      function add(kind, w, msg, br) { changes.push({ kind: kind, where: w, message: msg, breaking: br }); }
      sortKeys(A.keys.filter(function (k) { return !(k in B.m); })).forEach(function (k) { add('removed', where(k), 'Column removed.', true); });
      sortKeys(B.keys.filter(function (k) { return !(k in A.m); })).forEach(function (k) {
        add('added', where(k), 'Column added.' + (truthy(B.m[k].required) ? ' It is required, so producers must supply it.' : ''), false); });
      sortKeys(A.keys.filter(function (k) { return k in B.m; })).forEach(function (k) {
        var p = A.m[k], q = B.m[k], w = where(k);
        if ((p.logicalType === undefined ? null : p.logicalType) !== (q.logicalType === undefined ? null : q.logicalType))
          add('type', w, 'Type changed from ' + (truthy(p.logicalType) ? p.logicalType : 'none') + ' to ' + (truthy(q.logicalType) ? q.logicalType : 'none') + '.', true);
        [['required', 'required'], ['unique', 'unique']].forEach(function (f) {
          if (truthy(p[f[0]]) && !truthy(q[f[0]])) add(f[0], w, 'No longer promised to be ' + f[1] + '.', true);
          if (truthy(q[f[0]]) && !truthy(p[f[0]])) add(f[0], w, 'Now promised to be ' + f[1] + '.', false);
        });
        var la = limits(p), lb = limits(q), ids = Object.keys(la);
        Object.keys(lb).forEach(function (x) { if (ids.indexOf(x) < 0) ids.push(x); });
        ids.sort(cmp).forEach(function (rid) {
          var x = has(la, rid) ? la[rid] : null, y = has(lb, rid) ? lb[rid] : null;
          if (x !== null && y === null) add('quality', w, 'Quality rule ' + rid + ' removed.', true);
          else if (x === null && y !== null) add('quality', w, 'Quality rule ' + rid + ' added (at most ' + n(y) + '% failing).', false);
          else if (x !== y) add('quality', w, 'Rule ' + rid + ': at most ' + n(x) + '% failing became ' + n(y) + '%.', Number(y) > Number(x));
        });
      });
      var os = oldC.status === undefined ? null : oldC.status, ns = newC.status === undefined ? null : newC.status;
      if (os !== ns) add('status', 'status', 'Status changed from ' + str(os) + ' to ' + str(ns) + '.', ns === 'deprecated' || ns === 'retired');
      var breaking = changes.some(function (c) { return c.breaking; });
      var ov = String(truthy(oldC.version) ? oldC.version : ''), nxt = null;
      if (SEMVER.test(ov)) {
        var o = parts(ov);
        nxt = breaking ? (o[0] + 1) + '.0.0' : (changes.length ? o[0] + '.' + (o[1] + 1) + '.0' : o[0] + '.' + o[1] + '.' + o[2]);
      }
      var stated = String(truthy(newC.version) ? newC.version : ''), ok = null;
      if (nxt && SEMVER.test(stated)) {
        var a = parts(ov), b = parts(stated);
        ok = breaking ? b[0] > a[0] : (changes.length ? listGt(b, a) : !listGt(a, b));
      }
      return { changes: changes, breaking: breaking, suggested_version: nxt, stated_version: stated, version_ok: ok };
    };
  })();

  // ---------- Metadata Weaver (weaver.py): one record in, DCAT, schema.org, CKAN and ODCS out, with gaps ----------
  (function () {
    var W = {};
    var DQC = 'https://cyberdudeuk.github.io/ndl-dq-assurance/vocab#';
    var CTX = { dcat: 'http://www.w3.org/ns/dcat#', dct: 'http://purl.org/dc/terms/', foaf: 'http://xmlns.com/foaf/0.1/',
      vcard: 'http://www.w3.org/2006/vcard/ns#', dqc: DQC };
    var FIELDS = [
      ['title', 'Title', 'Title', 'title', 'dcat schema ckan odcs'],
      ['description', 'Description', 'Description', 'description', 'dcat schema ckan odcs'],
      ['identifier', 'Identifier', 'Identifier', 'identifier', 'dcat schema ckan odcs'],
      ['publisher', 'Publisher or creator', 'Publisher', 'creator', 'dcat schema ckan odcs'],
      ['contact', 'Contact point (a team or role)', 'Contact point', '', 'dcat schema ckan odcs'],
      ['keywords', 'Keywords', 'Keyword', '', 'dcat schema ckan odcs'],
      ['theme', 'Theme or domain', 'Theme', '', 'dcat ckan odcs'],
      ['licence', 'Licence', 'Licence', 'licence', 'dcat schema ckan odcs'],
      ['access_rights', 'Access rights', 'Access rights', 'accessRights', 'dcat schema ckan odcs'],
      ['security', 'Security classification', 'Security classification', 'securityClassification', 'dcat ckan odcs'],
      ['issued', 'Date created or issued', 'Issued', 'dateCreated', 'dcat schema ckan odcs'],
      ['modified', 'Date modified', 'Modified', '', 'dcat schema ckan'],
      ['expires', 'Expiry date', 'Expires', 'expires', 'dcat schema ckan odcs'],
      ['superseded_by', 'Superseded by', 'Superseded by', 'supersededBy', 'dcat ckan odcs'],
      ['accrual', 'Update frequency', 'Accrual periodicity', '', 'dcat ckan odcs'],
      ['spatial', 'Geographic coverage', 'Spatial coverage', '', 'dcat schema ckan'],
      ['temporal', 'Time period covered', 'Temporal coverage', 'temporalCoverage', 'dcat schema ckan odcs'],
      ['conforms_to', 'Conforms to (schema or standard)', 'Conforms to', 'conformsTo', 'dcat schema ckan odcs'],
      ['landing_page', 'Landing page', 'Landing page', '', 'dcat schema ckan'],
      ['version', 'Version', 'Version', '', 'dcat schema ckan odcs'],
      ['language', 'Language', 'Language', '', 'dcat schema ckan'],
      ['distributions', 'Distributions (files and APIs)', 'Distribution', 'mediaType', 'dcat schema ckan odcs'],
    ];
    var KEYS = FIELDS.map(function (f) { return f[0]; });
    var CDA = FIELDS.filter(function (f) { return f[3]; }).map(function (f) { return [f[0], f[3]]; });
    var TARGETS = ['dcat', 'schema', 'ckan', 'odcs'];
    var CARRY = {};
    TARGETS.forEach(function (t) { CARRY[t] = FIELDS.filter(function (f) { return f[4].split(' ').indexOf(t) >= 0; }).map(function (f) { return f[0]; }); });
    W.FIELDS = FIELDS; W.TARGETS = TARGETS; W.CARRY = CARRY; W.KEYS = KEYS;

    function isObj(v) { return v !== null && typeof v === 'object' && !Array.isArray(v); }
    function first(v) { return Array.isArray(v) ? (v.length ? first(v[0]) : null) : v; }
    function text(v) {
      v = first(v);
      if (v === undefined || v === null) return '';
      if (isObj(v)) {
        var ks = ['@value', 'name', 'foaf:name', 'vcard:fn', 'fn', 'title', '@id', 'url', 'label'];
        for (var i = 0; i < ks.length; i++) if (truthy(v[ks[i]])) return text(v[ks[i]]);
        return '';
      }
      if (typeof v === 'boolean') return '';
      return String(v).trim();
    }
    function truthy(v) {
      if (v === undefined || v === null || v === false || v === 0 || v === '') return false;
      if (Array.isArray(v)) return v.length > 0;
      if (isObj(v)) return Object.keys(v).length > 0;
      return true;
    }
    function list(v) {
      if (v === undefined || v === null || v === '') return [];
      if (!Array.isArray(v)) v = [v];
      var out = [];
      v.forEach(function (x) { var t = text(x); if (t && out.indexOf(t) < 0) out.push(t); });
      return out;
    }
    function strip(d, prefixes) {
      var out = {};
      Object.keys(d || {}).forEach(function (k) {
        var kk = k;
        prefixes.forEach(function (p) { if (kk.indexOf(p) === 0) kk = kk.slice(p.length); });
        if (!has(out, kk)) out[kk] = d[k];
      });
      return out;
    }
    function temporal(s, e) { s = text(s); e = text(e); if (s && e) return s + '/' + e; return s || (e ? '../' + e : ''); }
    function dist(title, url, fmt, mt) {
      return { title: title || '', url: url || '', format: fmt && fmt.indexOf('/') < 0 ? fmt.toUpperCase() : (fmt || ''), media_type: mt || '' };
    }
    function empty() { var c = {}; KEYS.forEach(function (k) { c[k] = (k === 'keywords' || k === 'theme' || k === 'distributions') ? [] : ''; }); return c; }
    function arr(v) { return Array.isArray(v) ? v : [v]; }

    W.detect = function (rec) {
      if (!isObj(rec)) throw new Error('A metadata record must be a JSON object.');
      if (rec.kind === 'DataContract' || has(rec, 'apiVersion')) return 'odcs';
      var t = has(rec, '@type') && truthy(rec['@type']) ? rec['@type'] : rec.type;
      var ts = Array.isArray(t) ? t.join(' ') : String(truthy(t) ? t : '');
      var ctx = JSON.stringify(has(rec, '@context') ? rec['@context'] : '');
      if (has(rec, 'tableSchema')) return 'csvw';  // CSVW first: its notes may borrow DCAT terms
      if (ts.indexOf('dcat:Dataset') >= 0 || ctx.indexOf('dcat') >= 0 || Object.keys(rec).some(function (k) { return k.indexOf('dcat:') === 0 || k.indexOf('dct:') === 0; })) return 'dcat';
      if ((/Dataset$/.test(ts) && ctx.indexOf('schema.org') >= 0) || ts === 'Dataset') return 'schema';
      if (has(rec, 'tableSchema') || (ctx.indexOf('csvw') >= 0 && has(rec, 'url'))) return 'csvw';
      var res = rec.resources, prof = rec.profile, sch = rec['$schema'];
      if (Array.isArray(res) && ((typeof prof === 'string' && prof.indexOf('package') >= 0) || (typeof sch === 'string' && sch.indexOf('frictionless') >= 0)
          || res.some(function (x) { return isObj(x) && has(x, 'path'); }))) return 'frictionless';
      var r = isObj(rec.result) ? rec.result : rec;  // CKAN API responses wrap the package in "result"
      if (['resources', 'notes', 'license_id', 'organization', 'extras', 'maintainer'].some(function (k) { return has(r, k); })) return 'ckan';
      throw new Error("Couldn't tell the format. Use DCAT or schema.org JSON-LD, a CKAN package, an ODCS contract, CSVW metadata or a Frictionless Data Package.");
    };

    var R = {};
    R.dcat = function (rec) {
      var r = strip(rec, ['dct:', 'dcat:', 'dcterms:']), c = empty();
      c.title = text(r.title); c.description = text(r.description);
      c.identifier = text(r.identifier) || text(rec['@id']);
      c.publisher = text(r.publisher) || text(r.creator);
      c.contact = text(r.contactPoint); c.keywords = list(r.keyword); c.theme = list(r.theme);
      c.licence = text(r.license); c.access_rights = text(r.accessRights); c.security = text(rec['dqc:securityClassification']);
      c.issued = text(r.issued) || text(r.created); c.modified = text(r.modified); c.expires = text(rec['dqc:expires']);
      c.superseded_by = text(r.isReplacedBy); c.accrual = text(r.accrualPeriodicity); c.spatial = text(r.spatial);
      var t = first(r.temporal);
      if (isObj(t)) { t = strip(t, ['dcat:', 'dct:', 'schema:']); c.temporal = temporal(t.startDate, t.endDate); } else c.temporal = text(t);
      c.conforms_to = text(r.conformsTo); c.landing_page = text(r.landingPage);
      c.version = text(r.version) || text(rec['owl:versionInfo']); c.language = text(r.language);
      var ds = truthy(r.distribution) ? r.distribution : [];
      arr(ds).forEach(function (d) { d = strip(d, ['dct:', 'dcat:']);
        c.distributions.push(dist(text(d.title), text(d.downloadURL) || text(d.accessURL), text(d.format), text(d.mediaType))); });
      return c;
    };
    R.schema = function (rec) {
      var r = strip(rec, ['schema:']), c = empty();
      c.title = text(r.name); c.description = text(r.description);
      c.identifier = text(r.identifier) || text(rec['@id']);
      c.publisher = text(r.publisher) || text(r.creator);
      var cr = first(r.creator);
      c.contact = text(isObj(cr) ? cr.contactPoint : null);
      var kw = r.keywords;
      c.keywords = typeof kw === 'string' ? kw.split(',').map(function (k) { return k.trim(); }).filter(Boolean) : list(kw);
      c.licence = text(r.license);
      c.access_rights = text(r.conditionsOfAccess) || (r.isAccessibleForFree === true ? 'Open' : '');
      c.issued = text(r.dateCreated) || text(r.datePublished); c.modified = text(r.dateModified); c.expires = text(r.expires);
      c.spatial = text(r.spatialCoverage); c.temporal = text(r.temporalCoverage); c.conforms_to = text(r.schemaVersion);
      c.landing_page = text(r.url); c.version = text(r.version); c.language = text(r.inLanguage);
      var ds = truthy(r.distribution) ? r.distribution : [];
      arr(ds).forEach(function (d) { d = strip(d, ['schema:']);
        c.distributions.push(dist(text(d.name), text(d.contentUrl) || text(d.url), '', text(d.encodingFormat))); });
      return c;
    };
    R.ckan = function (rec) {
      var r = isObj(rec.result) ? rec.result : rec, ex = {}, c = empty();
      (r.extras || []).forEach(function (e) { if (isObj(e)) ex[e.key] = e.value; });
      c.title = text(r.title); c.description = text(r.notes);
      c.identifier = text(ex.identifier) || text(r.id) || text(r.name);
      c.publisher = text((r.organization || {}).title) || text(r.author);
      c.contact = text(r.maintainer) || text(ex['contact-name']);
      c.keywords = list((r.tags || []).filter(isObj).map(function (t) { return t.display_name || t.name; }));
      c.theme = list((r.groups || []).filter(isObj).map(function (g) { return g.title || g.name; }));
      if (!c.theme.length) c.theme = list(ex.theme);
      c.licence = text(r.license_url) || text(r.license_id) || text(r.license_title);
      c.access_rights = text(ex.access_rights) || (r.isopen === true ? 'Open' : '');
      c.security = text(ex.security_classification);
      c.issued = text(ex.issued) || text(r.metadata_created); c.modified = text(ex.modified) || text(r.metadata_modified);
      c.expires = text(ex.expires); c.superseded_by = text(ex.superseded_by);
      c.accrual = text(ex.frequency) || text(ex.update_frequency);
      c.spatial = text(ex.spatial_text) || text(ex.spatial);
      c.temporal = temporal(ex.temporal_start, ex.temporal_end) || text(ex.temporal_coverage);
      c.conforms_to = text(ex.conforms_to) || text(ex.schema);
      c.landing_page = text(r.url); c.version = text(r.version); c.language = text(ex.language);
      (r.resources || []).forEach(function (d) { c.distributions.push(dist(text(d.name), text(d.url), text(d.format), text(d.mimetype))); });
      return c;
    };
    R.odcs = function (rec) {
      var cp = {}, c = empty(), desc = truthy(rec.description) ? rec.description : {};
      (rec.customProperties || []).forEach(function (p) { if (isObj(p)) cp[p.property] = p.value; });
      c.title = text(rec.name);
      c.description = isObj(desc) ? text(desc.purpose) : text(desc);
      c.identifier = text(rec.id);
      c.publisher = text(cp.publisher) || text(rec.tenant);
      c.contact = isObj(rec.team) ? text(rec.team.name) : '';
      c.keywords = list(rec.tags); c.theme = list(rec.domain);
      c.licence = text(cp.licence) || text(cp.license);
      c.access_rights = isObj(desc) ? text(desc.limitations) : '';
      c.security = text(cp.securityClassification); c.issued = text(rec.contractCreatedTs);
      c.expires = text(cp.expires); c.superseded_by = text(cp.supersededBy);
      var sla = rec.slaProperties || [];
      for (var i = 0; i < sla.length; i++) {
        var s = sla[i];
        if (isObj(s) && ['frequency', 'latency', 'freshness'].indexOf(s.property) >= 0) {
          c.accrual = [text(s.value), text(s.unit)].filter(Boolean).join(' '); break;
        }
      }
      c.temporal = text(cp.temporalCoverage);
      c.conforms_to = truthy(rec.schema) ? 'ODCS ' + (text(rec.apiVersion) || 'v3') : '';
      c.version = text(rec.version);
      (rec.servers || []).forEach(function (s) { if (isObj(s))
        c.distributions.push(dist(text(s.server), text(s.location) || text(s.host), text(s.format) || text(s.type), '')); });
      return c;
    };
    // CSV on the Web (W3C) table metadata (weaver.py read_csvw).
    R.csvw = function (rec) {
      var r = strip(rec, ['dc:', 'dcterms:', 'dct:', 'schema:', 'dcat:']), c = empty();
      c.title = text(r.title) || text(r.name); c.description = text(r.description);
      c.identifier = text(r.identifier) || text(rec['@id']) || text(rec.url);
      c.publisher = text(r.publisher) || text(r.creator);
      c.keywords = list(r.keywords); if (!c.keywords.length) c.keywords = list(r.keyword); if (!c.keywords.length) c.keywords = list(r.subject);
      c.licence = text(r.license) || text(r.rights);
      c.issued = text(r.issued) || text(r.created) || text(r.datePublished); c.modified = text(r.modified) || text(r.dateModified);
      c.spatial = text(r.spatial); c.temporal = text(r.temporal);
      c.conforms_to = has(rec, 'tableSchema') ? 'http://www.w3.org/ns/csvw' : '';
      c.language = text(rec['@language']) || text(r.language);
      if (text(rec.url)) c.distributions.push(dist(c.title, text(rec.url), 'CSV', 'text/csv'));
      return c;
    };
    // A Frictionless Data Package (weaver.py read_frictionless).
    R.frictionless = function (rec) {
      var c = empty(), people = (rec.contributors || []).filter(isObj);
      function role() {
        var rs = Array.prototype.slice.call(arguments);
        for (var i = 0; i < people.length; i++) if (typeof people[i].role === 'string' && rs.indexOf(people[i].role.toLowerCase()) >= 0) return text(people[i].title);
        return '';
      }
      c.title = text(rec.title) || text(rec.name); c.description = text(rec.description);
      c.identifier = text(rec.id) || text(rec.name);
      c.publisher = role('publisher') || role('author') || (people.length ? text(people[0].title) : '');
      c.contact = role('maintainer', 'contact'); c.keywords = list(rec.keywords);
      var lic = first(rec.licenses);
      c.licence = isObj(lic) ? (text(lic.path) || text(lic.name)) : '';
      c.issued = text(rec.created); c.version = text(rec.version); c.landing_page = text(rec.homepage);
      var prof = text(rec.profile) || text(rec['$schema']);
      c.conforms_to = prof.indexOf('http') === 0 ? prof : 'Frictionless Data Package';
      (rec.resources || []).forEach(function (d) {
        if (isObj(d)) c.distributions.push(dist(text(d.title) || text(d.name), typeof d.path === 'string' ? d.path : text(d.path), text(d.format), text(d.mediatype)));
      });
      return c;
    };
    W.read = function (rec, fmt) {
      fmt = fmt || W.detect(rec);
      if (!R[fmt]) throw new Error('Unknown format ' + fmt + '. Use one of: ' + Object.keys(R).join(', ') + '.');
      return [fmt, R[fmt](rec)];
    };

    function media(d) { return d.media_type || d.format; }
    function putter(out) { return function (k, v) { if (v !== '' && v !== null && v !== undefined && !(Array.isArray(v) && !v.length)) out[k] = v; }; }
    function pick(pairs) { var o = {}; pairs.forEach(function (p) { if (p[1]) o[p[0]] = p[1]; }); return o; }
    var Wr = {};
    Wr.dcat = function (c) {
      var out = { '@context': CTX, '@type': 'dcat:Dataset' }, put = putter(out);
      put('dct:title', c.title); put('dct:description', c.description); put('dct:identifier', c.identifier);
      put('dct:publisher', c.publisher ? { '@type': 'foaf:Agent', 'foaf:name': c.publisher } : '');
      put('dcat:contactPoint', c.contact ? { '@type': 'vcard:Kind', 'vcard:fn': c.contact } : '');
      put('dcat:keyword', c.keywords); put('dcat:theme', c.theme); put('dct:license', c.licence);
      put('dct:accessRights', c.access_rights); put('dqc:securityClassification', c.security); put('dct:issued', c.issued);
      put('dct:modified', c.modified); put('dqc:expires', c.expires); put('dct:isReplacedBy', c.superseded_by);
      put('dct:accrualPeriodicity', c.accrual); put('dct:spatial', c.spatial);
      if (c.temporal) {
        var i = c.temporal.indexOf('/'), s = i < 0 ? c.temporal : c.temporal.slice(0, i), e = i < 0 ? '' : c.temporal.slice(i + 1);
        var t = { '@type': 'dct:PeriodOfTime' };
        if (s && s !== '..') t['dcat:startDate'] = s;
        if (e && e !== '..') t['dcat:endDate'] = e;
        out['dct:temporal'] = t;
      }
      put('dct:conformsTo', c.conforms_to); put('dcat:landingPage', c.landing_page); put('dcat:version', c.version); put('dct:language', c.language);
      if (c.distributions.length) out['dcat:distribution'] = c.distributions.map(function (d) {
        return pick([['@type', 'dcat:Distribution'], ['dct:title', d.title], ['dcat:downloadURL', d.url], ['dct:format', d.format], ['dcat:mediaType', d.media_type]]); });
      return out;
    };
    Wr.schema = function (c) {
      var out = { '@context': 'https://schema.org/', '@type': 'Dataset' }, put = putter(out);
      put('name', c.title); put('description', c.description); put('identifier', c.identifier);
      if (c.publisher || c.contact) {
        var org = { '@type': 'Organization' };
        if (c.publisher) org.name = c.publisher;
        if (c.contact) org.contactPoint = { '@type': 'ContactPoint', name: c.contact };
        out.creator = org;
      }
      put('keywords', c.keywords); put('license', c.licence); put('conditionsOfAccess', c.access_rights);
      put('dateCreated', c.issued); put('dateModified', c.modified); put('expires', c.expires);
      put('spatialCoverage', c.spatial); put('temporalCoverage', c.temporal); put('schemaVersion', c.conforms_to);
      put('url', c.landing_page); put('version', c.version); put('inLanguage', c.language);
      if (c.distributions.length) out.distribution = c.distributions.map(function (d) {
        return pick([['@type', 'DataDownload'], ['name', d.title], ['contentUrl', d.url], ['encodingFormat', media(d)]]); });
      return out;
    };
    Wr.ckan = function (c) {
      var extras = [['identifier', c.identifier], ['access_rights', c.access_rights], ['security_classification', c.security],
        ['issued', c.issued], ['modified', c.modified], ['expires', c.expires], ['superseded_by', c.superseded_by],
        ['frequency', c.accrual], ['spatial_text', c.spatial], ['temporal_coverage', c.temporal], ['conforms_to', c.conforms_to],
        ['language', c.language], ['theme', c.theme.join(', ')]].filter(function (p) { return p[1]; }).map(function (p) { return { key: p[0], value: p[1] }; });
      var out = {}, put = putter(out);
      put('title', c.title); put('notes', c.description); put('url', c.landing_page); put('version', c.version);
      put('maintainer', c.contact); put('organization', c.publisher ? { title: c.publisher } : null);
      put('license_id', c.licence); put('tags', c.keywords.map(function (k) { return { name: k }; })); put('extras', extras);
      put('resources', c.distributions.map(function (d) { return pick([['name', d.title], ['url', d.url], ['format', d.format], ['mimetype', d.media_type]]); }));
      return out;
    };
    Wr.odcs = function (c) {
      var cp = [['publisher', c.publisher], ['licence', c.licence], ['securityClassification', c.security], ['expires', c.expires],
        ['supersededBy', c.superseded_by], ['temporalCoverage', c.temporal]].filter(function (p) { return p[1]; }).map(function (p) { return { property: p[0], value: p[1] }; });
      var out = { apiVersion: 'v3.1.0', kind: 'DataContract', id: c.identifier || 'dataset', version: c.version || '1.0.0',
        status: 'draft', name: c.title || c.identifier || 'dataset' };
      var desc = pick([['purpose', c.description], ['limitations', c.access_rights]]);
      if (Object.keys(desc).length) out.description = desc;
      if (c.theme.length) out.domain = c.theme[0];
      if (c.keywords.length) out.tags = c.keywords.slice();
      if (c.contact) out.team = { name: c.contact };
      if (c.issued) out.contractCreatedTs = c.issued;
      if (c.accrual) out.slaProperties = [{ property: 'frequency', value: c.accrual }];
      if (c.distributions.length) out.servers = c.distributions.map(function (d, i) {
        return pick([['server', d.title || 'distribution-' + (i + 1)], ['type', 'https'], ['location', d.url], ['format', d.format || d.media_type]]); });
      if (cp.length) out.customProperties = cp;
      return out;
    };
    W.write = Wr;

    function filled(c, k) {
      var v = c[k];
      if (k === 'distributions') return v.length > 0 && v.every(function (d) { return d.url; });
      return v !== '' && v !== null && v !== undefined && !(Array.isArray(v) && !v.length);
    }
    W.cdaCheck = function (c) {
      var out = {}, total = 0;
      CDA.forEach(function (p) {
        var k = p[0], st, why;
        if (k === 'distributions') {
          var ds = c.distributions;
          st = ds.length && ds.every(function (d) { return media(d); }) ? 'pass' : (ds.length ? 'partial' : 'missing');
          why = st === 'pass' ? 'Every distribution states a format' : (ds.length ? 'Some distributions have no format' : 'No distributions');
        } else if (k === 'description') {
          var n = Array.from(c.description).length;
          st = n >= 40 ? 'pass' : (n ? 'partial' : 'missing');
          why = n + ' characters' + (n >= 40 ? '' : ' (aim for at least 40)');
        } else {
          st = filled(c, k) ? 'pass' : 'missing';
          why = st === 'pass' ? 'Present' : 'Not in the record';
        }
        out[p[1]] = { status: st, field: k, why: why };
        total += st === 'pass' ? 1 : st === 'partial' ? 0.5 : 0;
      });
      return { properties: out, coverage: pyRound(100 * total / CDA.length, 1) };
    };
    W.coverage = function (c) {
      var out = {};
      TARGETS.forEach(function (t) {
        var can = CARRY[t], f = can.filter(function (k) { return filled(c, k); });
        out[t] = { filled: f.length, total: can.length, missing: can.filter(function (k) { return f.indexOf(k) < 0; }),
          not_carried: KEYS.filter(function (k) { return can.indexOf(k) < 0 && filled(c, k); }) };
      });
      return out;
    };
    // Application profiles (weaver.py PROFILES): simplified SHACL-style shapes, issues #11, #12, #13.
    var PROFILES = [
      ['dcat-ap-3', 'DCAT-AP 3 (European data portals)', 'dcat', ['dct:title', 'dct:description'],
        ['dcat:contactPoint', 'dcat:distribution', 'dcat:keyword', 'dct:publisher', 'dct:spatial', 'dct:temporal', 'dcat:theme']],
      ['geodcat-ap', 'GeoDCAT-AP (geospatial catalogues)', 'geodcat', ['dct:title', 'dct:description', 'dcat:contactPoint', 'dct:publisher', 'dct:spatial'],
        ['dct:conformsTo', 'dct:temporal', 'dct:license', 'dct:accessRights', 'dcat:distribution', 'dcat:keyword', 'dct:modified']],
      ['statdcat-ap', 'StatDCAT-AP (statistical catalogues)', 'statdcat', ['dct:title', 'dct:description'],
        ['dct:accrualPeriodicity', 'dct:temporal', 'dct:spatial', 'dcat:distribution', 'stat:dimension', 'stat:statMeasure', 'dqv:hasQualityAnnotation']],
      ['uk-gemini', 'UK GEMINI (geospatial metadata, as the critical data asset guidance asks for geospatial data)', 'geodcat',
        ['dct:title', 'dct:description', 'dcat:keyword', 'dct:temporal', 'dct:issued', 'dct:publisher', 'dcat:contactPoint',
          'dct:spatial', 'dct:identifier', 'dct:accessRights', 'dct:license', 'dct:conformsTo', 'dct:provenance', 'dcat:distribution'],
        ['dct:modified', 'dct:accrualPeriodicity', 'dcat:theme']],
      ['uk-cda', 'UK critical data asset properties (GOV.UK data asset management guidance)', 'dcat',
        ['dct:title', 'dct:description', 'dct:publisher', 'dct:issued', 'dqc:expires', 'dct:isReplacedBy', 'dct:temporal',
          'dct:conformsTo', 'dct:accessRights', 'dqc:securityClassification', 'dct:license'],
        ['dct:identifier', 'dcat:distribution', 'dcat:contactPoint', 'dct:accrualPeriodicity', 'dcat:keyword']]
    ];
    var DATE_PROPS = ['dct:issued', 'dct:modified', 'dqc:expires'];
    var ISO_DATE = /^[0-9]{4}(-[0-9]{2}(-[0-9]{2}([T ][0-9]{2}:[0-9]{2}(:[0-9]{2}(\.[0-9]+)?)?(Z|[+-][0-9]{2}:?[0-9]{2})?)?)?)?$/;
    function present(v) { return v !== undefined && v !== null && v !== '' && !(Array.isArray(v) && !v.length) && !(isObj(v) && !Object.keys(v).length); }
    W.toGeodcat = function (c) {
      var out = Wr.dcat(c);
      out['@context'] = Object.assign({}, CTX, { locn: 'http://www.w3.org/ns/locn#' });
      if (c.spatial) out['dct:spatial'] = c.spatial.indexOf('http') === 0 ? { '@type': 'dct:Location', '@id': c.spatial }
        : { '@type': 'dct:Location', 'locn:geographicName': c.spatial };
      return out;
    };
    W.toStatdcat = function (c) {
      var out = Wr.dcat(c);
      out['@context'] = Object.assign({}, CTX, { stat: 'http://data.europa.eu/(xyz)/statdcat-ap/', dqv: 'http://www.w3.org/ns/dqv#' });
      return out;
    };
    W.checkProfile = function (out, must, should) {
      var props = [];
      [['must', must], ['should', should]].forEach(function (lk) { lk[1].forEach(function (k) {
        props.push({ property: k, level: lk[0], status: present(out[k]) ? 'pass' : 'missing' }); }); });
      var dates = DATE_PROPS.filter(function (k) { return typeof out[k] === 'string' && !ISO_DATE.test(out[k]); })
        .map(function (k) { return { property: k, value: out[k], message: 'Not an ISO 8601 date (for example 2026-04-01)' }; });
      var musts = props.filter(function (p) { return p.level === 'must'; });
      var ok = function (p) { return p.status === 'pass'; };
      return { conforms: musts.every(ok) && !dates.length, must_met: musts.filter(ok).length, must_total: musts.length,
        should_met: props.filter(function (p) { return p.level === 'should' && ok(p); }).length, should_total: props.length - musts.length,
        properties: props, date_issues: dates };
    };
    // Values the critical data asset metadata guidance constrains (weaver.py uk_values).
    W.ukValues = function (out) {
      var issues = [], ar = out['dct:accessRights'], sc = out['dqc:securityClassification'], pub = out['dct:publisher'];
      if (typeof ar === 'string' && ar && !/^(open|commercial|internal)/.test(pyStrip(ar).toLowerCase()))
        issues.push({ property: 'dct:accessRights', value: ar, message: 'Start with Open, Commercial or Internal, then any handling caveat' });
      if (typeof sc === 'string' && sc && pyStrip(sc).toUpperCase().indexOf('OFFICIAL') !== 0)
        issues.push({ property: 'dqc:securityClassification', value: sc, message: 'Only OFFICIAL assets, including those with a handling caveat, are in scope of the DAM policy' });
      var name = isObj(pub) ? (pub['foaf:name'] || '') : (typeof pub === 'string' ? pub : '');
      if (name.indexOf('@') >= 0) issues.push({ property: 'dct:publisher', value: name, message: "Use the organisation's name, not a person or an email address" });
      return issues;
    };
    W.profiles = function (c) {
      var outs = { dcat: Wr.dcat(c), geodcat: W.toGeodcat(c), statdcat: W.toStatdcat(c) }, res = {};
      PROFILES.forEach(function (p) {
        var chk = W.checkProfile(outs[p[2]], p[3], p[4]);
        chk.value_issues = p[0] === 'uk-cda' ? W.ukValues(outs[p[2]]) : [];
        chk.conforms = chk.conforms && !chk.value_issues.length;
        res[p[0]] = { label: p[1], check: chk };
        if (p[2] !== 'dcat') res[p[0]].output = outs[p[2]];
      });
      return res;
    };
    // DQV: the Weaver's findings as W3C Data Quality Vocabulary (weaver.py to_dqv).
    var DQV_CTX = { dqv: 'http://www.w3.org/ns/dqv#', dcat: 'http://www.w3.org/ns/dcat#', dct: 'http://purl.org/dc/terms/',
      skos: 'http://www.w3.org/2004/02/skos/core#', xsd: 'http://www.w3.org/2001/XMLSchema#', dqc: CTX.dqc };
    var TNAMES = { dcat: 'DCAT v3', schema: 'schema.org', ckan: 'CKAN', odcs: 'ODCS' };
    W.toDqv = function (c, cov, cda, prof) {
      var dim = { '@id': 'dqc:metadata' };
      function m(mid, label, value, dtype) {
        return { '@type': 'dqv:QualityMeasurement', 'dqv:value': value,
          'dqv:isMeasurementOf': { '@id': 'dqc:metric-' + mid, '@type': 'dqv:Metric', 'skos:prefLabel': label,
            'dqv:expectedDataType': { '@id': dtype }, 'dqv:inDimension': dim } };
      }
      var ms = [m('cda-coverage', 'Critical data asset metadata properties present (percent)', cda.coverage, 'xsd:decimal')];
      TARGETS.forEach(function (t) { var x = cov[t]; ms.push(m('coverage-' + t, 'Fields ' + TNAMES[t] + ' can carry that are filled (percent)',
        x.total ? pyRound(100 * x.filled / x.total, 1) : 0, 'xsd:decimal')); });
      Object.keys(prof).forEach(function (pid) { ms.push(m('conforms-' + pid, 'Meets the must-have properties of ' + prof[pid].label, !!prof[pid].check.conforms, 'xsd:boolean')); });
      var missing = Object.keys(cda.properties).filter(function (k) { return cda.properties[k].status !== 'pass'; });
      var out = { '@context': DQV_CTX, '@type': 'dqv:QualityMetadata', 'dct:title': 'Metadata quality: ' + (c.title || c.identifier || 'dataset'),
        'dct:subject': c.identifier || c.title || 'dataset', 'dqv:hasQualityMeasurement': ms };
      if (missing.length) out['dqv:hasQualityAnnotation'] = [{ '@type': 'dqv:QualityAnnotation', 'dqv:inDimension': dim,
        'dct:description': 'Critical data asset properties missing or partial: ' + missing.join(', ') }];
      if (c.conforms_to) out['dct:conformsTo'] = c.conforms_to;
      return out;
    };
    W.weave = function (rec, fmt) {
      var r = W.read(rec, fmt), c = r[1], outputs = {};
      TARGETS.forEach(function (t) { outputs[t] = Wr[t](c); });
      var cov = W.coverage(c), cda = W.cdaCheck(c), prof = W.profiles(c);
      return { source_format: r[0], canonical: c, outputs: outputs, coverage: cov, cda: cda, profiles: prof, quality: W.toDqv(c, cov, cda, prof) };
    };
    DQ.weaver = W;
  })();

  // Internals, exposed for the parity tests.
  DQ._py = { pdNumber: pdNumber, pyFloat: pyFloat, pyRound: pyRound, pyFloatRepr: pyFloatRepr, parseDate: parseDate,
    isType: isType, translateRegex: translateRegex, isoDurationDays: isoDurationDays, pySum: pySum, pairwiseSum: pairwiseSum };

  g.DQ = DQ;
  if (typeof module !== 'undefined' && module.exports) module.exports = DQ;
})(typeof window !== 'undefined' ? window : globalThis);
