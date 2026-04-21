import { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { jwtDecode } from './jwtUtils';
import { login as apiLogin, registro as apiRegistro, clearTokens, getTokens, apiGet } from '../api/client';

const AuthContext = createContext(null);

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const parseToken = useCallback((accessToken) => {
    try {
      const decoded = jwtDecode(accessToken);
      return {
        userId: decoded.user_id,
        username: decoded.username || '',
        isStaff: decoded.is_staff || false,
      };
    } catch {
      return null;
    }
  }, []);

  // Cargar usuario inicial desde el token almacenado
  const loadUser = useCallback(async () => {
    const { access } = getTokens();
    if (!access) {
      setUser(null);
      setLoading(false);
      return;
    }

    // Parse token básico
    const tokenUser = parseToken(access);
    if (!tokenUser) {
      clearTokens();
      setUser(null);
      setLoading(false);
      return;
    }

    // Intentar obtener info adicional del perfil cliente
    try {
      const clientes = await apiGet('/api/clientes/');
      const results = clientes.results || clientes;
      if (Array.isArray(results) && results.length > 0) {
        tokenUser.clienteId = results[0].id;
        tokenUser.nombreCompleto = results[0].nombre_completo;
      }
    } catch {
      // Si falla (admin sin cliente, etc) seguimos con info del token
    }

    // Guardar en localStorage para persistencia
    localStorage.setItem('user_info', JSON.stringify(tokenUser));
    setUser(tokenUser);
    setLoading(false);
  }, [parseToken]);

  useEffect(() => {
    loadUser();

    const handleLogout = () => {
      setUser(null);
    };
    window.addEventListener('auth:logout', handleLogout);
    return () => window.removeEventListener('auth:logout', handleLogout);
  }, [loadUser]);

  const login = async (username, password) => {
    await apiLogin(username, password);
    await loadUser();
  };

  const register = async (formData) => {
    const result = await apiRegistro(formData);
    return result;
  };

  const logout = () => {
    clearTokens();
    setUser(null);
  };

  const isAdmin = user?.isStaff === true;
  const isClient = user !== null && !isAdmin;

  const value = {
    user,
    loading,
    login,
    register,
    logout,
    isAdmin,
    isClient,
    isAuthenticated: user !== null,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
