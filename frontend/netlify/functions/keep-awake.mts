// Netlify scheduled function. Render free sleeps after 15 idle minutes, so this
// pings the backend every 10 through the site's own /api proxy (URL is set by
// Netlify). /api/health does not touch the database, so the database can sleep.
export default async function keepAwake(): Promise<void> {
  try {
    const response = await fetch(`${process.env.URL ?? ''}/api/health`, {
      signal: AbortSignal.timeout(25_000),
    })
    console.log(`keep_awake status=${response.status}`)
  } catch (error) {
    console.log(`keep_awake failed error=${String(error)}`)
  }
}

export const config = { schedule: '*/10 * * * *' }
