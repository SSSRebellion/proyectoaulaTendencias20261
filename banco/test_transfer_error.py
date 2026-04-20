import urllib.request
import urllib.error
import json

def do_req(url, data=None, token=None):
    req = urllib.request.Request(url)
    if data:
        req.data = json.dumps(data).encode('utf-8')
        req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        with urllib.request.urlopen(req) as response:
            return response.getcode(), json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

code, data = do_req('http://127.0.0.1:8000/api/auth/token/', {'username': 'admin', 'password': 'admin'})
token = data['access']

code, cuentas = do_req('http://127.0.0.1:8000/api/cuentas/', token=token)
c1 = cuentas[0]['id']
c2 = cuentas[1]['id']

code, resp = do_req('http://127.0.0.1:8000/api/transferencias/', {'cuenta_origen': c1, 'cuenta_destino': c2, 'monto': '50000000.00'}, token)
print(code)
print(resp)
