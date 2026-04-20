import { useCallback, useEffect, useState } from 'react';

const LS_ACCESS = 'banco_access';
const LS_REFRESH = 'banco_refresh';
const LS_USER = 'banco_username';

async function apiFetch(path, { method = 'GET', body, skipAuth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (!skipAuth) {
    const access = localStorage.getItem(LS_ACCESS);
    if (access) headers.Authorization = `Bearer ${access}`;
  }
  const res = await fetch(path, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  return { ok: res.ok, status: res.status, data };
}

function formatError(data) {
  if (!data) return 'Error desconocido';
  if (typeof data === 'string') return data;
  if (data.detail) return String(data.detail);
  const parts = [];
  for (const [k, v] of Object.entries(data)) {
    let msg = Array.isArray(v) ? v.join(', ') : (typeof v === 'object' ? JSON.stringify(v) : v);
    // Hide the field name for typical user-facing errors
    if (['monto', 'cuenta_destino', 'cuenta_origen', 'non_field_errors'].includes(k)) {
      parts.push(msg);
    } else {
      parts.push(`${k}: ${msg}`);
    }
  }
  return parts.join('\n') || JSON.stringify(data);
}

export default function App() {
  const [username, setUsername] = useState(() => localStorage.getItem(LS_USER) ?? '');
  const [password, setPassword] = useState('');
  const [logged, setLogged] = useState(() => !!localStorage.getItem(LS_ACCESS));
  const [cuentas, setCuentas] = useState([]);
  const [cuentaId, setCuentaId] = useState('');
  const [montoOp, setMontoOp] = useState('');
  const [cuentaDestinoId, setCuentaDestinoId] = useState('');
  const [montoTransfer, setMontoTransfer] = useState('');
  const [movimientos, setMovimientos] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [mensaje, setMensaje] = useState('');
  const [error, setError] = useState('');

  const [clientes, setClientes] = useState([]);
  const [nuevoCliente, setNuevoCliente] = useState({
    username: '', password: '', nombre_completo: '', numero_identificacion: '',
    email: '', telefono: '', direccion: '', fecha_nacimiento: ''
  });
  const [nuevaCuenta, setNuevaCuenta] = useState({
    cliente: '', tipo: 'ahorros', saldo: '0', fecha_apertura: ''
  });

  const isAdmin = username === 'admin';

  const cargarCuentas = useCallback(async () => {
    setCargando(true);
    setError('');
    const { ok, data } = await apiFetch('/api/cuentas/');
    setCargando(false);
    if (!ok) {
      setError(formatError(data));
      return;
    }
    const list = Array.isArray(data) ? data : data?.results ?? [];
    setCuentas(list);
    if (list.length && !cuentaId) {
      setCuentaId(String(list[0].id));
    }
  }, [cuentaId]);

  const cargarClientes = useCallback(async () => {
    if (!isAdmin) return;
    const { ok, data } = await apiFetch('/api/clientes/');
    if (ok) {
      setClientes(Array.isArray(data) ? data : data?.results ?? []);
    }
  }, [isAdmin]);

  useEffect(() => {
    if (logged) {
      cargarCuentas();
      if (isAdmin) cargarClientes();
    }
  }, [logged, cargarCuentas, cargarClientes, isAdmin]);

  const cargarMovimientos = async () => {
    if (!cuentaId) return;
    setCargando(true);
    setError('');
    const { ok, data } = await apiFetch(`/api/cuentas/${cuentaId}/movimientos/`);
    setCargando(false);
    if (!ok) {
      setError(formatError(data));
      return;
    }
    setMovimientos(Array.isArray(data) ? data : []);
  };

  useEffect(() => {
    if (logged && cuentaId) cargarMovimientos();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [logged, cuentaId]);

  const login = async (e) => {
    e.preventDefault();
    setError('');
    setMensaje('');
    setCargando(true);
    const { ok, data } = await apiFetch('/api/auth/token/', {
      method: 'POST',
      body: { username, password },
      skipAuth: true,
    });
    setCargando(false);
    if (!ok) {
      setError(formatError(data));
      return;
    }
    localStorage.setItem(LS_ACCESS, data.access);
    localStorage.setItem(LS_REFRESH, data.refresh);
    localStorage.setItem(LS_USER, username);
    setLogged(true);
    setMensaje('Sesión iniciada.');
  };

  const logout = () => {
    localStorage.removeItem(LS_ACCESS);
    localStorage.removeItem(LS_REFRESH);
    localStorage.removeItem(LS_USER);
    setLogged(false);
    setCuentas([]);
    setMovimientos([]);
    setClientes([]);
    setMensaje('');
    setError('');
  };

  const crearCliente = async (e) => {
    e.preventDefault();
    setError(''); setMensaje(''); setCargando(true);
    const { ok, data } = await apiFetch('/api/clientes/', {
      method: 'POST',
      body: nuevoCliente,
    });
    setCargando(false);
    if (!ok) {
      setError(formatError(data));
      return;
    }
    setMensaje('Cliente creado exitosamente.');
    setNuevoCliente({username: '', password: '', nombre_completo: '', numero_identificacion: '', email: '', telefono: '', direccion: '', fecha_nacimiento: ''});
    cargarClientes();
  };

  const crearCuenta = async (e) => {
    e.preventDefault();
    setError(''); setMensaje(''); setCargando(true);
    const { ok, data } = await apiFetch('/api/cuentas/', {
      method: 'POST',
      body: {
        ...nuevaCuenta,
        cliente: Number(nuevaCuenta.cliente),
        saldo: Number(nuevaCuenta.saldo),
        estado: 'activa',
      },
    });
    setCargando(false);
    if (!ok) {
      setError(formatError(data));
      return;
    }
    setMensaje('Cuenta creada exitosamente.');
    setNuevaCuenta({cliente: '', tipo: 'ahorros', saldo: '0', fecha_apertura: ''});
    cargarCuentas();
  };

  const deposito = async (e) => {
    e.preventDefault();
    setError('');
    setMensaje('');
    setCargando(true);
    const { ok, data } = await apiFetch(`/api/cuentas/${cuentaId}/deposito/`, {
      method: 'POST',
      body: { monto: montoOp },
    });
    setCargando(false);
    if (!ok) {
      setError(formatError(data));
      return;
    }
    setMensaje(`Depósito registrado. Nuevo saldo: ${data.saldo_resultante}`);
    setMontoOp('');
    await cargarCuentas();
    await cargarMovimientos();
  };

  const retiro = async (e) => {
    e.preventDefault();
    setError('');
    setMensaje('');
    setCargando(true);
    const { ok, data } = await apiFetch(`/api/cuentas/${cuentaId}/retiro/`, {
      method: 'POST',
      body: { monto: montoOp },
    });
    setCargando(false);
    if (!ok) {
      setError(formatError(data));
      return;
    }
    setMensaje(`Retiro registrado. Nuevo saldo: ${data.saldo_resultante}`);
    setMontoOp('');
    await cargarCuentas();
    await cargarMovimientos();
  };

  const transferir = async (e) => {
    e.preventDefault();
    setError('');
    setMensaje('');
    setCargando(true);
    const { ok, data } = await apiFetch('/api/transferencias/', {
      method: 'POST',
      body: {
        cuenta_origen: Number(cuentaId),
        cuenta_destino: Number(cuentaDestinoId),
        monto: montoTransfer,
      },
    });
    setCargando(false);
    if (!ok) {
      setError(formatError(data));
      return;
    }
    setMensaje(`Transferencia #${data.id} completada.`);
    setMontoTransfer('');
    setCuentaDestinoId('');
    await cargarCuentas();
    await cargarMovimientos();
  };

  if (!logged) {
    return (
      <div className="app">
        <h1>Gestión Bancaria</h1>
        <p className="small">
          Conecta contra la API Django (backend en <code>http://127.0.0.1:8000</code>). Ejecuta{' '}
          <code>npm run dev</code> en <code>frontend/</code> y el proxy enviará <code>/api</code> al
          backend.
        </p>
        <div className="card">
          <form onSubmit={login}>
            <label htmlFor="u">Usuario</label>
            <input
              id="u"
              value={username}
              onChange={(ev) => setUsername(ev.target.value)}
              autoComplete="username"
              required
            />
            <label htmlFor="p">Contraseña</label>
            <input
              id="p"
              type="password"
              value={password}
              onChange={(ev) => setPassword(ev.target.value)}
              autoComplete="current-password"
              required
            />
            {error ? <div className="msg-error">{error}</div> : null}
            {mensaje ? <div className="msg-ok">{mensaje}</div> : null}
            <button type="submit" disabled={cargando}>
              {cargando ? 'Entrando…' : 'Iniciar sesión'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="toolbar">
        <h1 style={{ flex: 1, margin: 0 }}>Panel — Gestión Bancaria</h1>
        <span className="small">Usuario: {username}</span>
        <button type="button" className="secondary" onClick={logout}>
          Cerrar sesión
        </button>
      </div>

      {error ? <div className="msg-error">{error}</div> : null}
      {mensaje ? <div className="msg-ok">{mensaje}</div> : null}

      {isAdmin && (
        <div className="card row cols-2">
          <div>
            <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Crear Cliente (Admin)</h2>
            <form onSubmit={crearCliente}>
              <input placeholder="Usuario" value={nuevoCliente.username} onChange={e => setNuevoCliente({...nuevoCliente, username: e.target.value})} required />
              <input placeholder="Contraseña" type="password" value={nuevoCliente.password} onChange={e => setNuevoCliente({...nuevoCliente, password: e.target.value})} required />
              <input placeholder="Nombre Completo" value={nuevoCliente.nombre_completo} onChange={e => setNuevoCliente({...nuevoCliente, nombre_completo: e.target.value})} required />
              <input placeholder="Número de Identificación" value={nuevoCliente.numero_identificacion} onChange={e => setNuevoCliente({...nuevoCliente, numero_identificacion: e.target.value})} required />
              <input placeholder="Email" type="email" value={nuevoCliente.email} onChange={e => setNuevoCliente({...nuevoCliente, email: e.target.value})} required />
              <input placeholder="Teléfono" value={nuevoCliente.telefono} onChange={e => setNuevoCliente({...nuevoCliente, telefono: e.target.value})} required />
              <input placeholder="Dirección" value={nuevoCliente.direccion} onChange={e => setNuevoCliente({...nuevoCliente, direccion: e.target.value})} required />
              <label>Fecha de Nacimiento</label>
              <input type="date" value={nuevoCliente.fecha_nacimiento} onChange={e => setNuevoCliente({...nuevoCliente, fecha_nacimiento: e.target.value})} required />
              <button type="submit" disabled={cargando}>Crear Cliente</button>
            </form>
          </div>
          <div>
            <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Crear Cuenta (Admin)</h2>
            <form onSubmit={crearCuenta}>
              <label>Cliente</label>
              <select value={nuevaCuenta.cliente} onChange={e => setNuevaCuenta({...nuevaCuenta, cliente: e.target.value})} required>
                <option value="">-- Seleccionar Cliente --</option>
                {clientes.map(c => <option key={c.id} value={c.id}>{c.nombre_completo} ({c.numero_identificacion})</option>)}
              </select>
              <label>Tipo de Cuenta</label>
              <select value={nuevaCuenta.tipo} onChange={e => setNuevaCuenta({...nuevaCuenta, tipo: e.target.value})} required>
                <option value="ahorros">Ahorros</option>
                <option value="corriente">Corriente</option>
              </select>
              <label>Saldo Inicial</label>
              <input placeholder="0.00" value={nuevaCuenta.saldo} onChange={e => setNuevaCuenta({...nuevaCuenta, saldo: e.target.value})} required />
              <label>Fecha de Apertura</label>
              <input type="date" value={nuevaCuenta.fecha_apertura} onChange={e => setNuevaCuenta({...nuevaCuenta, fecha_apertura: e.target.value})} required />
              <button type="submit" disabled={cargando}>Crear Cuenta</button>
            </form>
          </div>
        </div>
      )}

      <div className="card">
        <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Cuentas</h2>
        <button type="button" onClick={cargarCuentas} disabled={cargando}>
          Actualizar lista
        </button>
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Número</th>
              <th>Tipo</th>
              <th>Saldo</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            {cuentas.map((c) => (
              <tr key={c.id}>
                <td>{c.id}</td>
                <td>{c.numero_cuenta}</td>
                <td>{c.tipo}</td>
                <td>{c.saldo}</td>
                <td>{c.estado}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {cuentas.length === 0 ? <p className="small">No hay cuentas visibles para este usuario.</p> : null}
      </div>

      <div className="card row cols-2">
        <div>
          <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Depósito / retiro</h2>
          <label htmlFor="cuenta">Cuenta</label>
          <select id="cuenta" value={cuentaId} onChange={(e) => setCuentaId(e.target.value)}>
            {cuentas.map((c) => (
              <option key={c.id} value={c.id}>
                {c.numero_cuenta} — {c.tipo} ({c.saldo})
              </option>
            ))}
          </select>
          <label htmlFor="monto">Monto</label>
          <input
            id="monto"
            value={montoOp}
            onChange={(e) => setMontoOp(e.target.value)}
            placeholder="0.00"
          />
          <div className="toolbar">
            <button type="button" disabled={cargando || !cuentaId} onClick={deposito}>
              Depositar
            </button>
            <button type="button" disabled={cargando || !cuentaId} className="secondary" onClick={retiro}>
              Retirar
            </button>
          </div>
        </div>
        <div>
          <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Transferencia</h2>
          <p className="small">Origen: la cuenta seleccionada arriba.</p>
          <label htmlFor="dest">ID cuenta destino</label>
          <input
            id="dest"
            value={cuentaDestinoId}
            onChange={(e) => setCuentaDestinoId(e.target.value)}
            placeholder="Ej. 2"
          />
          <label htmlFor="mt">Monto</label>
          <input
            id="mt"
            value={montoTransfer}
            onChange={(e) => setMontoTransfer(e.target.value)}
            placeholder="0.00"
          />
          <button type="button" disabled={cargando || !cuentaId} onClick={transferir}>
            Transferir
          </button>
        </div>
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Movimientos (cuenta seleccionada)</h2>
        <button type="button" onClick={cargarMovimientos} disabled={cargando || !cuentaId}>
          Actualizar movimientos
        </button>
        <table>
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Tipo</th>
              <th>Monto</th>
              <th>Saldo resultante</th>
            </tr>
          </thead>
          <tbody>
            {movimientos.map((m) => (
              <tr key={m.id}>
                <td>{m.fecha}</td>
                <td>{m.tipo}</td>
                <td>{m.monto}</td>
                <td>{m.saldo_resultante}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {movimientos.length === 0 ? <p className="small">Sin movimientos aún.</p> : null}
      </div>
    </div>
  );
}
