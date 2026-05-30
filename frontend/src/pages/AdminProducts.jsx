import { useEffect, useState } from 'react';
import { apiGet, apiPost, apiPatch, apiDelete } from '../api/client';
import Modal from '../components/Modal';

export default function AdminProducts() {
  const [productos, setProductos] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    cliente: '',
    tipo: 'tarjeta_credito',
    nombre: '',
    cupo: '',
    saldo_utilizado: '0',
    estado: 'activo',
    fecha_vencimiento: '',
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    try {
      const [pData, cData] = await Promise.all([
        apiGet('/api/productos/'),
        apiGet('/api/clientes/'),
      ]);
      setProductos((pData.results || pData) ?? []);
      setClientes((cData.results || cData) ?? []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const openCreate = () => {
    setEditing(null);
    const venc = new Date();
    venc.setFullYear(venc.getFullYear() + 1);
    setForm({
      cliente: '',
      tipo: 'tarjeta_credito',
      nombre: '',
      cupo: '',
      saldo_utilizado: '0',
      estado: 'activo',
      fecha_vencimiento: venc.toISOString().split('T')[0],
    });
    setError('');
    setShowModal(true);
  };

  const openEdit = (p) => {
    setEditing(p);
    setForm({
      cliente: p.cliente,
      tipo: p.tipo,
      nombre: p.nombre,
      cupo: p.cupo,
      saldo_utilizado: p.saldo_utilizado,
      estado: p.estado,
      fecha_vencimiento: p.fecha_vencimiento,
    });
    setError('');
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Eliminar este producto financiero?')) return;
    try {
      await apiDelete(`/api/productos/${id}/`);
      setLoading(true);
      await loadData();
    } catch (err) {
      alert(err.data?.detail || 'Error al eliminar.');
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
        nombre: form.nombre,
        cupo: form.cupo,
        saldo_utilizado: form.saldo_utilizado,
        estado: form.estado,
        fecha_vencimiento: form.fecha_vencimiento,
      };
      if (editing) {
        await apiPatch(`/api/productos/${editing.id}/`, payload);
      } else {
        await apiPost('/api/productos/', payload);
      }
      setShowModal(false);
      setLoading(true);
      await loadData();
    } catch (err) {
      if (err.data) {
        setError(Object.entries(err.data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`).join('. '));
      } else {
        setError('Error al guardar el producto.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  const fmt = (n) => parseFloat(n).toLocaleString('es-CO', { minimumFractionDigits: 2 });

  if (loading) {
    return <div className="page-loading"><div className="spinner" /><p>Cargando productos...</p></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Productos Financieros</h1>
        <button className="btn btn-primary" onClick={openCreate}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Nuevo Producto
        </button>
      </div>

      <div className="card">
        <div className="card-body">
          {productos.length === 0 ? (
            <p className="empty-state">No hay productos registrados</p>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Cliente</th>
                    <th>Tipo</th>
                    <th>Nombre</th>
                    <th>Cupo</th>
                    <th>Utilizado</th>
                    <th>Estado</th>
                    <th>Vencimiento</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {productos.map((p) => (
                    <tr key={p.id}>
                      <td>{p.cliente_nombre}</td>
                      <td>{p.tipo_display}</td>
                      <td>{p.nombre || '—'}</td>
                      <td className="mono">${fmt(p.cupo)}</td>
                      <td className="mono">${fmt(p.saldo_utilizado)}</td>
                      <td><span className="badge badge-info">{p.estado_display}</span></td>
                      <td>{new Date(p.fecha_vencimiento).toLocaleDateString('es-CO')}</td>
                      <td>
                        <div className="action-buttons">
                          <button className="btn btn-ghost btn-sm" onClick={() => openEdit(p)} title="Editar">✎</button>
                          <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p.id)} title="Eliminar">🗑</button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editing ? 'Editar Producto' : 'Nuevo Producto'}>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Cliente</label>
            <select value={form.cliente} onChange={(e) => setForm({ ...form, cliente: e.target.value })} required disabled={!!editing}>
              <option value="">Seleccione</option>
              {clientes.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre_completo}</option>
              ))}
            </select>
          </div>
          <div className="form-grid">
            <div className="form-group">
              <label>Tipo</label>
              <select value={form.tipo} onChange={(e) => setForm({ ...form, tipo: e.target.value })}>
                <option value="tarjeta_credito">Tarjeta de crédito</option>
                <option value="prestamo">Préstamo</option>
              </select>
            </div>
            <div className="form-group">
              <label>Estado</label>
              <select value={form.estado} onChange={(e) => setForm({ ...form, estado: e.target.value })}>
                <option value="activo">Activo</option>
                <option value="inactivo">Inactivo</option>
                <option value="vencido">Vencido</option>
                <option value="bloqueado">Bloqueado</option>
              </select>
            </div>
          </div>
          <div className="form-group">
            <label>Nombre / referencia</label>
            <input value={form.nombre} onChange={(e) => setForm({ ...form, nombre: e.target.value })} placeholder="Visa Oro" />
          </div>
          <div className="form-grid">
            <div className="form-group">
              <label>Cupo</label>
              <input type="number" step="0.01" min="0" value={form.cupo} onChange={(e) => setForm({ ...form, cupo: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Saldo utilizado</label>
              <input type="number" step="0.01" min="0" value={form.saldo_utilizado} onChange={(e) => setForm({ ...form, saldo_utilizado: e.target.value })} required />
            </div>
          </div>
          <div className="form-group">
            <label>Fecha de vencimiento</label>
            <input type="date" value={form.fecha_vencimiento} onChange={(e) => setForm({ ...form, fecha_vencimiento: e.target.value })} required />
          </div>
          <button type="submit" className="btn btn-primary btn-full" disabled={submitting}>
            {submitting ? 'Guardando...' : editing ? 'Actualizar' : 'Crear producto'}
          </button>
        </form>
      </Modal>
    </div>
  );
}
