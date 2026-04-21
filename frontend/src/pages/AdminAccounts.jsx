import { useEffect, useState } from 'react';
import { apiGet, apiPost, apiPatch, apiDelete } from '../api/client';
import Modal from '../components/Modal';

export default function AdminAccounts() {
  const [cuentas, setCuentas] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    cliente: '', tipo: 'ahorros', saldo: '0', fecha_apertura: '', estado: 'activa',
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    try {
      const [cuData, clData] = await Promise.all([
        apiGet('/api/cuentas/'),
        apiGet('/api/clientes/'),
      ]);
      setCuentas((cuData.results || cuData) ?? []);
      setClientes((clData.results || clData) ?? []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const openCreate = () => {
    setEditing(null);
    const today = new Date().toISOString().split('T')[0];
    setForm({ cliente: '', tipo: 'ahorros', saldo: '0', fecha_apertura: today, estado: 'activa' });
    setError('');
    setShowModal(true);
  };

  const openEdit = (cuenta) => {
    setEditing(cuenta);
    setForm({
      cliente: cuenta.cliente,
      tipo: cuenta.tipo,
      saldo: cuenta.saldo,
      fecha_apertura: cuenta.fecha_apertura,
      estado: cuenta.estado,
    });
    setError('');
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar esta cuenta?')) return;
    try {
      await apiDelete(`/api/cuentas/${id}/`);
      setLoading(true);
      await loadData();
    } catch (err) {
      alert(err.data?.detail || 'Error al eliminar la cuenta.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const payload = {
        cliente: parseInt(form.cliente),
        tipo: form.tipo,
        saldo: form.saldo,
        fecha_apertura: form.fecha_apertura,
        estado: form.estado,
      };

      if (editing) {
        await apiPatch(`/api/cuentas/${editing.id}/`, payload);
      } else {
        await apiPost('/api/cuentas/', payload);
      }
      setShowModal(false);
      setLoading(true);
      await loadData();
    } catch (err) {
      if (err.data) {
        const msgs = Object.entries(err.data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('. ');
        setError(msgs);
      } else {
        setError('Error al guardar la cuenta.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="page-loading"><div className="spinner" /><p>Cargando cuentas...</p></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Gestión de Cuentas Bancarias</h1>
        <button className="btn btn-primary" onClick={openCreate}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Nueva Cuenta
        </button>
      </div>

      <div className="card">
        <div className="card-body">
          {cuentas.length === 0 ? (
            <p className="empty-state">No hay cuentas registradas</p>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Número</th>
                    <th>Cliente</th>
                    <th>Tipo</th>
                    <th>Saldo</th>
                    <th>Estado</th>
                    <th>Apertura</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {cuentas.map((c) => {
                    const clienteInfo = clientes.find(cl => cl.id === c.cliente);
                    return (
                      <tr key={c.id}>
                        <td className="mono">{c.numero_cuenta}</td>
                        <td>{clienteInfo?.nombre_completo || `Cliente #${c.cliente}`}</td>
                        <td><span className={`badge badge-${c.tipo === 'ahorros' ? 'info' : 'warning'}`}>{c.tipo}</span></td>
                        <td className="mono">${parseFloat(c.saldo).toLocaleString('es-CO', { minimumFractionDigits: 2 })}</td>
                        <td>
                          <span className={`badge badge-${c.estado === 'activa' ? 'success' : c.estado === 'bloqueada' ? 'danger' : 'warning'}`}>
                            {c.estado}
                          </span>
                        </td>
                        <td>{new Date(c.fecha_apertura).toLocaleDateString('es-CO')}</td>
                        <td>
                          <div className="action-buttons">
                            <button className="btn btn-ghost btn-sm" onClick={() => openEdit(c)} title="Editar">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                              </svg>
                            </button>
                            <button className="btn btn-danger btn-sm" onClick={() => handleDelete(c.id)} title="Eliminar">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                              </svg>
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Modal crear/editar */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editing ? 'Editar Cuenta' : 'Nueva Cuenta Bancaria'}>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Cliente</label>
            <select
              value={form.cliente}
              onChange={(e) => setForm({ ...form, cliente: e.target.value })}
              required
              disabled={!!editing}
            >
              <option value="">Seleccione un cliente</option>
              {clientes.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre_completo} — {c.numero_identificacion}</option>
              ))}
            </select>
          </div>
          <div className="form-grid">
            <div className="form-group">
              <label>Tipo de cuenta</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
                <option value="ahorros">Ahorros</option>
                <option value="corriente">Corriente</option>
              </select>
            </div>
            <div className="form-group">
              <label>Estado</label>
              <select value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
                <option value="activa">Activa</option>
                <option value="inactiva">Inactiva</option>
                <option value="bloqueada">Bloqueada</option>
              </select>
            </div>
          </div>
          <div className="form-grid">
            <div className="form-group">
              <label>Saldo inicial</label>
              <input
                type="number" step="0.01" min="0"
                value={form.saldo}
                onChange={(e) => setForm({ ...form, saldo: e.target.value })}
                required
              />
            </div>
            <div className="form-group">
              <label>Fecha de apertura</label>
              <input
                type="date"
                value={form.fecha_apertura}
                onChange={(e) => setForm({ ...form, fecha_apertura: e.target.value })}
                required
              />
            </div>
          </div>
          <button type="submit" className="btn btn-primary btn-full" disabled={submitting}>
            {submitting ? <span className="spinner-sm" /> : null}
            {submitting ? 'Guardando...' : editing ? 'Actualizar Cuenta' : 'Crear Cuenta'}
          </button>
        </form>
      </Modal>
    </div>
  );
}
