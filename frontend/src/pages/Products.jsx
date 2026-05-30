import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';

export default function Products() {
  const [productos, setProductos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await apiGet('/api/productos/');
        setProductos((data.results || data) ?? []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const fmt = (n) => parseFloat(n).toLocaleString('es-CO', { minimumFractionDigits: 2 });

  if (loading) {
    return <div className="page-loading"><div className="spinner" /><p>Cargando productos...</p></div>;
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Mis Productos Financieros</h1>
          <p className="page-subtitle">Tarjetas de crédito y préstamos asociados</p>
        </div>
      </div>

      <div className="card">
        <div className="card-body">
          {productos.length === 0 ? (
            <p className="empty-state">No tiene productos financieros registrados.</p>
          ) : (
            <div className="table-responsive">
              <table className="table">
                <thead>
                  <tr>
                    <th>Tipo</th>
                    <th>Nombre</th>
                    <th>Cupo</th>
                    <th>Utilizado</th>
                    <th>Disponible</th>
                    <th>Estado</th>
                    <th>Vencimiento</th>
                  </tr>
                </thead>
                <tbody>
                  {productos.map((p) => (
                    <tr key={p.id}>
                      <td>{p.tipo_display}</td>
                      <td>{p.nombre || '—'}</td>
                      <td className="mono">${fmt(p.cupo)}</td>
                      <td className="mono">${fmt(p.saldo_utilizado)}</td>
                      <td className="mono">${fmt(p.cupo_disponible)}</td>
                      <td>
                        <span className={`badge badge-${p.estado === 'activo' ? 'success' : 'warning'}`}>
                          {p.estado_display}
                        </span>
                      </td>
                      <td>{new Date(p.fecha_vencimiento).toLocaleDateString('es-CO')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
