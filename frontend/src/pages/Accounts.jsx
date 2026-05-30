import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { apiGet } from '../api/client';

export default function Accounts() {
  const { isAdmin } = useAuth();
  const [cuentas, setCuentas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [resumen, setResumen] = useState(null);

  const loadCuentas = async () => {
    try {
      const data = await apiGet('/api/cuentas/');
      setCuentas((data.results || data) ?? []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadCuentas(); }, []);

  const verResumen = async (cuentaId) => {
    try {
      const data = await apiGet(`/api/cuentas/${cuentaId}/resumen/`);
      setResumen(data);
      setSelected(cuentaId);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return <div className="page-loading"><div className="spinner" /><p>Cargando cuentas...</p></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>{isAdmin ? 'Todas las Cuentas' : 'Mis Cuentas'}</h1>
          <p className="page-subtitle">
            {isAdmin
              ? 'Consulta de todas las cuentas del banco. Para crear o bloquear, use Gestión de Cuentas.'
              : 'Consulte el estado de sus cuentas bancarias'}
          </p>
        </div>
        {isAdmin ? (
          <Link to="/admin/cuentas" className="btn btn-primary">
            Gestionar Cuentas
          </Link>
        ) : null}
      </div>

      {cuentas.length === 0 ? (
        <div className="card">
          <div className="card-body">
            <div className="empty-state-box">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: 'var(--text-muted)' }}>
                <rect x="2" y="5" width="20" height="14" rx="2" /><line x1="2" y1="10" x2="22" y2="10" />
              </svg>
              <p className="empty-state">
                {isAdmin ? 'No hay cuentas registradas' : 'No tiene cuentas bancarias asignadas'}
              </p>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                {isAdmin
                  ? 'Cree cuentas desde la sección de administración'
                  : 'Contacte al administrador para que le asigne una cuenta'}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="accounts-grid">
          {cuentas.map((cuenta) => (
            <div
              key={cuenta.id}
              className={`account-card ${selected === cuenta.id ? 'account-card-selected' : ''}`}
              onClick={() => verResumen(cuenta.id)}
            >
              <div className="account-card-header">
                <span className={`account-type ${cuenta.tipo}`}>
                  {cuenta.tipo === 'ahorros' ? 'Ahorros' : 'Corriente'}
                </span>
                <span className={`badge badge-${cuenta.estado === 'activa' ? 'success' : cuenta.estado === 'bloqueada' ? 'danger' : 'warning'}`}>
                  {cuenta.estado}
                </span>
              </div>
              <div className="account-number">{cuenta.numero_cuenta}</div>
              {isAdmin && cuenta.cliente_nombre && (
                <div className="account-date">Cliente: {cuenta.cliente_nombre}</div>
              )}
              <div className="account-balance">
                <span className="account-balance-label">Saldo disponible</span>
                <span className="account-balance-value">
                  ${parseFloat(cuenta.saldo).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="account-date">
                Apertura: {new Date(cuenta.fecha_apertura).toLocaleDateString('es-CO')}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Panel de resumen */}
      {resumen && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <h2>Resumen de Cuenta</h2>
            <button className="btn btn-ghost btn-sm" onClick={() => { setResumen(null); setSelected(null); }}>Cerrar</button>
          </div>
          <div className="card-body">
            <div className="detail-grid">
              <div className="detail-item">
                <span className="detail-label">Número de Cuenta</span>
                <span className="detail-value mono">{resumen.numero_cuenta}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Tipo</span>
                <span className="detail-value">{resumen.tipo === 'ahorros' ? 'Ahorros' : 'Corriente'}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Saldo</span>
                <span className="detail-value mono">${parseFloat(resumen.saldo).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Estado</span>
                <span className="detail-value">{resumen.estado}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Cliente</span>
                <span className="detail-value">{resumen.cliente_nombre}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Identificación</span>
                <span className="detail-value mono">{resumen.cliente_identificacion}</span>
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
