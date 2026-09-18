const { chromium } = require('/home/philips/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert = require('node:assert/strict');

(async () => {
  const base = process.env.WORDPRESS_TEST_URL || 'http://127.0.0.1:8899';
  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(base + '/wp-admin/themes.php', { waitUntil: 'domcontentloaded', timeout: 60000 });
  const parishTheme = page.locator('.theme').filter({ hasText: 'St. Columba Parish' }).first();
  const activate = parishTheme.getByRole('link', { name: 'Activate', exact: true });
  if (await activate.count()) {
    await activate.click();
    await page.waitForLoadState('domcontentloaded');
  }
  await page.goto(base + '/', { waitUntil: 'domcontentloaded', timeout: 60000 });

  assert.equal(await page.locator('h1').innerText(), 'Welcome to\nSt. Columba Parish');
  assert.equal(await page.locator('link[href*="/wp-content/themes/"][href*="/site/assets/site.css"]').count(), 1);
  assert((await page.locator('.hero').getAttribute('style')).includes('hero-church-interior'));
  assert.equal(await page.getByRole('link', { name: 'Daily Readings', exact: true }).first().getAttribute('href'),
    'https://readings.livingwithchrist.ca/');
  assert.equal((await page.locator('#ministries .ministries-all').textContent()).trim(), 'All Ministries');

  const aboutHref = await page.locator('a', { hasText: 'Who We Are' }).first().getAttribute('href');
  assert(aboutHref.endsWith('/about/'));
  const aboutResponse = await page.goto(new URL(aboutHref, base).href, { waitUntil: 'domcontentloaded', timeout: 60000 });
  assert.equal(aboutResponse.status(), 200, `About page returned ${aboutResponse.status()} at ${page.url()}`);
  assert.equal(await page.locator('h1').innerText(), 'Who We Are');
  assert(page.url().endsWith('/about/'));

  await page.goto(base + '/gallery/', { waitUntil: 'domcontentloaded', timeout: 60000 });
  assert((await page.locator('.gallery img').count()) >= 10);
  assert.deepEqual(errors, []);
  assert(!(await page.locator('body').innerText()).includes('Fatal error'));

  await browser.close();
  console.log('PASS: WordPress activation, generated pages, theme assets, Daily Readings and gallery');
})().catch(error => { console.error(error); process.exit(1); });
