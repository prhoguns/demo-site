import test from 'node:test';
import assert from 'node:assert/strict';
import { latestMass } from '../netlify/functions/daily-mass.mjs';

test('follows the featured Mass, ignoring unrelated homepage videos', async () => {
  const urls = [];
  const result = await latestMass(async url => {
    urls.push(url);
    return new Response(url.endsWith('/mass/september-18-2026/')
      ? '<iframe src="https://www.youtube.com/embed/9b844-Dm2sU?rel=0"></iframe>'
      : '<a href="https://dailytvmass.com/mass/september-18-2026/">Watch today</a><iframe src="https://www.youtube.com/embed/AAAAAAAAAAA"></iframe>');
  });
  assert.equal(result.videoId, '9b844-Dm2sU');
  assert.equal(result.source, urls[1]);
  assert.equal(urls.length, 2);
});

test('follows changed featured dates without rebuilding', async () => {
  const result = await latestMass(async url => new Response(url.endsWith('/mass/september-19-2026/')
    ? '<iframe src="https://www.youtube-nocookie.com/embed/BBBBBBBBBBB"></iframe>'
    : '<a href="/mass/september-19-2026/">Watch today</a>'));
  assert.equal(result.videoId, 'BBBBBBBBBBB');
});

test('fails safely on upstream errors, missing features and malformed video IDs', async () => {
  await assert.rejects(latestMass(async () => new Response('', { status: 503 })));
  await assert.rejects(latestMass(async () => new Response('<html>No Mass found</html>')));
  await assert.rejects(latestMass(async url => new Response(url.endsWith('/mass/today/')
    ? '<iframe src="https://www.youtube.com/embed/invalid"></iframe>'
    : '<a href="/mass/today/">Watch</a>')));
});
