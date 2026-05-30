from datetime import datetime, time
from decimal import Decimal

from django.utils import timezone

from .models import Deposito


def obtener_extracto(cuenta, fecha_desde, fecha_hasta):
    """Calcula extracto: saldo inicial, movimientos en rango y saldo final."""
    inicio = timezone.make_aware(datetime.combine(fecha_desde, time.min))
    fin = timezone.make_aware(datetime.combine(fecha_hasta, time.max))

    movimientos = list(
        Deposito.objects.filter(
            cuenta=cuenta,
            fecha__gte=inicio,
            fecha__lte=fin,
        ).order_by('fecha', 'id')
    )

    ultimo_previo = (
        Deposito.objects.filter(cuenta=cuenta, fecha__lt=inicio)
        .order_by('-fecha', '-id')
        .first()
    )
    saldo_inicial = ultimo_previo.saldo_resultante if ultimo_previo else Decimal('0')

    transacciones = [
        {
            'id': m.id,
            'fecha': m.fecha,
            'tipo_operacion': m.tipo_operacion,
            'tipo_operacion_display': m.get_tipo_operacion_display(),
            'monto': m.monto,
            'descripcion': m.descripcion,
            'saldo_resultante': m.saldo_resultante,
        }
        for m in movimientos
    ]

    saldo_final = movimientos[-1].saldo_resultante if movimientos else saldo_inicial

    return {
        'cuenta_id': cuenta.id,
        'numero_cuenta': cuenta.numero_cuenta,
        'tipo_cuenta': cuenta.tipo,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'saldo_inicial': saldo_inicial,
        'saldo_final': saldo_final,
        'transacciones': transacciones,
    }
