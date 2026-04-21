import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import Modal from '../components/Modal';

export default function Transfers() {
  const [transferencias, setTransferencias] = useState([]);
  const [cuentas, setCuentas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ cuenta_origen: '', cuenta_destino: '', monto: '', descripcion: '' });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    try {
      const [tData, cData] = await Promise.all([
        apiGet('/api/transferencias/'),
        apiGet('/api/cuentas/'),
      ]);
      setTransferencias((tData.results || tData) ?? []);
      setCuentas((cData.results || cData) ?? []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      await apiPost('/api/transferencias/', {
        cuenta_origen: parseInt(form.cuenta_origen),
        cuenta_destino: parseInt(form.cuenta_destino),
        monto: form.monto,
        descripcion: form.descripcion,
      });
      setShowModal(false);
      setForm({ cuenta_origen: '', cuenta_destino: '', monto: '', descripcion: '' });
      setLoading(true);
      await loadData();
    } catch (err) {
      if (err.data) {
        const msgs = Object.values(err.data).flat().join('. ');
        setError(msgs);
      } else {
        setError('Error al realizar la transferencia.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="page-loading"><div className="spinner" /><p>Cargando transferencias...</p></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Transferencias</h1>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="17 1 21 5 17 9" /><path d="M3 11V9a4 4 0 0 1 4-4h14" />
          </svg>
          Nueva Transferencia
        </button>
      </div>

      <div className="card">
        <div className="card-body">
          {transferencias.length === 0 ? (
            <p className="empty-state">No hay transferencias registradas</p>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Origen</th>
                    <th>Destino</th>
                    <th>Monto</th>
                    <th>Estado</th>
                    <th>Descripción</th>
                    <th>Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {transferencias.map((t) => (
                    <tr key={t.id}>
                      <td className="mono">#{t.id}</td>
                      <td>
                        <div className="cell-stack">
                          <span className="mono">{t.cuenta_origen_numero}</span>
                          <span className="cell-sub">{t.cliente_origen_nombre}</span>
                        </div>
                      </td>
                      <td>
                        <div className="cell-stack">
                          <span className="mono">{t.cuenta_destino_numero}</span>
                          <span className="cell-sub">{t.cliente_destino_nombre}</span>
                        </div>
                      </td>
                      <td className="mono">${parseFloat(t.monto).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                      <td><span className="badge badge-success">{t.estado_display || t.estado}</span></td>
                      <td>{t.descripcion || '—'}</td>
                      <td>{new Date(t.fecha).toLocaleString('es-CO')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Modal nueva transferencia */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nueva Transferencia">
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="tr-origen">Cuenta Origen</label>
            <select
              id="tr-origen"
              value={form.cuenta_origen}
              onChange={(e) => setForm({ ...form, cuenta_origen: e.target.value })}
              required
            >
              <option value="">Seleccione cuenta origen</option>
              {cuentas.filter(c => c.estado === 'activa').map((c) => (
                <option key={c.id} value={c.id}>
                  {c.numero_cuenta} — ${parseFloat(c.saldo).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="tr-destino">Cuenta Destino (ID)</label>
            <input
              id="tr-destino"
              type="number"
              value={form.cuenta_destino}
              onChange={(e) => setForm({ ...form, cuenta_destino: e.target.value })}
              placeholder="ID de la cuenta destino"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="tr-monto">Monto</label>
            <input
              id="tr-monto"
              type="number"
              step="0.01"
              min="0.01"
              value={form.monto}
              onChange={(e) => setForm({ ...form, monto: e.target.value })}
              placeholder="0.00"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="tr-desc">Descripción (opcional)</label>
            <input
              id="tr-desc"
              type="text"
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              placeholder="Concepto de la transferencia"
            />
          </div>
          <button type="submit" className="btn btn-primary btn-full" disabled={submitting}>
            {submitting ? <span className="spinner-sm" /> : null}
            {submitting ? 'Procesando...' : 'Realizar Transferencia'}
          </button>
        </form>
      </Modal>
    </div>
  );
}
