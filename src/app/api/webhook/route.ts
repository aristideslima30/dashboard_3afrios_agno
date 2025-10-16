export const dynamic = 'force-dynamic'

export async function POST(req: Request) {
  try {
    const backendBase = (process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');
    const url = `${backendBase}/webhook`;

    // Preserve incoming body and content-type when proxying
    const body = await req.text();
    const contentType = req.headers.get('content-type') || 'application/json';

    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': contentType },
      body,
    });

    const resText = await res.text();
    const resType = res.headers.get('content-type') || 'application/json';
    return new Response(resText, { status: res.status, headers: { 'Content-Type': resType } });
  } catch (err) {
    return new Response(
      JSON.stringify({ ok: false, error: 'proxy_failed', detail: String(err) }),
      {
        status: 502,
        headers: { 'Content-Type': 'application/json' },
      }
    );
  }
}

export async function GET() {
  return new Response(
    JSON.stringify({ ok: true, route: 'webhook', mode: 'proxy' }),
    {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }
  );
}