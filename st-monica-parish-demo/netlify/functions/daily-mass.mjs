// Read the Mass selected by the broadcaster, rather than guessing from upload dates.
const origin = 'https://dailytvmass.com';
export async function latestMass(fetcher = fetch) {
  async function read(url) {
    const response = await fetcher(url, { signal: AbortSignal.timeout(8000) });
    if (!response.ok) throw new Error('Daily TV Mass is unavailable');
    return response.text();
  }
  const home = await read(origin + '/');
  const path = home.match(/href=["'](?:https:\/\/dailytvmass\.com)?(\/mass\/[a-z0-9-]+\/)["']/i)?.[1];
  if (!path) throw new Error('Featured Mass not found');
  const page = await read(origin + path);
  const videoId = page.match(/(?:youtube(?:-nocookie)?\.com\/embed\/)([\w-]{11})(?:[?"'\s])/i)?.[1];
  if (!videoId) throw new Error('Mass video not found');
  return { videoId, source: origin + path };
}
export default async () => {
  try {
    return Response.json(await latestMass(), {
      headers: { 'Cache-Control': 'public, max-age=300, s-maxage=900' }
    });
  } catch {
    // The page keeps the official uploads playlist and direct broadcaster link.
    return Response.json({ unavailable: true }, {
      status: 503, headers: { 'Cache-Control': 'no-store' }
    });
  }
};
