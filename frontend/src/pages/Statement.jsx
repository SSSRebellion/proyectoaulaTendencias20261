import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { useAuth } from '../context/AuthContext';

function defaultRange() {
  const hasta = new Date();
  const desde = new Date();
  desde.setDate(desde.getDate() - 30);
  return {
    fecha_desde: desde.toISOString().split('T')[0],
    fecha_hasta: hasta.toISOString().split('T')[0],
  };
}

export default function Statement() {
  const { isAdmin } = useAuth();
  const [cuentas, setCuentas] = useState([]);
  const [cuentaId, setCuentaId] = useState('');
  const [fechas, setFechas] = useState(defaultRange);
  const [extracto, setExtracto] = useState(null);
  const [loading, setLoading] = useState(true);
  const [consultando, setConsultando] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        const data = await apiGet('/api/cuentas/');
        const lista = (data.results || data) ?? [];
        setCuentas(lista);
        if (lista.length > 0) setCuentaId(String(lista[0].id));
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const consultar = async (e) => {
    e.preventDefault();
    if (!cuentaId) return;
    setError('');
    setConsultando(true);
    try {
      const data = await apiGet(
        `/api/cuentas/${cuentaId}/extracto/?fecha_desde=${fechas.fecha_desde}&fecha_hasta=${fechas.fecha_hasta}`,
      );
      setExtracto(data);
    } catch (err) {
      if (err.data) {
        const msgs = Object.values(err.data).flat().join('. ');
        setError(msgs);
      } else {
        setError(err.message || 'No se pudo obtener el extracto.');
      }
      setExtracto(null);
    } finally {
      setConsultando(false);
    }
  };

  const fmt = (n) => parseFloat(n).toLocaleString('es-CO', { minimumFractionDigits: 2 });

  if (loading) {
    return <div className="page-loading"><div className="spinner" /><p>Cargando cuentas...</p></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Extracto Bancario</h1>
          <p className="page-subtitle">
            {isAdmin ? 'Consulta extractos de cualquier cuenta' : 'Consulte movimientos de sus cuentas'}
          </p>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          {cuentas.length === 0 ? (
            <p className="empty-state">No tiene cuentas. Cree una en la sección Cuentas.</p>
          ) : (
            <form onSubmit={consultar} className="extracto-form">
              <div className="form-grid">
                <div className="form-group">
                  <label>Cuenta</label>
                  <select value={cuentaId} onChange={(e) => setCuentaId(e.target.value)} required>
                    {cuentas.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.numero_cuenta} — {c.tipo}
                        {isAdmin && c.cliente_nombre ? ` (${c.cliente_nombre})` : ''}
                        {' '}(${fmt(c.saldo)})
                      </option>
                    ))}
                  </select>
                </div>
                <div className="form-group">
                  <label>Desde</label>
                  <input
                    type="date"
                    value={fechas.fecha_desde}
                    onChange={(e) => setFechas({ ...fechas, fecha_desde: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Hasta</label>
                  <input
                    type="date"
                    value={fechas.fecha_hasta}
                    onChange={(e) => setFechas({ ...fechas, fecha_hasta: e.target.value })}
                    required
                  />
                </div>
              </div>
              {error && <div className="alert alert-error">{error}</div>}
              <button type="submit" className="btn btn-primary" disabled={consultando}>
                {consultando ? <span className="spinner-sm" /> : null}
                {consultando ? 'Consultando...' : 'Generar extracto'}
              </button>
            </form>
          )}
        </div>
      </div>

      {extracto && (
        <div className="card">
          <div className="card-body">
            <div className="extracto-resumen">
              <div>
                <span className="text-muted">Cuenta</span>
                <strong className="mono">{extracto.numero_cuenta}</strong>
              </div>
              <div>
                <span className="text-muted">Periodo</span>
                <strong>
                  {new Date(extracto.fecha_desde).toLocaleDateString('es-CO')}
                  {' — '}
                  {new Date(extracto.fecha_hasta).toLocaleDateString('es-CO')}
                </strong>
              </div>
              <div>
                <span className="text-muted">Saldo inicial</span>
                <strong className="mono">${fmt(extracto.saldo_inicial)}</strong>
              </div>
              <div>
                <span className="text-muted">Saldo final</span>
                <strong className="mono">${fmt(extracto.saldo_final)}</strong>
              </div>
            </div>

            {extracto.transacciones.length === 0 ? (
              <p className="empty-state">Sin movimientos en el periodo seleccionado.</p>
            ) : (
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Fecha</th>
                      <th>Tipo</th>
                      <th>Monto</th>
                      <th>Descripción</th>
                      <th>Saldo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {extracto.transacciones.map((t) => (
                      <tr key={t.id}>
                        <td>{new Date(t.fecha).toLocaleString('es-CO')}</td>
                        <td>
                          <span className={`badge ${t.tipo_operacion === 'deposito' ? 'badge-success' : 'badge-danger'}`}>
                            {t.tipo_operacion_display}
                          </span>
                        </td>
                        <td className="mono">${fmt(t.monto)}</td>
                        <td>{t.descripcion || '—'}</td>
                        <td className="mono">${fmt(t.saldo_resultante)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
