import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Accounts from './pages/Accounts';
import Deposits from './pages/Deposits';
import Transfers from './pages/Transfers';
import Clients from './pages/Clients';
import AdminAccounts from './pages/AdminAccounts';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="app-layout">
          <Navbar />
          <main className="main-content">
            <Routes>
              {/* Públicas */}
              <Route path="/login" element={<Login />} />
              <Route path="/registro" element={<Register />} />

              {/* Protegidas — cualquier usuario autenticado */}
              <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
              <Route path="/cuentas" element={<ProtectedRoute><Accounts /></ProtectedRoute>} />
              <Route path="/depositos" element={<ProtectedRoute><Deposits /></ProtectedRoute>} />
              <Route path="/transferencias" element={<ProtectedRoute><Transfers /></ProtectedRoute>} />

              {/* Protegidas — solo administrador */}
              <Route path="/admin/clientes" element={<ProtectedRoute requireAdmin><Clients /></ProtectedRoute>} />
              <Route path="/admin/cuentas" element={<ProtectedRoute requireAdmin><AdminAccounts /></ProtectedRoute>} />

              {/* Redirect por defecto */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </main>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}
