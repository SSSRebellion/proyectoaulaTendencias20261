from rest_framework.permissions import BasePermission

from .models import Cliente


def es_administrador_bancario(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.is_superuser or user.is_staff


class EsAdministradorBancario(BasePermission):
    def has_permission(self, request, view):
        return es_administrador_bancario(request.user)


class EsAdministradorOClienteAutenticado(BasePermission):
    """Permite acceso a administradores o a usuarios cliente autenticados."""

    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated:
            return False
        if es_administrador_bancario(u):
            return True
        return Cliente.objects.filter(user=u).exists()
