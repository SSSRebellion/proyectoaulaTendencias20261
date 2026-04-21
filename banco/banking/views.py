"""
Vistas del módulo bancario.

Política de permisos:
    ┌──────────────────────┬──────────────────────────────────────────────────┐
    │ Recurso              │ Admin                  │ Cliente                │
    ├──────────────────────┼────────────────────────┼────────────────────────┤
    │ Clientes             │ CRUD completo          │ Ver/editar solo el     │
    │                      │                        │ suyo propio            │
    ├──────────────────────┼────────────────────────┼────────────────────────┤
    │ Cuentas bancarias    │ CRUD completo          │ Solo lectura de sus    │
    │                      │                        │ propias cuentas        │
    ├──────────────────────┼────────────────────────┼────────────────────────┤
    │ Depósitos            │ CRUD completo          │ Crear en sus cuentas + │
    │                      │                        │ ver su historial       │
    ├──────────────────────┼────────────────────────┼────────────────────────┤
    │ Transferencias       │ CRUD completo          │ Crear desde sus        │
    │                      │                        │ cuentas + ver las suyas│
    └──────────────────────┴────────────────────────┴────────────────────────┘
"""

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Cliente, CuentaBancaria, Deposito, Transferencia
from .permissions import (
    EsAdminODueñoDeCuenta,
    EsAdminParaEscrituraClienteParaLectura,
    EsAdministradorBancario,
    EsAdministradorOClienteAutenticado,
    es_administrador_bancario,
)
from .serializers import (
    ClienteAdminSerializer,
    ClienteAutoedicionSerializer,
    ClienteListaSerializer,
    CuentaBancariaSerializer,
    CuentaResumenSerializer,
    DepositoListaSerializer,
    DepositoSerializer,
    TransferenciaListaSerializer,
    TransferenciaSerializer,
)


# ─────────────────────────────────────────────
# Clientes
# ─────────────────────────────────────────────

class ClienteViewSet(viewsets.ModelViewSet):
    """
    Admin: CRUD completo de clientes.
    Cliente: ver y editar únicamente su propio perfil.
    """

    queryset = Cliente.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'update', 'partial_update'):
            # Admin o cliente dueño del recurso
            return [EsAdminODueñoDeCuenta()]
        # create, destroy → solo admin
        return [EsAdministradorBancario()]

    def get_queryset(self):
        qs = Cliente.objects.all()
        if es_administrador_bancario(self.request.user):
            return qs
        # Cliente solo ve su propio perfil
        return qs.filter(user=self.request.user)

    def get_serializer_class(self):
        if es_administrador_bancario(self.request.user):
            if self.action in ('create', 'update', 'partial_update'):
                return ClienteAdminSerializer
            return ClienteListaSerializer
        # Cliente editando su propio perfil
        if self.action in ('update', 'partial_update'):
            return ClienteAutoedicionSerializer
        return ClienteListaSerializer

    def perform_update(self, serializer):
        """El has_object_permission ya validó propiedad; guardar directamente."""
        serializer.save()


# ─────────────────────────────────────────────
# Cuentas bancarias
# ─────────────────────────────────────────────

class CuentaBancariaViewSet(viewsets.ModelViewSet):
    """
    Admin: CRUD completo de cuentas bancarias.
    Cliente: puede crear cuentas propias + lectura de sus cuentas.
    """

    queryset = CuentaBancaria.objects.select_related('cliente')

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'resumen', 'create'):
            # Admin y clientes autenticados pueden listar, ver y crear
            return [EsAdminODueñoDeCuenta()]
        # update, partial_update, destroy → solo admin
        return [EsAdministradorBancario()]

    def get_serializer_class(self):
        from .serializers import CuentaClienteCrearSerializer

        if self.action == 'create':
            if not es_administrador_bancario(self.request.user):
                # Cliente crea su propia cuenta (auto-asigna cliente, fecha, saldo)
                return CuentaClienteCrearSerializer
        return CuentaBancariaSerializer

    def get_queryset(self):
        qs = CuentaBancaria.objects.select_related('cliente')
        if es_administrador_bancario(self.request.user):
            return qs
        # Cliente solo ve sus propias cuentas
        return qs.filter(cliente__user=self.request.user)

    @action(detail=True, methods=['get'], url_path='resumen')
    def resumen(self, request, pk=None):
        """Saldo e información básica de la cuenta (y cliente asociado)."""
        cuenta = self.get_object()  # has_object_permission se ejecuta aquí
        serializer = CuentaResumenSerializer(cuenta)
        return Response(serializer.data)


