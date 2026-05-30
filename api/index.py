from http.server import BaseHTTPRequestHandler
import json
import urllib.request
import time
import concurrent.futures

CHARGER_API = 'https://wx.isfdz.com/api/equi/afterProtocol/getLineInfo'
APP_ID = '1ff95d3fcfe75503'
STU_STATIONS = [
    '4GR00008495', '4GR00008489', '4GR00008490', '4GR00008498',
    '4GR00008497', '4GR00008480', '4GR00008484', '4GR00008485',
    '4GR00008488', '4GR00008493', '4GR00008494', '4GR00008491',
    '4GR00008492'
]

CORS_HEADERS = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
}

def query_station(code):
    try:
        body = json.dumps({
            'code': code,
            'parentCode': None,
            'timestamp': int(time.time() * 1000),
            'app_id': APP_ID,
            'sign': 'fake'
        }).encode('utf-8')
        req = urllib.request.Request(CHARGER_API, data=body, headers={'Content-Type': 'application/json;charset=UTF-8'})
        resp = urllib.request.urlopen(req, timeout=10)
        result = json.loads(resp.read())
        if result.get('code') == 200 and isinstance(result.get('data'), list) and len(result['data']) > 0:
            ports = result['data']
            return {
                'code': code,
                'total': len(ports),
                'free': sum(1 for p in ports if p.get('state') == 1),
                'busy': sum(1 for p in ports if p.get('state') == 2),
            }
    except:
        pass
    return None


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()

    def do_GET(self):
        path = self.path.rstrip('/')
        headers = {**CORS_HEADERS, 'Content-Type': 'application/json'}

        if path == '' or path == '/':
            self.send_response(200)
            for k, v in headers.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok', 'service': 'stu-charger-proxy'}).encode())
            return

        if path == '/all':
            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    results = list(executor.map(query_station, STU_STATIONS))
                valid = [r for r in results if r is not None]
                self.send_response(200)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(json.dumps({'code': 200, 'data': valid, 'timestamp': int(time.time() * 1000)}).encode())
                return
            except Exception as e:
                self.send_response(500)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(json.dumps({'code': 500, 'msg': str(e)}).encode())
                return

        self.send_response(404)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(json.dumps({'code': 404, 'msg': 'not found'}).encode())
