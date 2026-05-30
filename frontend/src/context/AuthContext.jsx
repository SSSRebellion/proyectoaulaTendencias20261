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
        isStaff: Boolean(decoded.is_staff || decoded.is_superuser),
      };
    } catch {
      return null;
    }
  }, []);

  const loadUser = useCallback(async () => {
    const { access } = getTokens();
    if (!access) {
      setUser(null);
      setLoading(false);
      return;
    }

    const tokenUser = parseToken(access);
    if (!tokenUser) {
      clearTokens();
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const perfil = await apiGet('/api/auth/me/');
      tokenUser.isStaff = Boolean(perfil.es_administrador || perfil.is_staff);
      tokenUser.username = perfil.username || tokenUser.username;
      if (perfil.nombre_completo) {
        tokenUser.nombreCompleto = perfil.nombre_completo;
        tokenUser.clienteId = perfil.cliente_id;
      }
    } catch {
      if (!tokenUser.isStaff) {
        try {
          const clientes = await apiGet('/api/clientes/');
          const results = clientes.results || clientes;
          if (Array.isArray(results) && results.length > 0) {
            tokenUser.clienteId = results[0].id;
            tokenUser.nombreCompleto = results[0].nombre_completo;
          }
        } catch {
          // Admin sin perfil cliente, etc.
        }
      }
    }

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
