from decimal import Decimal

from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import CuentaBancaria, Movimiento, Transferencia


def _validar_monto(monto: Decimal) -> None:
    if monto is None or monto <= 0:
        raise ValidationError({'monto': 'El monto debe ser mayor que cero.'})


def _cuenta_debe_estar_activa(cuenta: CuentaBancaria) -> None:
    if cuenta.estado != CuentaBancaria.Estado.ACTIVA:
        raise ValidationError(
            {'cuenta': 'La cuenta no está activa; no se puede realizar la operación.'}
        )


def ejecutar_deposito(cuenta_id: int, monto: Decimal) -> Movimiento:
    _validar_monto(monto)
    with transaction.atomic():
        c = CuentaBancaria.objects.select_for_update().get(pk=cuenta_id)
        _cuenta_debe_estar_activa(c)
        c.saldo += monto
        c.save(update_fields=['saldo', 'actualizado_en'])
        return Movimiento.objects.create(
            cuenta=c,
            tipo=Movimiento.Tipo.DEPOSITO,
            monto=monto,
            saldo_resultante=c.saldo,
        )


def ejecutar_retiro(cuenta_id: int, monto: Decimal) -> Movimiento:
    _validar_monto(monto)
    with transaction.atomic():
        c = CuentaBancaria.objects.select_for_update().get(pk=cuenta_id)
        _cuenta_debe_estar_activa(c)
        if c.saldo < monto:
            raise ValidationError(
                {'monto': 'Saldo insuficiente para realizar el retiro.'}
            )
        c.saldo -= monto
        c.save(update_fields=['saldo', 'actualizado_en'])
        return Movimiento.objects.create(
            cuenta=c,
            tipo=Movimiento.Tipo.RETIRO,
            monto=monto,
            saldo_resultante=c.saldo,
        )


def ejecutar_transferencia(
    cuenta_origen_id: int, cuenta_destino_id: int, monto: Decimal
) -> Transferencia:
    _validar_monto(monto)
    if cuenta_origen_id == cuenta_destino_id:
        raise ValidationError(
            {'cuenta_destino': 'La cuenta de origen y destino deben ser distintas.'}
        )

    with transaction.atomic():
        origen = CuentaBancaria.objects.select_for_update().get(pk=cuenta_origen_id)
        destino = CuentaBancaria.objects.select_for_update().get(pk=cuenta_destino_id)
        _cuenta_debe_estar_activa(origen)
        _cuenta_debe_estar_activa(destino)
        if origen.saldo < monto:
            raise ValidationError(
                {'monto': 'Saldo insuficiente para realizar la transferencia.'}
            )
        origen.saldo -= monto
        destino.saldo += monto
        origen.save(update_fields=['saldo', 'actualizado_en'])
        destino.save(update_fields=['saldo', 'actualizado_en'])

        tr = Transferencia.objects.create(
            cuenta_origen=origen,
            cuenta_destino=destino,
            monto=monto,
        )
        Movimiento.objects.create(
            cuenta=origen,
            tipo=Movimiento.Tipo.TRANSFERENCIA_ORIGEN,
            monto=monto,
            saldo_resultante=origen.saldo,
            transferencia=tr,
        )
        Movimiento.objects.create(
            cuenta=destino,
            tipo=Movimiento.Tipo.TRANSFERENCIA_DESTINO,
            monto=monto,
            saldo_resultante=destino.saldo,
            transferencia=tr,
        )
        return tr

