const CHARGER_API = 'https://wx.isfdz.com/api/equi/afterProtocol/getLineInfo';
const APP_ID = '1ff95d3fcfe75503';
const STU_STATIONS = [
  '4GR00008495', '4GR00008489', '4GR00008490', '4GR00008498',
  '4GR00008497', '4GR00008480', '4GR00008484', '4GR00008485',
  '4GR00008488', '4GR00008493', '4GR00008494', '4GR00008491',
  '4GR00008492'
];

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

async function queryStation(code) {
  try {
    const body = JSON.stringify({
      code,
      parentCode: null,
      timestamp: Date.now(),
      app_id: APP_ID,
      sign: 'fake'
    });
    const resp = await fetch(CHARGER_API, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json;charset=UTF-8' },
      body,
      signal: AbortSignal.timeout(5000)
    });
    const result = await resp.json();
    if (result.code === 200 && Array.isArray(result.data) && result.data.length > 0) {
      const ports = result.data;
      return {
        code,
        total: ports.length,
        free: ports.filter(p => p.state === 1).length,
        busy: ports.filter(p => p.state === 2).length,
      };
    }
  } catch (e) {}
  return null;
}

export default async function handler(req) {
  if (req.method === 'OPTIONS') {
    return new Response(null, { status: 200, headers: CORS_HEADERS });
  }

  const url = new URL(req.url);
  const path = url.pathname.replace(/\/$/, '');

  if (path === '' || path === '/') {
    return Response.json({ status: 'ok', service: 'stu-charger-proxy' }, { headers: CORS_HEADERS });
  }

  if (path === '/all') {
    try {
      const results = await Promise.all(STU_STATIONS.map(queryStation));
      const valid = results.filter(r => r !== null);
      return Response.json(
        { code: 200, data: valid, timestamp: Date.now() },
        { headers: CORS_HEADERS }
      );
    } catch (e) {
      return Response.json({ code: 500, msg: e.message }, { status: 500, headers: CORS_HEADERS });
    }
  }

  return Response.json({ code: 404, msg: 'not found' }, { status: 404, headers: CORS_HEADERS });
}
