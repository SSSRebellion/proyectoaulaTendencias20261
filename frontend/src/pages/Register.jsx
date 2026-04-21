import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [form, setForm] = useState({
    username: '',
    password: '',
    email: '',
    nombre_completo: '',
    numero_identificacion: '',
    telefono: '',
    direccion: '',
    fecha_nacimiento: '',
  });
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
    setFieldErrors({ ...fieldErrors, [e.target.name]: null });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setFieldErrors({});
    setLoading(true);

    try {
      await register(form);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      if (err.data && typeof err.data === 'object') {
        const errors = {};
        let general = '';
        Object.entries(err.data).forEach(([key, val]) => {
          const msg = Array.isArray(val) ? val[0] : val;
          if (key === 'non_field_errors' || key === 'detail') {
            general = msg;
          } else {
            errors[key] = msg;
          }
        });
        setFieldErrors(errors);
        if (general) setError(general);
      } else {
        setError('Error al registrarse. Intente nuevamente.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="auth-page">
        <div className="auth-container">
          <div className="auth-header">
            <div className="auth-logo success">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <h1>¡Registro Exitoso!</h1>
            <p className="auth-subtitle">Redirigiendo al inicio de sesión...</p>
          </div>
        </div>
      </div>
    );
  }

  const fields = [
    { name: 'nombre_completo', label: 'Nombre completo', type: 'text', placeholder: 'Juan Pérez' },
    { name: 'numero_identificacion', label: 'Número de identificación', type: 'text', placeholder: '1234567890' },
    { name: 'email', label: 'Correo electrónico', type: 'email', placeholder: 'correo@ejemplo.com' },
    { name: 'telefono', label: 'Teléfono', type: 'text', placeholder: '3001234567' },
    { name: 'direccion', label: 'Dirección', type: 'text', placeholder: 'Calle 123 #45-67' },
    { name: 'fecha_nacimiento', label: 'Fecha de nacimiento', type: 'date', placeholder: '' },
    { name: 'username', label: 'Nombre de usuario', type: 'text', placeholder: 'juanperez' },
    { name: 'password', label: 'Contraseña (mín. 8 caracteres)', type: 'password', placeholder: '••••••••' },
  ];

  return (
    <div className="auth-page">
      <div className="auth-container auth-container-wide">
        <div className="auth-header">
          <div className="auth-logo">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11M20 10v11M8 14v3M12 14v3M16 14v3" />
            </svg>
          </div>
          <h1>Crear Cuenta</h1>
          <p className="auth-subtitle">Complete sus datos para registrarse</p>
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-grid">
            {fields.map((f) => (
              <div className={`form-group ${fieldErrors[f.name] ? 'has-error' : ''}`} key={f.name}>
                <label htmlFor={f.name}>{f.label}</label>
                <input
                  id={f.name}
                  name={f.name}
                  type={f.type}
                  value={form[f.name]}
                  onChange={handleChange}
                  placeholder={f.placeholder}
                  required
                />
                {fieldErrors[f.name] && <span className="field-error">{fieldErrors[f.name]}</span>}
              </div>
            ))}
          </div>

          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? <span className="spinner-sm" /> : null}
            {loading ? 'Registrando...' : 'Registrarse'}
          </button>
        </form>

        <div className="auth-footer">
          <p>
            ¿Ya tiene cuenta? <Link to="/login">Inicie sesión</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
