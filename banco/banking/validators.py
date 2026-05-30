from rest_framework import serializers

from .models import CuentaBancaria


def validar_cuenta_operable(cuenta, campo='cuenta'):
    """Impide operaciones en cuentas bloqueadas o inactivas."""
    if cuenta.estado == CuentaBancaria.Estado.BLOQUEADA:
        raise serializers.ValidationError(
            {campo: 'La cuenta está bloqueada. No se permiten operaciones.'}
        )
    if cuenta.estado == CuentaBancaria.Estado.INACTIVA:
        raise serializers.ValidationError(
            {campo: 'La cuenta está inactiva. No se permiten operaciones.'}
        )
    if cuenta.estado != CuentaBancaria.Estado.ACTIVA:
        raise serializers.ValidationError(
            {campo: 'La cuenta no está activa. No se permiten operaciones.'}
        )
