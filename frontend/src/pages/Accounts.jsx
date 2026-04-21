import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import Modal from '../components/Modal';

export default function Accounts() {
  const [cuentas, setCuentas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [resumen, setResumen] = useState(null);

  // Modal de creación
  const [showModal, setShowModal] = useState(false);
  const [tipoCuenta, setTipoCuenta] = useState('ahorros');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Pantalla de éxito con número generado
  const [cuentaCreada, setCuentaCreada] = useState(null);

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

  const handleCrear = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const data = await apiPost('/api/cuentas/', { tipo: tipoCuenta });
      setCuentaCreada(data);
      setShowModal(false);
      setTipoCuenta('ahorros');
      // Recargar la lista
      setLoading(true);
      await loadCuentas();
    } catch (err) {
      if (err.data) {
        const msgs = Object.values(err.data).flat().join('. ');
        setError(msgs);
      } else {
        setError('Error al crear la cuenta.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const cerrarExito = () => {
    setCuentaCreada(null);
  };

  if (loading) {
    return <div className="page-loading"><div className="spinner" /><p>Cargando cuentas...</p></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Mis Cuentas</h1>
          <p className="page-subtitle">Consulte el estado de sus cuentas bancarias</p>
        </div>
        <button className="btn btn-primary" onClick={() => { setShowModal(true); setError(''); }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Crear Cuenta
        </button>
      </div>

      {/* Banner de cuenta recién creada */}
      {cuentaCreada && (
        <div className="success-banner">
          <div className="success-banner-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <div className="success-banner-content">
            <h3>¡Cuenta creada exitosamente!</h3>
            <p>Su nueva cuenta de <strong>{cuentaCreada.tipo === 'ahorros' ? 'Ahorros' : 'Corriente'}</strong> ha sido creada.</p>
            <div className="success-account-number">
              <span className="success-label">Número de cuenta asignado</span>
              <span className="success-number">{cuentaCreada.numero_cuenta}</span>
            </div>
          </div>
          <button className="btn btn-ghost btn-sm" onClick={cerrarExito}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      )}

      {cuentas.length === 0 && !cuentaCreada ? (
        <div className="card">
          <div className="card-body">
            <div className="empty-state-box">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: 'var(--text-muted)' }}>
                <rect x="2" y="5" width="20" height="14" rx="2" /><line x1="2" y1="10" x2="22" y2="10" />
              </svg>
              <p className="empty-state">No tiene cuentas bancarias registradas</p>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                Haga clic en "Crear Cuenta" para abrir su primera cuenta
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

      {/* Modal crear cuenta */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Crear Nueva Cuenta">
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleCrear}>
          <div className="create-account-info">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: 'var(--accent-blue-light)' }}>
              <rect x="2" y="5" width="20" height="14" rx="2" /><line x1="2" y1="10" x2="22" y2="10" />
            </svg>
            <p>Se le asignará un <strong>número de cuenta único</strong> al azar automáticamente. La cuenta se abrirá con saldo $0 y estado activa.</p>
          </div>

          <div className="form-group">
            <label htmlFor="tipo-cuenta">Tipo de cuenta</label>
            <select
              id="tipo-cuenta"
              value={tipoCuenta}
              onChange={(e) => setTipoCuenta(e.target.value)}
              required
            >
              <option value="ahorros">🏦 Cuenta de Ahorros</option>
              <option value="corriente">💳 Cuenta Corriente</option>
            </select>
          </div>

          <div className="create-account-details">
            <div className="create-detail">
              <span className="create-detail-label">Saldo inicial</span>
              <span className="create-detail-value">$0.00</span>
            </div>
            <div className="create-detail">
              <span className="create-detail-label">Estado</span>
              <span className="create-detail-value"><span className="badge badge-success">Activa</span></span>
            </div>
            <div className="create-detail">
              <span className="create-detail-label">Fecha de apertura</span>
              <span className="create-detail-value">{new Date().toLocaleDateString('es-CO')}</span>
            </div>
            <div className="create-detail">
              <span className="create-detail-label">Número de cuenta</span>
              <span className="create-detail-value" style={{ color: 'var(--accent-blue-light)' }}>Se generará automáticamente</span>
            </div>
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={submitting}>
            {submitting ? <span className="spinner-sm" /> : null}
            {submitting ? 'Creando cuenta...' : 'Crear Cuenta'}
          </button>
        </form>
      </Modal>
    </div>
  );
}
