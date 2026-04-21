from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.db import transaction
from rest_framework import serializers

from .models import Cliente, CuentaBancaria, Deposito, Transferencia


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


class CuentaClienteCrearSerializer(serializers.ModelSerializer):
    """
    Serializer para que un cliente cree su propia cuenta bancaria.

    El cliente solo elige el tipo de cuenta. El sistema asigna
    automáticamente: cliente (del usuario autenticado), fecha de apertura
    (hoy), saldo inicial (0), estado (activa), y genera el número de
    cuenta al azar.
    """

    class Meta:
        model = CuentaBancaria
        fields = (
            'id',
            'tipo',
            'numero_cuenta',
            'saldo',
            'fecha_apertura',
            'estado',
            'creado_en',
        )
        read_only_fields = ('id', 'numero_cuenta', 'saldo', 'fecha_apertura', 'estado', 'creado_en')

    def create(self, validated_data):
        from datetime import date

        user = self.context['request'].user
        cliente = user.cliente  # el view ya validó que existe

        return CuentaBancaria.objects.create(
            cliente=cliente,
            tipo=validated_data['tipo'],
            saldo=0,
            fecha_apertura=date.today(),
            estado=CuentaBancaria.Estado.ACTIVA,
        )


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


class DepositoSerializer(serializers.ModelSerializer):
    """Serializer para crear depósitos y retiros."""

    class Meta:
        model = Deposito
        fields = (
            'id',
            'cuenta',
            'monto',
            'tipo_operacion',
            'descripcion',
            'fecha',
            'saldo_resultante',
            'creado_en',
        )
        read_only_fields = ('id', 'fecha', 'saldo_resultante', 'creado_en')

    def validate(self, attrs):
        cuenta = attrs['cuenta']
        monto = attrs['monto']
        tipo = attrs.get('tipo_operacion', Deposito.TipoOperacion.DEPOSITO)

        if cuenta.estado != CuentaBancaria.Estado.ACTIVA:
            raise serializers.ValidationError(
                {'cuenta': 'La cuenta no está activa.'}
            )

        if tipo == Deposito.TipoOperacion.RETIRO and cuenta.saldo < monto:
            raise serializers.ValidationError(
                {'monto': f'Fondos insuficientes. Saldo actual: {cuenta.saldo}'}
            )

        return attrs

    def create(self, validated_data):
        cuenta = validated_data['cuenta']
        monto = validated_data['monto']
        tipo = validated_data.get('tipo_operacion', Deposito.TipoOperacion.DEPOSITO)

        with transaction.atomic():
            # Re-leer la cuenta con bloqueo para evitar condiciones de carrera
            cuenta = CuentaBancaria.objects.select_for_update().get(pk=cuenta.pk)

            if tipo == Deposito.TipoOperacion.DEPOSITO:
                cuenta.saldo += monto
            else:
                if cuenta.saldo < monto:
                    raise serializers.ValidationError(
                        {'monto': f'Fondos insuficientes. Saldo actual: {cuenta.saldo}'}
                    )
                cuenta.saldo -= monto

            cuenta.save(update_fields=['saldo'])

            validated_data['saldo_resultante'] = cuenta.saldo
            deposito = Deposito.objects.create(**validated_data)

        return deposito


class DepositoListaSerializer(serializers.ModelSerializer):
    """Serializer de solo lectura con información expandida."""

    numero_cuenta = serializers.CharField(source='cuenta.numero_cuenta', read_only=True)
    tipo_operacion_display = serializers.CharField(
        source='get_tipo_operacion_display', read_only=True
    )

    class Meta:
        model = Deposito
        fields = (
            'id',
            'cuenta',
            'numero_cuenta',
            'monto',
            'tipo_operacion',
            'tipo_operacion_display',
            'descripcion',
            'fecha',
            'saldo_resultante',
            'creado_en',
        )
        read_only_fields = fields


