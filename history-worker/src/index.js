const ALLOWED_ORIGINS = new Set(['https://my4d.vercel.app']);   // Origin 头不带末尾斜杠
const TTL_MS = 5 * 60 * 1000;
const shardCache = new Map();                                    // isolate 内缓存

const json = (body, status, extra) => new Response(JSON.stringify(body), {
  status, headers: { 'Content-Type': 'application/json; charset=utf-8',
    'X-Content-Type-Options': 'nosniff', ...extra } });

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const cors = { 'Vary': 'Origin' };
    if (ALLOWED_ORIGINS.has(origin)) {          // 不在白名单就不回写 ACAO，更不要返回 "null"
      cors['Access-Control-Allow-Origin'] = origin;
      cors['Access-Control-Allow-Methods'] = 'GET, OPTIONS';
      cors['Access-Control-Allow-Headers'] = 'Content-Type';
    }
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
    if (request.method !== 'GET') return json({ error: 'method not allowed' }, 405, { ...cors, Allow: 'GET, OPTIONS' });

    const url = new URL(request.url);
    if (url.pathname !== '/api/history') return json({ error: 'not found' }, 404, { ...cors, 'Cache-Control': 'no-store' });
    const num = (url.searchParams.get('num') || '').trim();
    if (!/^\d{4}$/.test(num)) return json({ error: 'invalid number' }, 400, { ...cors, 'Cache-Control': 'no-store' });

    try {
      const prefix = num.slice(0, 2);
      let hit = shardCache.get(prefix);
      if (!hit || Date.now() - hit.at > TTL_MS) {
        const obj = await env.HISTORY.get(prefix + '.json');
        hit = { at: Date.now(), data: obj ? await obj.json() : {} };
        shardCache.set(prefix, hit);
      }
      return json(hit.data[num] || [], 200, { ...cors, 'Cache-Control': 'public, max-age=300' });
    } catch (e) {
      console.error('history lookup failed', e);
      return json({ error: 'upstream error' }, 502, { ...cors, 'Cache-Control': 'no-store' });   // 带 CORS 头，前端能读到错误
    }
  },
};
