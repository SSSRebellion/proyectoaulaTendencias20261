from decimal import Decimal

from django.contrib.auth.models import Group, User
from rest_framework import serializers

from .models import Cliente, CuentaBancaria, Movimiento, Transferencia
from .permissions import es_administrador_bancario


class ClienteListaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = (
            'id',
            'nombre_completo',
            'numero_identificacion',
            'email',
            'telefono',
            'direccion',
            'fecha_nacimiento',
            'creado_en',
        )
        read_only_fields = fields


class ClienteAdminSerializer(serializers.ModelSerializer):
    """Alta/edición por administrador. Usuario opcional para vincular login."""

    username = serializers.CharField(write_only=True, required=False, allow_blank=False)
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = Cliente
        fields = (
            'id',
            'nombre_completo',
            'numero_identificacion',
            'email',
            'telefono',
            'direccion',
            'fecha_nacimiento',
            'username',
            'password',
            'creado_en',
            'actualizado_en',
        )
        read_only_fields = ('id', 'creado_en', 'actualizado_en')

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        if (username and not password) or (password and not username):
            raise serializers.ValidationError(
                'Debe enviar username y password juntos para crear el usuario de acceso.'
            )
        return attrs

    def create(self, validated_data):
        username = validated_data.pop('username', None)
        password = validated_data.pop('password', None)
        user = None
        if username and password:
            if User.objects.filter(username=username).exists():
                raise serializers.ValidationError({'username': 'Usuario ya existe.'})
            user = User.objects.create_user(
                username=username,
                email=validated_data['email'],
                password=password,
                is_staff=False,
                is_superuser=False,
            )
            grupo, _ = Group.objects.get_or_create(name='cliente')
            user.groups.add(grupo)
        return Cliente.objects.create(user=user, **validated_data)

    def update(self, instance, validated_data):
        validated_data.pop('username', None)
        validated_data.pop('password', None)
        return super().update(instance, validated_data)


class ClienteAutoedicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = (
            'id',
            'nombre_completo',
            'numero_identificacion',
            'email',
            'telefono',
            'direccion',
            'fecha_nacimiento',
            'creado_en',
        )
        read_only_fields = ('id', 'numero_identificacion', 'creado_en')


class CuentaBancariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CuentaBancaria
        fields = (
            'id',
            'cliente',
            'tipo',
            'numero_cuenta',
            'saldo',
            'fecha_apertura',
            'estado',
            'creado_en',
            'actualizado_en',
        )
        read_only_fields = ('id', 'numero_cuenta', 'creado_en', 'actualizado_en')


class CuentaResumenSerializer(serializers.ModelSerializer):
    cliente_nombre = serializers.CharField(source='cliente.nombre_completo', read_only=True)
    cliente_identificacion = serializers.CharField(
        source='cliente.numero_identificacion', read_only=True
    )

    class Meta:
        model = CuentaBancaria
        fields = (
            'numero_cuenta',
            'tipo',
            'saldo',
            'fecha_apertura',
            'estado',
            'cliente_nombre',
            'cliente_identificacion',
        )


class OperacionMontoSerializer(serializers.Serializer):
    monto = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))


class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movimiento
        fields = ('id', 'cuenta', 'tipo', 'monto', 'saldo_resultante', 'fecha', 'transferencia')
        read_only_fields = (
            'id',
            'cuenta',
            'tipo',
            'monto',
            'saldo_resultante',
            'fecha',
            'transferencia',
        )


class TransferenciaSerializer(serializers.ModelSerializer):
    """Detalle de transferencia con movimientos asociados."""

    movimientos = MovimientoSerializer(many=True, read_only=True)

    class Meta:
        model = Transferencia
        fields = (
            'id',
            'cuenta_origen',
            'cuenta_destino',
            'monto',
            'creado_en',
            'movimientos',
        )
        read_only_fields = (
            'id',
            'cuenta_origen',
            'cuenta_destino',
            'monto',
            'creado_en',
            'movimientos',
        )


class TransferenciaCrearSerializer(serializers.Serializer):
    cuenta_origen = serializers.PrimaryKeyRelatedField(queryset=CuentaBancaria.objects.all())
    cuenta_destino = serializers.PrimaryKeyRelatedField(queryset=CuentaBancaria.objects.all())
    monto = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=Decimal('0.01'))

    def validate(self, attrs):
        request = self.context.get('request')
        origen = attrs['cuenta_origen']
        destino = attrs['cuenta_destino']
        if origen.pk == destino.pk:
            raise serializers.ValidationError(
                {'cuenta_destino': 'La cuenta de destino debe ser distinta a la de origen.'}
            )
        if request and not es_administrador_bancario(request.user):
            if origen.cliente.user_id != request.user.id:
                raise serializers.ValidationError(
                    {'cuenta_origen': 'Solo puede transferir desde sus propias cuentas.'}
                )
        return attrs
