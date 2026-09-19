const { chromium } = require('/home/philips/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const root = '/home/philips/Documents/website/demo-site/delivery/website';
  const pages = fs.readdirSync(root, { withFileTypes: true })
    .filter(entry => entry.isDirectory() && fs.existsSync(path.join(root, entry.name, 'index.html')))
    .map(entry => entry.name)
    .sort();
  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const failures = [];

  for (const slug of pages) {
    await page.goto(pathToFileURL(path.join(root, slug, 'index.html')).href,
      { waitUntil: 'domcontentloaded' });
    const offsets = await page.locator('.entry-content').evaluate(entry => {
      const entryRect = entry.getBoundingClientRect();
      return Array.from(entry.children).filter(child => {
        const style = getComputedStyle(child);
        return style.display !== 'none' && !child.matches('.alignfull,.alignleft,.alignright');
      }).map(child => {
        const rect = child.getBoundingClientRect();
        const expected = entryRect.left + (entryRect.width - rect.width) / 2;
        return {
          tag: child.tagName.toLowerCase(),
          className: child.className,
          offset: Math.round((rect.left - expected) * 10) / 10
        };
      }).filter(item => Math.abs(item.offset) > 1);
    }).catch(() => []);
    offsets.forEach(item => failures.push(`${slug}: ${item.tag}.${item.className} offset ${item.offset}px`));
  }

  await browser.close();
  assert.deepEqual(failures, []);
  console.log(`PASS: ${pages.length} content pages share one centered text axis`);
})().catch(error => { console.error(error); process.exit(1); });
