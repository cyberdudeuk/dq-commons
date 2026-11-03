/*
 * Read Excel (.xlsx), OpenDocument (.ods), JSON and JSON Lines files in the browser, with no
 * libraries and no upload, and turn the first (or a chosen) sheet into CSV text for the engine.
 *
 * Uses the browser's own DecompressionStream('deflate-raw') to open the zip container, and
 * DOMParser for the XML inside. Dates become YYYY-MM-DD; everything else is written as shown.
 * The Python toolkit (dqkit/sources.py) remains the reference for large or unusual files.
 */
(function (g) {
  'use strict';
  var S = {};

  // ---------- zip ----------
  function u16(b, o) { return b[o] | (b[o + 1] << 8); }
  function u32(b, o) { return (b[o] | (b[o + 1] << 8) | (b[o + 2] << 16) | (b[o + 3] << 24)) >>> 0; }
  async function inflate(bytes) {
    if (typeof DecompressionStream === 'undefined') throw new Error('this browser cannot open spreadsheets; save the sheet as CSV instead');
    var stream = new Blob([bytes]).stream().pipeThrough(new DecompressionStream('deflate-raw'));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }
  async function unzip(buf, wanted) {
    var b = new Uint8Array(buf), eocd = -1;
    for (var i = b.length - 22; i >= Math.max(0, b.length - 65557); i--) if (u32(b, i) === 0x06054b50) { eocd = i; break; }
    if (eocd < 0) throw new Error('not a zip-based spreadsheet');
    var n = u16(b, eocd + 10), off = u32(b, eocd + 16), out = {}, dec = new TextDecoder('utf-8');
    for (var k = 0; k < n; k++) {
      if (u32(b, off) !== 0x02014b50) throw new Error('damaged spreadsheet (central directory)');
      var method = u16(b, off + 10), csize = u32(b, off + 20), nlen = u16(b, off + 28), xlen = u16(b, off + 30), clen = u16(b, off + 32), lho = u32(b, off + 42);
      var name = dec.decode(b.subarray(off + 46, off + 46 + nlen));
      off += 46 + nlen + xlen + clen;
      if (!wanted(name)) continue;
      var start = lho + 30 + u16(b, lho + 26) + u16(b, lho + 28), data = b.subarray(start, start + csize);
      out[name] = dec.decode(method === 0 ? data : method === 8 ? await inflate(data) : (function () { throw new Error('unsupported compression in ' + name); })());
    }
    return out;
  }
  function xml(text) { return new DOMParser().parseFromString(text, 'application/xml'); }
  function kids(el, local) { return Array.prototype.filter.call(el.childNodes, function (c) { return c.nodeType === 1 && c.localName === local; }); }
  function all(el, local) { return Array.prototype.slice.call(el.getElementsByTagNameNS('*', local)); }

  // ---------- xlsx ----------
  var DATE_FMT_IDS = { 14: 1, 15: 1, 16: 1, 17: 1, 18: 0, 19: 0, 20: 0, 21: 0, 22: 1, 27: 1, 30: 1, 36: 1, 45: 0, 46: 0, 47: 0, 50: 1, 57: 1 };
  function colIndex(ref) { var m = /^([A-Z]+)/.exec(ref), n = 0; for (var i = 0; i < m[1].length; i++) n = n * 26 + (m[1].charCodeAt(i) - 64); return n - 1; }
  function serialToISO(v) { var d = new Date(Math.round((v - 25569) * 864e5)); return d.toISOString().slice(0, 10); }
  function num(s) { var x = Number(s); return Number.isFinite(x) && String(x) !== s && Math.abs(x) < 1e15 ? String(parseFloat(x.toPrecision(15))) : s; }
  async function readXlsx(buf, sheetName) {
    var f = await unzip(buf, function (n) { return /^xl\/(workbook\.xml|sharedStrings\.xml|styles\.xml|worksheets\/[^/]+\.xml|_rels\/workbook\.xml\.rels)$/.test(n); });
    var wb = xml(f['xl/workbook.xml']), rels = xml(f['xl/_rels/workbook.xml.rels'] || '<r/>');
    var sheets = all(wb, 'sheet').map(function (s) { return { name: s.getAttribute('name'), rid: s.getAttributeNS('http://schemas.openxmlformats.org/officeDocument/2006/relationships', 'id') || s.getAttribute('r:id') }; });
    var target = {}; all(rels, 'Relationship').forEach(function (r) { target[r.getAttribute('Id')] = r.getAttribute('Target'); });
    var pick = sheetName ? sheets.filter(function (s) { return s.name === sheetName; })[0] : sheets[0];
    if (!pick) throw new Error('no sheet called ' + sheetName + '. Sheets: ' + sheets.map(function (s) { return s.name; }).join(', '));
    var path = 'xl/' + String(target[pick.rid] || 'worksheets/sheet1.xml').replace(/^\/?xl\//, '').replace(/^\//, '');
    if (!f[path]) throw new Error('sheet ' + pick.name + ' could not be read');
    var shared = f['xl/sharedStrings.xml'] ? all(xml(f['xl/sharedStrings.xml']), 'si').map(function (si) { return all(si, 't').map(function (t) { return t.textContent; }).join(''); }) : [];
    var dateStyles = [];
    if (f['xl/styles.xml']) {
      var st = xml(f['xl/styles.xml']), custom = {};
      all(st, 'numFmt').forEach(function (nf) { custom[nf.getAttribute('numFmtId')] = nf.getAttribute('formatCode'); });
      var xfs = all(st, 'cellXfs')[0];
      if (xfs) kids(xfs, 'xf').forEach(function (xf, i) {
        var id = +xf.getAttribute('numFmtId'), code = custom[id] || '';
        dateStyles[i] = DATE_FMT_IDS[id] !== undefined || (/[dmy]/i.test(code.replace(/"[^"]*"|\[[^\]]*\]/g, '')) && !/^[#0.,%]+$/.test(code));
      });
    }
    var rows = [], width = 0;
    all(xml(f[path]), 'row').forEach(function (row) {
      var r = +row.getAttribute('r') - 1, cells = [];
      kids(row, 'c').forEach(function (c, j) {
        var ref = c.getAttribute('r'), ci = ref ? colIndex(ref) : j, t = c.getAttribute('t'), v = kids(c, 'v')[0], val = '';
        if (t === 's') val = shared[+v.textContent] || '';
        else if (t === 'inlineStr') val = all(c, 't').map(function (x) { return x.textContent; }).join('');
        else if (t === 'b') val = v && v.textContent === '1' ? 'TRUE' : 'FALSE';
        else if (v) { val = v.textContent; if (t !== 'str' && t !== 'e' && dateStyles[+c.getAttribute('s') || 0] && val !== '') val = serialToISO(+val); else if (!t || t === 'n') val = num(val); }
        cells[ci] = val;
      });
      rows[r >= 0 ? r : rows.length] = cells; width = Math.max(width, cells.length);
    });
    return { sheets: sheets.map(function (s) { return s.name; }), sheet: pick.name, rows: tidy(rows, width) };
  }

  // ---------- ods ----------
  async function readOds(buf, sheetName) {
    var f = await unzip(buf, function (n) { return n === 'content.xml'; });
    var doc = xml(f['content.xml']), tables = all(doc, 'table').filter(function (t) { return t.namespaceURI && /table/.test(t.namespaceURI); });
    var names = tables.map(function (t) { return t.getAttributeNS(t.namespaceURI, 'name') || t.getAttribute('table:name'); });
    var idx = sheetName ? names.indexOf(sheetName) : 0;
    if (idx < 0) throw new Error('no sheet called ' + sheetName + '. Sheets: ' + names.join(', '));
    var T = tables[idx], ns = T.namespaceURI, OFF = 'urn:oasis:names:tc:opendocument:xmlns:office:1.0', rows = [], width = 0;
    all(T, 'table-row').forEach(function (row) {
      var rep = Math.min(+(row.getAttributeNS(ns, 'number-rows-repeated') || 1), 1000), cells = [];
      Array.prototype.forEach.call(row.childNodes, function (c) {
        if (c.nodeType !== 1 || (c.localName !== 'table-cell' && c.localName !== 'covered-table-cell')) return;
        var n = Math.min(+(c.getAttributeNS(ns, 'number-columns-repeated') || 1), 1024), type = c.getAttributeNS(OFF, 'value-type'), val;
        if (type === 'date') val = String(c.getAttributeNS(OFF, 'date-value') || '').slice(0, 10);
        else if (type === 'float' || type === 'percentage' || type === 'currency') val = num(c.getAttributeNS(OFF, 'value'));
        else if (type === 'boolean') val = c.getAttributeNS(OFF, 'boolean-value') === 'true' ? 'TRUE' : 'FALSE';
        else val = all(c, 'p').map(function (p) { return p.textContent; }).join('\n');
        for (var k = 0; k < n; k++) cells.push(val);
      });
      for (var k = 0; k < rep; k++) { rows.push(cells.slice()); width = Math.max(width, cells.length); }
    });
    return { sheets: names, sheet: names[idx], rows: tidy(rows, width) };
  }

  // Drop trailing empty rows and columns (spreadsheets pad both).
  function tidy(rows, width) {
    rows = rows.map(function (r) { var x = []; for (var i = 0; i < width; i++) x.push(r && r[i] !== undefined ? r[i] : ''); return x; });
    while (rows.length && rows[rows.length - 1].every(function (v) { return v === ''; })) rows.pop();
    var w = 0; rows.forEach(function (r) { for (var i = r.length - 1; i >= 0; i--) if (r[i] !== '') { w = Math.max(w, i + 1); break; } });
    return rows.map(function (r) { return r.slice(0, w); });
  }

  // ---------- json ----------
  function readJson(text, lines) {
    var data;
    if (lines) data = text.split(/\r?\n/).filter(function (l) { return l.trim(); }).map(function (l, i) { try { return JSON.parse(l); } catch (e) { throw new Error('line ' + (i + 1) + ' is not valid JSON'); } });
    else {
      data = JSON.parse(text);
      if (!Array.isArray(data)) { var k = Object.keys(data || {}).filter(function (x) { return Array.isArray(data[x]); })[0]; if (!k) throw new Error('expected a list of records'); data = data[k]; }
    }
    var cols = [];
    data.forEach(function (r) { if (r && typeof r === 'object') Object.keys(r).forEach(function (c) { if (cols.indexOf(c) < 0) cols.push(c); }); });
    var rows = [cols].concat(data.map(function (r) { return cols.map(function (c) { var v = r ? r[c] : null;
      return v === null || v === undefined ? '' : typeof v === 'object' ? JSON.stringify(v) : String(v); }); }));
    return { sheets: [], sheet: null, rows: rows };
  }

  S.toCSV = function (rows) {
    return rows.map(function (r) { return r.map(function (v) { v = String(v); return /[",\r\n]/.test(v) || /^\s|\s$/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }).join(','); }).join('\n') + '\n';
  };
  // file: a File or Blob with a name. Returns {csv, sheets, sheet, kind}.
  S.read = async function (file, sheetName) {
    var name = (file.name || '').toLowerCase(), kind = /\.xlsx$|\.xlsm$/.test(name) ? 'xlsx' : /\.ods$/.test(name) ? 'ods' : /\.jsonl$|\.ndjson$/.test(name) ? 'jsonl' : /\.json$/.test(name) ? 'json' : /\.tsv$|\.tab$/.test(name) ? 'tsv' : 'csv';
    if (/\.xls$/.test(name)) throw new Error('old .xls files are not supported in the browser; save as .xlsx or CSV');
    var r;
    if (kind === 'xlsx') r = await readXlsx(await file.arrayBuffer(), sheetName);
    else if (kind === 'ods') r = await readOds(await file.arrayBuffer(), sheetName);
    else if (kind === 'json' || kind === 'jsonl') r = readJson(await file.text(), kind === 'jsonl');
    else if (kind === 'tsv') r = { sheets: [], sheet: null, rows: (await file.text()).replace(/^﻿/, '').split(/\r?\n/).filter(function (l, i, a) { return l !== '' || i < a.length - 1; }).map(function (l) { return l.split('\t'); }) };
    else return { csv: (await file.text()).replace(/^﻿/, ''), sheets: [], sheet: null, kind: kind };
    if (!r.rows.length) throw new Error('the file has no rows');
    return { csv: S.toCSV(r.rows), sheets: r.sheets, sheet: r.sheet, kind: kind };
  };
  g.DQSheets = S;
})(typeof window !== 'undefined' ? window : globalThis);
