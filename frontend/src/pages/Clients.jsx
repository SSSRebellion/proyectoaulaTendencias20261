import { useEffect, useState } from 'react';
import { apiGet, apiPost, apiPatch, apiDelete } from '../api/client';
import Modal from '../components/Modal';

export default function Clients() {
  const [clientes, setClientes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({
    nombre_completo: '', numero_identificacion: '', email: '',
    telefono: '', direccion: '', fecha_nacimiento: '',
    username: '', password: '',
  });
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadClientes = async () => {
    try {
      const data = await apiGet('/api/clientes/');
      setClientes((data.results || data) ?? []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadClientes(); }, []);

  const openCreate = () => {
    setEditing(null);
    setForm({
      nombre_completo: '', numero_identificacion: '', email: '',
      telefono: '', direccion: '', fecha_nacimiento: '',
      username: '', password: '',
    });
    setError('');
    setShowModal(true);
  };

  const openEdit = (cliente) => {
    setEditing(cliente);
    setForm({
      nombre_completo: cliente.nombre_completo,
      numero_identificacion: cliente.numero_identificacion,
      email: cliente.email,
      telefono: cliente.telefono || '',
      direccion: cliente.direccion || '',
      fecha_nacimiento: cliente.fecha_nacimiento || '',
      username: '', password: '',
    });
    setError('');
    setShowModal(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('¿Está seguro de eliminar este cliente?')) return;
    try {
      await apiDelete(`/api/clientes/${id}/`);
      setLoading(true);
      await loadClientes();
    } catch (err) {
      alert(err.data?.detail || 'Error al eliminar el cliente.');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);

    try {
      const payload = { ...form };
      // No enviar username/password vacíos en edición
      if (editing) {
        delete payload.username;
        delete payload.password;
      } else if (!payload.username || !payload.password) {
        delete payload.username;
        delete payload.password;
      }

      if (editing) {
        await apiPatch(`/api/clientes/${editing.id}/`, payload);
      } else {
        await apiPost('/api/clientes/', payload);
      }
      setShowModal(false);
      setLoading(true);
      await loadClientes();
    } catch (err) {
      if (err.data) {
        const msgs = Object.entries(err.data)
          .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
          .join('. ');
        setError(msgs);
      } else {
        setError('Error al guardar el cliente.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <div className="page-loading"><div className="spinner" /><p>Cargando clientes...</p></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Gestión de Clientes</h1>
        <button className="btn btn-primary" onClick={openCreate}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Nuevo Cliente
        </button>
      </div>

      <div className="card">
        <div className="card-body">
          {clientes.length === 0 ? (
            <p className="empty-state">No hay clientes registrados</p>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Nombre</th>
                    <th>Identificación</th>
                    <th>Email</th>
                    <th>Teléfono</th>
                    <th>Creado</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {clientes.map((c) => (
                    <tr key={c.id}>
                      <td className="mono">#{c.id}</td>
                      <td>{c.nombre_completo}</td>
                      <td className="mono">{c.numero_identificacion}</td>
                      <td>{c.email}</td>
                      <td className="mono">{c.telefono}</td>
                      <td>{new Date(c.creado_en).toLocaleDateString('es-CO')}</td>
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
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Modal crear/editar */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={editing ? 'Editar Cliente' : 'Nuevo Cliente'}>
        {error && <div className="alert alert-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-grid">
            <div className="form-group">
              <label>Nombre completo</label>
              <input type="text" value={form.nombre_completo} onChange={(e) => setForm({ ...form, nombre_completo: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Identificación</label>
              <input type="text" value={form.numero_identificacion} onChange={(e) => setForm({ ...form, numero_identificacion: e.target.value })} required disabled={!!editing} />
            </div>
            <div className="form-group">
              <label>Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Teléfono</label>
              <input type="text" value={form.telefono} onChange={(e) => setForm({ ...form, telefono: e.target.value })} required />
            </div>
            <div className="form-group full-width">
              <label>Dirección</label>
              <input type="text" value={form.direccion} onChange={(e) => setForm({ ...form, direccion: e.target.value })} required />
            </div>
            <div className="form-group">
              <label>Fecha de nacimiento</label>
              <input type="date" value={form.fecha_nacimiento} onChange={(e) => setForm({ ...form, fecha_nacimiento: e.target.value })} required />
            </div>
          </div>

          {!editing && (
            <>
              <div className="form-separator">Credenciales de acceso (opcional)</div>
              <div className="form-grid">
                <div className="form-group">
                  <label>Usuario</label>
                  <input type="text" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} />
                </div>
                <div className="form-group">
                  <label>Contraseña</label>
                  <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} minLength={8} />
                </div>
              </div>
            </>
          )}

          <button type="submit" className="btn btn-primary btn-full" disabled={submitting}>
            {submitting ? <span className="spinner-sm" /> : null}
            {submitting ? 'Guardando...' : editing ? 'Actualizar Cliente' : 'Crear Cliente'}
          </button>
        </form>
      </Modal>
    </div>
  );
}
