import { useEffect, useState } from 'react';
import { apiGet, apiPost } from '../api/client';
import Modal from '../components/Modal';

export default function Deposits() {
  const [depositos, setDepositos] = useState([]);
  const [cuentas, setCuentas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ cuenta: '', monto: '', tipo_operacion: 'deposito', descripcion: '' });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    try {
      const [dData, cData] = await Promise.all([
        apiGet('/api/depositos/'),
        apiGet('/api/cuentas/'),
      ]);
      setDepositos((dData.results || dData) ?? []);
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
      await apiPost('/api/depositos/', {
        cuenta: parseInt(form.cuenta),
        monto: form.monto,
        tipo_operacion: form.tipo_operacion,
        descripcion: form.descripcion,
      });
      setShowModal(false);
      setForm({ cuenta: '', monto: '', tipo_operacion: 'deposito', descripcion: '' });
      setLoading(true);
      await loadData();
    } catch (err) {
      if (err.data) {
        const msgs = Object.values(err.data).flat().join('. ');
        setError(msgs);
      } else {
        setError('Error al realizar la operación.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="page-loading"><div className="spinner" /><p>Cargando movimientos...</p></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Depósitos y Retiros</h1>
        <button className="btn btn-primary" onClick={() => setShowModal(true)}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Nueva Operación
        </button>
      </div>

      <div className="card">
        <div className="card-body">
          {depositos.length === 0 ? (
            <p className="empty-state">No hay movimientos registrados</p>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Cuenta</th>
                    <th>Tipo</th>
                    <th>Monto</th>
                    <th>Saldo Resultante</th>
                    <th>Descripción</th>
                    <th>Fecha</th>
                  </tr>
                </thead>
                <tbody>
                  {depositos.map((d) => (
                    <tr key={d.id}>
                      <td className="mono">#{d.id}</td>
                      <td className="mono">{d.numero_cuenta}</td>
                      <td>
                        <span className={`badge ${d.tipo_operacion === 'deposito' ? 'badge-success' : 'badge-danger'}`}>
                          {d.tipo_operacion_display || d.tipo_operacion}
                        </span>
                      </td>
                      <td className="mono">${parseFloat(d.monto).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                      <td className="mono">${parseFloat(d.saldo_resultante).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                      <td>{d.descripcion || '—'}</td>
                      <td>{new Date(d.fecha).toLocaleString('es-CO')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Modal nueva operación */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="Nueva Operación">
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="dep-cuenta">Cuenta</label>
            <select
              id="dep-cuenta"
              value={form.cuenta}
              onChange={(e) => setForm({ ...form, cuenta: e.target.value })}
              required
            >
              <option value="">Seleccione una cuenta</option>
              {cuentas.filter(c => c.estado === 'activa').map((c) => (
                <option key={c.id} value={c.id}>
                  {c.numero_cuenta} — ${parseFloat(c.saldo).toLocaleString('es-CO', { minimumFractionDigits: 2 })}
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="dep-tipo">Tipo de operación</label>
            <select
              id="dep-tipo"
              value={form.tipo_operacion}
              onChange={(e) => setForm({ ...form, tipo_operacion: e.target.value })}
            >
              <option value="deposito">Depósito</option>
              <option value="retiro">Retiro</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="dep-monto">Monto</label>
            <input
              id="dep-monto"
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
            <label htmlFor="dep-desc">Descripción (opcional)</label>
            <input
              id="dep-desc"
              type="text"
              value={form.descripcion}
              onChange={(e) => setForm({ ...form, descripcion: e.target.value })}
              placeholder="Concepto del movimiento"
            />
          </div>
          <button type="submit" className="btn btn-primary btn-full" disabled={submitting}>
            {submitting ? <span className="spinner-sm" /> : null}
            {submitting ? 'Procesando...' : 'Realizar Operación'}
          </button>
        </form>
      </Modal>
    </div>
  );
}
