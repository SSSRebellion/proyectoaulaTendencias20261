"""
Permisos del módulo bancario.

Política de acceso:
    - Administrador bancario (is_staff / is_superuser):
        Gestión completa de clientes, cuentas, depósitos y transferencias.
    - Cliente autenticado:
        Solo puede operar (ver, depositar, transferir) sobre sus propias cuentas.
"""

from rest_framework.permissions import BasePermission

from .models import Cliente


# ─────────────────────────────────────────────
# Utilidades
# ─────────────────────────────────────────────

def es_administrador_bancario(user) -> bool:
    """Retorna True si el usuario es administrador bancario."""
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff


def _get_cliente(user):
    """Retorna la instancia de Cliente vinculada al usuario, o None."""
    try:
        return user.cliente
    except Cliente.DoesNotExist:
        return None


# ─────────────────────────────────────────────
# Clases de permiso
# ─────────────────────────────────────────────

class EsAdministradorBancario(BasePermission):
    """Solo administradores bancarios (staff / superuser)."""

    message = 'Acceso restringido a administradores bancarios.'

    def has_permission(self, request, view):
        return es_administrador_bancario(request.user)


class EsAdministradorOClienteAutenticado(BasePermission):
    """Permite acceso a administradores bancarios o clientes autenticados."""

    message = 'Debe ser administrador bancario o cliente autenticado.'

    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if es_administrador_bancario(u):
            return True
        return Cliente.objects.filter(user=u).exists()


class EsAdminODueñoDeCuenta(BasePermission):
    """
    Permiso a nivel de objeto: el administrador puede acceder a cualquier
    recurso; el cliente solo a recursos vinculados a sus propias cuentas.

    Funciona para objetos que tienen:
    - .cliente.user  (Cliente)
    - .cliente__user vía cuenta (CuentaBancaria)
    - .cuenta.cliente.user (Deposito)
    - .cuenta_origen.cliente.user (Transferencia)
    """

    message = 'Solo puede acceder a recursos de sus propias cuentas.'

    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if es_administrador_bancario(u):
            return True
        return Cliente.objects.filter(user=u).exists()

    def has_object_permission(self, request, view, obj):
        if es_administrador_bancario(request.user):
            return True

        user_id = request.user.id

        # Cliente → verificar que el objeto le pertenece
        # Soporta: Cliente, CuentaBancaria, Deposito, Transferencia
        if hasattr(obj, 'user_id'):
            # obj es Cliente
            return obj.user_id == user_id

        if hasattr(obj, 'cliente'):
            # obj es CuentaBancaria
            return obj.cliente.user_id == user_id

        if hasattr(obj, 'cuenta'):
            # obj es Deposito
            return obj.cuenta.cliente.user_id == user_id

        if hasattr(obj, 'cuenta_origen'):
            # obj es Transferencia — el cliente puede verla si es origen o destino
            return (
                obj.cuenta_origen.cliente.user_id == user_id
                or obj.cuenta_destino.cliente.user_id == user_id
            )

        return False


class EsAdminParaEscrituraClienteParaLectura(BasePermission):
    """
    Administrador: CRUD completo.
    Cliente autenticado: solo lectura (list, retrieve) de sus propios recursos.

    Uso: Cuentas bancarias — el cliente puede ver sus cuentas pero no
    crearlas, editarlas ni eliminarlas.
    """

    message = 'Solo el administrador puede modificar este recurso.'

    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if es_administrador_bancario(u):
            return True
        # Clientes solo pueden leer
        if view.action in ('list', 'retrieve'):
            return Cliente.objects.filter(user=u).exists()
        return False
