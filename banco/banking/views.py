from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from .models import Cliente, CuentaBancaria, Deposito, ProductoFinanciero, Transferencia
from .permissions import (
    EsAdminODueñoDeCuenta,
    EsAdministradorBancario,
    es_administrador_bancario,
)
from .serializers import (
    CambiarEstadoCuentaSerializer,
    ClienteAdminSerializer,
    ClienteAutoedicionSerializer,
    ClienteListaSerializer,
    CuentaBancariaSerializer,
    CuentaResumenSerializer,
    DepositoListaSerializer,
    DepositoSerializer,
    ExtractoQuerySerializer,
    ExtractoSerializer,
    ProductoFinancieroSerializer,
    TransferenciaListaSerializer,
    TransferenciaSerializer,
)
from .services import obtener_extracto


# ─────────────────────────────────────────────
# Clientes
# ─────────────────────────────────────────────

class ClienteViewSet(viewsets.ModelViewSet):
 

    queryset = Cliente.objects.all()

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'update', 'partial_update'):
            
            return [EsAdminODueñoDeCuenta()]
        
        return [EsAdministradorBancario()]

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

    def perform_update(self, serializer):
        """El has_object_permission ya validó propiedad; guardar directamente."""
        serializer.save()




class CuentaBancariaViewSet(viewsets.ModelViewSet):
  

    queryset = CuentaBancaria.objects.select_related('cliente')

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'resumen', 'extracto'):
            return [EsAdminODueñoDeCuenta()]
        if self.action == 'cambiar_estado':
            return [EsAdministradorBancario()]
        return [EsAdministradorBancario()]

    def get_serializer_class(self):
        return CuentaBancariaSerializer

    def get_queryset(self):
        qs = CuentaBancaria.objects.select_related('cliente')
        if es_administrador_bancario(self.request.user):
            return qs
       
        return qs.filter(cliente__user=self.request.user)

    @action(detail=True, methods=['get'], url_path='resumen')
    def resumen(self, request, pk=None):
        """Saldo e información básica de la cuenta (y cliente asociado)."""
        cuenta = self.get_object()
        serializer = CuentaResumenSerializer(cuenta)
        return Response(serializer.data)

    @action(detail=True, methods=['get'], url_path='extracto')
    def extracto(self, request, pk=None):
        """Extracto bancario en un rango de fechas."""
        cuenta = self.get_object()
        query = ExtractoQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        data = obtener_extracto(
            cuenta,
            query.validated_data['fecha_desde'],
            query.validated_data['fecha_hasta'],
        )
        return Response(ExtractoSerializer(data).data)

    @action(detail=True, methods=['patch'], url_path='cambiar-estado')
    def cambiar_estado(self, request, pk=None):
        """Bloqueo/desbloqueo de cuenta (solo administrador)."""
        cuenta = self.get_object()
        serializer = CambiarEstadoCuentaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cuenta.estado = serializer.validated_data['estado']
        cuenta.save(update_fields=['estado', 'actualizado_en'])
        return Response(CuentaBancariaSerializer(cuenta).data)




class DepositoViewSet(viewsets.ModelViewSet):
   

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




class TransferenciaViewSet(viewsets.ModelViewSet):


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


class ProductoFinancieroViewSet(viewsets.ModelViewSet):
   

    queryset = ProductoFinanciero.objects.select_related('cliente')
    serializer_class = ProductoFinancieroSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [EsAdminODueñoDeCuenta()]
        return [EsAdministradorBancario()]

    def get_queryset(self):
        qs = ProductoFinanciero.objects.select_related('cliente')
        if es_administrador_bancario(self.request.user):
            return qs
        return qs.filter(cliente__user=self.request.user)
