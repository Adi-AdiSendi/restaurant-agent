// Netlify scheduled function. Render free sleeps after 15 idle minutes, so this
// pings the backend every 10. It calls Render directly: calling the site's own
// /api proxy from a function did not keep it awake (seen live, docs/challenges.md).
// Must match the /api/* redirect in netlify.toml; a test checks they agree.
// /api/health does not touch the database, so the database can still sleep.
export const BACKEND_HEALTH_URL = 'https://restaurant-agent-api.onrender.com/api/health'

export default async function keepAwake(): Promise<void> {
  const started = Date.now()
  try {
    // A sleeping backend can take longer than this to answer; the request
    // still wakes it. Scheduled functions stop at 30 s.
    const response = await fetch(BACKEND_HEALTH_URL, { signal: AbortSignal.timeout(25_000) })
    console.log(`keep_awake status=${response.status} ms=${Date.now() - started}`)
  } catch (error) {
    console.log(`keep_awake failed ms=${Date.now() - started} error=${String(error)}`)
  }
}

export const config = { schedule: '@yearly' }
