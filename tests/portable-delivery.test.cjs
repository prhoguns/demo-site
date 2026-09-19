const { chromium } = require('/home/philips/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  const root = '/home/philips/Documents/website/demo-site/delivery/website';
  const browser = await chromium.launch({
    executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox']
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  const homeSource = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
  assert(!homeSource.includes('"index.html>'), 'portable URL rewriting damaged self-closing markup');
  await page.goto(pathToFileURL(path.join(root, 'index.html')).href, { waitUntil: 'domcontentloaded' });

  assert.equal(await page.locator('h1').innerText(), 'Welcome to\nSt. Columba Parish');
  assert((await page.locator('.hero').getAttribute('style')).includes('hero-church-interior'));
  const heroBackground = await page.locator('.hero').evaluate(element => getComputedStyle(element).backgroundImage);
  assert(heroBackground.includes('/delivery/website/wp-content/'));
  assert(!heroBackground.includes('/assets/wp-content/'));
  assert.deepEqual(await page.locator('.hero__actions a').allTextContents(),
    ['Mass times', 'New here?', 'Daily Readings']);
  assert.equal(await page.getByRole('link', { name: 'Daily Readings', exact: true }).first().getAttribute('href'),
    'https://readings.livingwithchrist.ca/');
  assert.deepEqual(await page.locator('.tile h3').allTextContents(),
    ['Sacraments', 'Ministries', 'Weekly Bulletin', 'New Here?']);
  assert.equal(await page.locator('#ministries .media-row').count(), 3);
  assert.equal((await page.locator('#ministries .ministries-all').textContent()).trim(), 'All Ministries');
  assert.equal((await page.locator('.quote-band blockquote p').textContent()).trim(),
    '“Be at peace, and have unfeigned charity among yourselves.”');
  assert.equal(await page.locator('.quote-band cite a').getAttribute('href'),
    'https://celt.ucc.ie/published/L201040.html');
  const firstMinistryImage = page.locator('#ministries img').first();
  await firstMinistryImage.scrollIntoViewIfNeeded();
  await firstMinistryImage.evaluate(image => image.decode());
  assert((await firstMinistryImage.evaluate(image => image.naturalWidth)) > 0);

  await page.locator('#searchToggle').click();
  await page.locator('#searchInput').fill('baptism');
  const searchHref = await page.locator('#searchResults a').first().getAttribute('href');
  assert(searchHref.startsWith('file:') && searchHref.endsWith('/index.html'));

  await page.goto(pathToFileURL(path.join(root, 'events/index.html')).href,
    { waitUntil: 'domcontentloaded' });
  const eventHref = await page.locator('.month-cal__event').first().getAttribute('href');
  assert(eventHref.startsWith('file:') && /\/index\.html(?:#.*)?$/.test(eventHref));

  await page.goto(pathToFileURL(path.join(root, 'questions/index.html')).href,
    { waitUntil: 'domcontentloaded' });
  const questionImages = await page.locator('main img').evaluateAll(images => images.map(image => image.src));
  assert(questionImages.length > 0);
  assert(questionImages.every(src => !/(priest-greeting|baptism-pouring|baptism-font|stock-church-interior)/.test(src)));

  await page.goto(pathToFileURL(path.join(root, 'gallery/index.html')).href,
    { waitUntil: 'domcontentloaded' });
  const galleryImages = await page.locator('.gallery img').evaluateAll(images => images.map(image => image.src));
  assert(galleryImages.length >= 10);
  assert(galleryImages.every(src => !/(priest-greeting|baptism-pouring|baptism-font|stock-church-interior)/.test(src)));
  assert.deepEqual(errors, []);

  await browser.close();
  console.log('PASS: portable file preview, Daily Readings, homepage, ministries, search, Questions and gallery');
})().catch(error => { console.error(error); process.exit(1); });
