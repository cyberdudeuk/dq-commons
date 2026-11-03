// Automated accessibility checks (axe-core) on every portal page: desktop light and phone dark.
// Usage (in CI): npm install --no-save playwright @axe-core/playwright && npx playwright install chromium
//                node scripts/a11y_check.mjs portal/dist
// Fails (exit 1) on any serious or critical violation of WCAG 2.0, 2.1 or 2.2 A and AA rules.
// Automated checks find only part of the problems; testing with disabled people is still needed (BL-02).
import { chromium } from 'playwright';
import { AxeBuilder } from '@axe-core/playwright';
import { readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const dist = resolve(process.argv[2] || 'portal/dist');
const pages = readdirSync(dist).filter((f) => f.endsWith('.html')).sort();
const modes = [{ name: 'desktop-light', viewport: { width: 1280, height: 900 }, colorScheme: 'light' },
               { name: 'phone-dark', viewport: { width: 390, height: 844 }, colorScheme: 'dark' }];
const browser = await chromium.launch();
let bad = 0;
for (const m of modes) {
  const ctx = await browser.newContext({ viewport: m.viewport, colorScheme: m.colorScheme });
  for (const f of pages) {
    const page = await ctx.newPage();
    await page.goto(pathToFileURL(resolve(dist, f)).href);
    await page.waitForTimeout(300);
    const r = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']).analyze();
    const serious = r.violations.filter((v) => ['serious', 'critical'].includes(v.impact));
    for (const v of serious) console.log(`${m.name} ${f}: [${v.impact}] ${v.id} - ${v.help} (${v.nodes.length} element(s))`);
    bad += serious.length;
    await page.close();
  }
  await ctx.close();
}
await browser.close();
console.log(bad ? `${bad} serious or critical accessibility problem(s).` : `No serious or critical problems on ${pages.length} pages x ${modes.length} modes.`);
process.exit(bad ? 1 : 0);
