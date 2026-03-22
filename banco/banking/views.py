from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Cliente, CuentaBancaria
from .permissions import EsAdministradorBancario, es_administrador_bancario
from .serializers import (
    ClienteAdminSerializer,
    ClienteAutoedicionSerializer,
    ClienteListaSerializer,
    CuentaBancariaSerializer,
    CuentaResumenSerializer,
)


class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    permission_classes = [EsAdministradorBancario]

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'partial_update', 'update'):
            from .permissions import EsAdministradorOClienteAutenticado

            return [EsAdministradorOClienteAutenticado()]
        return super().get_permissions()

    def get_queryset(self):
        qs = Cliente.objects.all()
        if es_administrador_bancario(self.request.user):
            return qs
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if es_administrador_bancario(self.request.user):
            if self.action in ('create', 'update', 'partial_update'):
                return ClienteAdminSerializer
            return ClienteListaSerializer
        if self.action in ('update', 'partial_update'):
            return ClienteAutoedicionSerializer
        return ClienteListaSerializer

    def perform_create(self, serializer):
        if not es_administrador_bancario(self.request.user):
            raise PermissionDenied('Solo el administrador bancario puede crear clientes.')
        serializer.save()

    def perform_destroy(self, instance):
        if not es_administrador_bancario(self.request.user):
            raise PermissionDenied('Solo el administrador bancario puede eliminar clientes.')
        super().perform_destroy(instance)

    def perform_update(self, serializer):
        if not es_administrador_bancario(self.request.user):
            if serializer.instance.user_id != self.request.user.id:
                raise PermissionDenied()
        serializer.save()


class CuentaBancariaViewSet(viewsets.ModelViewSet):
    queryset = CuentaBancaria.objects.select_related('cliente')
    serializer_class = CuentaBancariaSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'resumen'):
            from .permissions import EsAdministradorOClienteAutenticado

            return [EsAdministradorOClienteAutenticado()]
        return [EsAdministradorBancario()]

    def get_queryset(self):
        qs = CuentaBancaria.objects.select_related('cliente')
        if es_administrador_bancario(self.request.user):
            return qs
        return qs.filter(cliente__user=self.request.user)

    def perform_create(self, serializer):
        if not es_administrador_bancario(self.request.user):
            raise PermissionDenied('Solo el administrador bancario puede crear cuentas.')
        serializer.save()

    def perform_update(self, serializer):
        if not es_administrador_bancario(self.request.user):
            raise PermissionDenied()
        serializer.save()

    def perform_destroy(self, instance):
        if not es_administrador_bancario(self.request.user):
            raise PermissionDenied()
        super().perform_destroy(instance)

    @action(detail=True, methods=['get'], url_path='resumen')
    def resumen(self, request, pk=None):
        """Saldo e información básica de la cuenta (y cliente asociado)."""
        cuenta = self.get_object()
        serializer = CuentaResumenSerializer(cuenta)
        return Response(serializer.data)
