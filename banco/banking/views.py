from django.db.models import Q

from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import Cliente, CuentaBancaria, Transferencia
from .permissions import EsAdministradorBancario, es_administrador_bancario
from .serializers import (
    ClienteAdminSerializer,
    ClienteAutoedicionSerializer,
    ClienteListaSerializer,
    CuentaBancariaSerializer,
    CuentaResumenSerializer,
    MovimientoSerializer,
    OperacionMontoSerializer,
    TransferenciaCrearSerializer,
    TransferenciaSerializer,
)
from .services import ejecutar_deposito, ejecutar_retiro, ejecutar_transferencia


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
        if self.action in (
            'list',
            'retrieve',
            'resumen',
            'deposito',
            'retiro',
            'movimientos',
        ):
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

    @action(detail=True, methods=['post'], url_path='deposito')
    def deposito(self, request, pk=None):
        cuenta = self.get_object()
        serializer = OperacionMontoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mov = ejecutar_deposito(cuenta.pk, serializer.validated_data['monto'])
        return Response(
            MovimientoSerializer(mov).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['post'], url_path='retiro')
    def retiro(self, request, pk=None):
        cuenta = self.get_object()
        serializer = OperacionMontoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mov = ejecutar_retiro(cuenta.pk, serializer.validated_data['monto'])
        return Response(
            MovimientoSerializer(mov).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=['get'], url_path='movimientos')
    def movimientos(self, request, pk=None):
        cuenta = self.get_object()
        movs = cuenta.movimientos.all()[:500]
        return Response(MovimientoSerializer(movs, many=True).data)


class TransferenciaViewSet(mixins.CreateModelMixin, ReadOnlyModelViewSet):
    """Transferencias atómicas entre cuentas (consulta y creación)."""

    queryset = Transferencia.objects.all()

    def get_permissions(self):
        from .permissions import EsAdministradorOClienteAutenticado

        return [EsAdministradorOClienteAutenticado()]

    def get_queryset(self):
        qs = Transferencia.objects.select_related(
            'cuenta_origen', 'cuenta_destino'
        ).prefetch_related('movimientos')
        u = self.request.user
        if es_administrador_bancario(u):
            return qs
        return (
            qs.filter(
                Q(cuenta_origen__cliente__user=u)
                | Q(cuenta_destino__cliente__user=u)
            )
            .distinct()
        )

    def get_serializer_class(self):
        if self.action == 'create':
            return TransferenciaCrearSerializer
        return TransferenciaSerializer

    def create(self, request, *args, **kwargs):
        serializer = TransferenciaCrearSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        o = serializer.validated_data['cuenta_origen']
        d = serializer.validated_data['cuenta_destino']
        monto = serializer.validated_data['monto']
        tr = ejecutar_transferencia(o.pk, d.pk, monto)
        tr = Transferencia.objects.prefetch_related('movimientos').get(pk=tr.pk)
        return Response(
            TransferenciaSerializer(tr).data,
            status=status.HTTP_201_CREATED,
        )