# ─────────────────────────────────────────────
# Depósitos / Movimientos
# ─────────────────────────────────────────────

class DepositoViewSet(viewsets.ModelViewSet):
    """
    Admin: CRUD completo de depósitos.
    Cliente: crear depósitos/retiros en sus propias cuentas + ver su historial.
    """

    queryset = Deposito.objects.select_related('cuenta', 'cuenta__cliente')

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return [EsAdminODueñoDeCuenta()]
        # update, partial_update, destroy → solo admin
        return [EsAdministradorBancario()]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return DepositoListaSerializer
        return DepositoSerializer

    def get_queryset(self):
        qs = Deposito.objects.select_related('cuenta', 'cuenta__cliente')
        if es_administrador_bancario(self.request.user):
            return qs
        # Cliente solo ve movimientos de sus propias cuentas
        return qs.filter(cuenta__cliente__user=self.request.user)

    def perform_create(self, serializer):
        """Valida que el cliente solo opere sobre sus propias cuentas."""
        if not es_administrador_bancario(self.request.user):
            cuenta = serializer.validated_data['cuenta']
            if cuenta.cliente.user_id != self.request.user.id:
                raise PermissionDenied(
                    'Solo puede realizar operaciones en sus propias cuentas.'
                )
        serializer.save()


# ─────────────────────────────────────────────
# Transferencias
# ─────────────────────────────────────────────

class TransferenciaViewSet(viewsets.ModelViewSet):
    """
    Endpoint para ejecutar y consultar transferencias entre cuentas bancarias.

    POST /api/transferencias/
        Ejecuta una transferencia. Requiere: cuenta_origen, cuenta_destino, monto.
        Validaciones:
        - Saldo suficiente en la cuenta origen
        - Ambas cuentas activas
        - Cuenta origen ≠ cuenta destino
        - Cliente solo puede transferir desde sus propias cuentas
        Garantías:
        - Actualización atómica de ambos saldos (transaction.atomic + select_for_update)
        - Bloqueo ordenado por PK para prevenir deadlocks
        - Registro de movimiento (Deposito) en ambas cuentas
        - Registro de Transferencia con referencias a ambos movimientos

    GET /api/transferencias/
        Lista transferencias. Administradores ven todas; clientes solo las suyas
        (donde son origen o destino).
    """

    queryset = Transferencia.objects.select_related(
        'cuenta_origen', 'cuenta_origen__cliente',
        'cuenta_destino', 'cuenta_destino__cliente',
    )

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'create'):
            return [EsAdminODueñoDeCuenta()]
        # update, partial_update, destroy → solo admin
        return [EsAdministradorBancario()]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TransferenciaListaSerializer
        return TransferenciaSerializer

    def get_queryset(self):
        qs = Transferencia.objects.select_related(
            'cuenta_origen', 'cuenta_origen__cliente',
            'cuenta_destino', 'cuenta_destino__cliente',
        )
        if es_administrador_bancario(self.request.user):
            return qs
        # Los clientes ven transferencias donde son origen O destino
        return qs.filter(
            Q(cuenta_origen__cliente__user=self.request.user)
            | Q(cuenta_destino__cliente__user=self.request.user)
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Clientes solo pueden transferir desde sus propias cuentas
        if not es_administrador_bancario(request.user):
            cuenta_origen = serializer.validated_data['cuenta_origen']
            if cuenta_origen.cliente.user_id != request.user.id:
                raise PermissionDenied(
                    'Solo puede realizar transferencias desde sus propias cuentas.'
                )

        transferencia = serializer.save()

        # Responder con el serializer de lista para mostrar toda la información
        response_serializer = TransferenciaListaSerializer(transferencia)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
