const ALLOWED_ORIGIN = 'https://my4d.vercel.app/'\; // 改成实际域名

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const headers = {
      'Access-Control-Allow-Origin': origin === ALLOWED_ORIGIN ? origin : 'null',
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Vary': 'Origin',
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'public, max-age=300'
    };
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers });

    const url = new URL(request.url);
    if (url.pathname !== '/api/history') {
      return new Response(JSON.stringify({ error: 'not found' }), { status: 404, headers });
    }
    const num = (url.searchParams.get('num') || '').trim();
    if (!/^\d{4}$/.test(num)) {
      return new Response(JSON.stringify({ error: 'invalid number' }), { status: 400, headers });
    }

    const obj = await env.HISTORY.get(num.slice(0, 2) + '.json');
    if (!obj) return new Response('[]', { headers });
    const shard = await obj.json();
    return new Response(JSON.stringify(shard[num] || []), { headers });
  }
};
