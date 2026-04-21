import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiGet } from '../api/client';

export default function Dashboard() {
  const { user, isAdmin } = useAuth();
  const [cuentas, setCuentas] = useState([]);
  const [depositos, setDepositos] = useState([]);
  const [transferencias, setTransferencias] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [cData, dData, tData] = await Promise.all([
          apiGet('/api/cuentas/'),
          apiGet('/api/depositos/'),
          apiGet('/api/transferencias/'),
        ]);
        setCuentas((cData.results || cData) ?? []);
        setDepositos((dData.results || dData) ?? []);
        setTransferencias((tData.results || tData) ?? []);
      } catch (err) {
        console.error('Error cargando dashboard:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="page-loading"><div className="spinner" /><p>Cargando dashboard...</p></div>;
  }

  const saldoTotal = cuentas.reduce((sum, c) => sum + parseFloat(c.saldo || 0), 0);
  const cuentasActivas = cuentas.filter((c) => c.estado === 'activa').length;
  const ultMovimientos = depositos.slice(0, 5);
  const ultTransferencias = transferencias.slice(0, 5);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <p className="page-subtitle">
          Bienvenido, {user?.nombreCompleto || user?.username || 'Usuario'}
          {isAdmin && <span className="badge badge-admin">Administrador</span>}
        </p>
      </div>

      {/* KPI Cards */}
      <div className="stats-grid">
        <div className="stat-card stat-primary">
          <div className="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="1" x2="12" y2="23" /><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
            </svg>
          </div>
          <div className="stat-info">
            <span className="stat-value">${saldoTotal.toLocaleString('es-CO', { minimumFractionDigits: 2 })}</span>
            <span className="stat-label">Saldo Total</span>
          </div>
        </div>
        <div className="stat-card stat-success">
          <div className="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="2" y="5" width="20" height="14" rx="2" /><line x1="2" y1="10" x2="22" y2="10" />
            </svg>
          </div>
          <div className="stat-info">
            <span className="stat-value">{cuentasActivas}</span>
            <span className="stat-label">Cuentas Activas</span>
          </div>
        </div>
        <div className="stat-card stat-info">
          <div className="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" /><polyline points="17 6 23 6 23 12" />
            </svg>
          </div>
          <div className="stat-info">
            <span className="stat-value">{depositos.length}</span>
            <span className="stat-label">Movimientos</span>
          </div>
        </div>
        <div className="stat-card stat-warning">
          <div className="stat-icon">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="17 1 21 5 17 9" /><path d="M3 11V9a4 4 0 0 1 4-4h14" />
              <polyline points="7 23 3 19 7 15" /><path d="M21 13v2a4 4 0 0 1-4 4H3" />
            </svg>
          </div>
          <div className="stat-info">
            <span className="stat-value">{transferencias.length}</span>
            <span className="stat-label">Transferencias</span>
          </div>
        </div>
      </div>

      {/* Recent activity */}
      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h2>Últimos Movimientos</h2>
          </div>
          <div className="card-body">
            {ultMovimientos.length === 0 ? (
              <p className="empty-state">No hay movimientos recientes</p>
            ) : (
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Tipo</th>
                      <th>Monto</th>
                      <th>Saldo Resultante</th>
                      <th>Fecha</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ultMovimientos.map((d) => (
                      <tr key={d.id}>
                        <td>
                          <span className={`badge ${d.tipo_operacion === 'deposito' ? 'badge-success' : 'badge-danger'}`}>
                            {d.tipo_operacion_display || d.tipo_operacion}
                          </span>
                        </td>
                        <td className="mono">${parseFloat(d.monto).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                        <td className="mono">${parseFloat(d.saldo_resultante).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                        <td>{new Date(d.fecha).toLocaleDateString('es-CO')}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2>Últimas Transferencias</h2>
          </div>
          <div className="card-body">
            {ultTransferencias.length === 0 ? (
              <p className="empty-state">No hay transferencias recientes</p>
            ) : (
              <div className="table-responsive">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Origen</th>
                      <th>Destino</th>
                      <th>Monto</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ultTransferencias.map((t) => (
                      <tr key={t.id}>
                        <td className="mono">{t.cuenta_origen_numero}</td>
                        <td className="mono">{t.cuenta_destino_numero}</td>
                        <td className="mono">${parseFloat(t.monto).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                        <td><span className="badge badge-success">{t.estado_display || t.estado}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