class TransferenciaSerializer(serializers.Serializer):
    """
    Serializer para ejecutar una transferencia entre dos cuentas bancarias.

    Implementa:
    - Validación de saldo suficiente en cuenta origen
    - Actualización atómica de ambas cuentas (con select_for_update ordenado por PK)
    - Registro de movimientos (Deposito) en ambas cuentas al completarse la transferencia
    """

    cuenta_origen = serializers.PrimaryKeyRelatedField(
        queryset=CuentaBancaria.objects.all(),
        help_text='ID de la cuenta que envía el dinero.',
    )
    cuenta_destino = serializers.PrimaryKeyRelatedField(
        queryset=CuentaBancaria.objects.all(),
        help_text='ID de la cuenta que recibe el dinero.',
    )
    monto = serializers.DecimalField(
        max_digits=14,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text='Monto a transferir (debe ser mayor a 0).',
    )
    descripcion = serializers.CharField(
        max_length=255,
        required=False,
        default='',
        help_text='Concepto o descripción de la transferencia.',
    )

    def validate(self, attrs):
        origen = attrs['cuenta_origen']
        destino = attrs['cuenta_destino']
        monto = attrs['monto']

        # No se puede transferir a la misma cuenta
        if origen.pk == destino.pk:
            raise serializers.ValidationError(
                {'cuenta_destino': 'La cuenta destino debe ser diferente a la cuenta origen.'}
            )

        # Ambas cuentas deben estar activas
        if origen.estado != CuentaBancaria.Estado.ACTIVA:
            raise serializers.ValidationError(
                {'cuenta_origen': 'La cuenta origen no está activa.'}
            )
        if destino.estado != CuentaBancaria.Estado.ACTIVA:
            raise serializers.ValidationError(
                {'cuenta_destino': 'La cuenta destino no está activa.'}
            )

        # Validación preliminar de saldo (se re-valida dentro de la transacción atómica)
        if origen.saldo < monto:
            raise serializers.ValidationError(
                {'monto': f'Fondos insuficientes en la cuenta origen. Saldo actual: {origen.saldo}'}
            )

        return attrs

    def create(self, validated_data):
        cuenta_origen_obj = validated_data['cuenta_origen']
        cuenta_destino_obj = validated_data['cuenta_destino']
        monto = validated_data['monto']
        descripcion = validated_data.get('descripcion', '')

        with transaction.atomic():
            # ── Bloqueo ordenado por PK para prevenir deadlocks ──
            pks = sorted([cuenta_origen_obj.pk, cuenta_destino_obj.pk])
            cuentas_bloqueadas = {
                c.pk: c
                for c in CuentaBancaria.objects.select_for_update().filter(pk__in=pks)
            }
            origen = cuentas_bloqueadas[cuenta_origen_obj.pk]
            destino = cuentas_bloqueadas[cuenta_destino_obj.pk]

            # ── Re-validación dentro del bloqueo (condición de carrera) ──
            if origen.saldo < monto:
                raise serializers.ValidationError(
                    {'monto': f'Fondos insuficientes. Saldo actual: {origen.saldo}'}
                )

            # ── Actualización atómica de saldos ──
            origen.saldo -= monto
            destino.saldo += monto
            origen.save(update_fields=['saldo'])
            destino.save(update_fields=['saldo'])

            # ── Registro de movimientos en ambas cuentas ──
            concepto_origen = (
                f'Transferencia enviada a cuenta {destino.numero_cuenta}'
            )
            if descripcion:
                concepto_origen += f' — {descripcion}'

            movimiento_origen = Deposito.objects.create(
                cuenta=origen,
                monto=monto,
                tipo_operacion=Deposito.TipoOperacion.RETIRO,
                saldo_resultante=origen.saldo,
                descripcion=concepto_origen,
            )

            concepto_destino = (
                f'Transferencia recibida de cuenta {origen.numero_cuenta}'
            )
            if descripcion:
                concepto_destino += f' — {descripcion}'

            movimiento_destino = Deposito.objects.create(
                cuenta=destino,
                monto=monto,
                tipo_operacion=Deposito.TipoOperacion.DEPOSITO,
                saldo_resultante=destino.saldo,
                descripcion=concepto_destino,
            )

            # ── Registro de la transferencia ──
            transferencia = Transferencia.objects.create(
                cuenta_origen=origen,
                cuenta_destino=destino,
                monto=monto,
                descripcion=descripcion,
                estado=Transferencia.EstadoTransferencia.EXITOSA,
                movimiento_origen=movimiento_origen,
                movimiento_destino=movimiento_destino,
                saldo_origen_resultante=origen.saldo,
                saldo_destino_resultante=destino.saldo,
            )

        return transferencia


class TransferenciaListaSerializer(serializers.ModelSerializer):
    """Serializer de solo lectura para listar transferencias con campos expandidos."""

    cuenta_origen_numero = serializers.CharField(
        source='cuenta_origen.numero_cuenta', read_only=True
    )
    cuenta_destino_numero = serializers.CharField(
        source='cuenta_destino.numero_cuenta', read_only=True
    )
    cliente_origen_nombre = serializers.CharField(
        source='cuenta_origen.cliente.nombre_completo', read_only=True
    )
    cliente_destino_nombre = serializers.CharField(
        source='cuenta_destino.cliente.nombre_completo', read_only=True
    )
    estado_display = serializers.CharField(
        source='get_estado_display', read_only=True
    )

    class Meta:
        model = Transferencia
        fields = (
            'id',
            'cuenta_origen',
            'cuenta_origen_numero',
            'cliente_origen_nombre',
            'cuenta_destino',
            'cuenta_destino_numero',
            'cliente_destino_nombre',
            'monto',
            'descripcion',
            'fecha',
            'estado',
            'estado_display',
            'saldo_origen_resultante',
            'saldo_destino_resultante',
            'movimiento_origen',
            'movimiento_destino',
        )
        read_only_fields = fields
