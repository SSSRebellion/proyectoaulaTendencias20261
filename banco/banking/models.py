import secrets
import string

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Cliente(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cliente',
        null=True,
        blank=True,
        help_text='Usuario de acceso para clientes que se registran en la API.',
    )
    nombre_completo = models.CharField(max_length=255)
    numero_identificacion = models.CharField(max_length=32, unique=True)
    email = models.EmailField()
    telefono = models.CharField(max_length=32)
    direccion = models.TextField()
    fecha_nacimiento = models.DateField()
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f'{self.nombre_completo} ({self.numero_identificacion})'


class CuentaBancaria(models.Model):
    class TipoCuenta(models.TextChoices):
        CORRIENTE = 'corriente', 'Corriente'
        AHORROS = 'ahorros', 'Ahorros'

    class Estado(models.TextChoices):
        ACTIVA = 'activa', 'Activa'
        INACTIVA = 'inactiva', 'Inactiva'
        BLOQUEADA = 'bloqueada', 'Bloqueada'

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='cuentas',
    )
    tipo = models.CharField(max_length=20, choices=TipoCuenta.choices)
    numero_cuenta = models.CharField(max_length=20, unique=True, editable=False)
    saldo = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
    )
    fecha_apertura = models.DateField()
    estado = models.CharField(
        max_length=20,
        choices=Estado.choices,
        default=Estado.ACTIVA,
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Cuenta bancaria'
        verbose_name_plural = 'Cuentas bancarias'

    def __str__(self):
        return f'{self.numero_cuenta} — {self.cliente}'

    def _generar_numero_cuenta(self):
        alphabet = string.digits
        for _ in range(50):
            candidate = ''.join(secrets.choice(alphabet) for _ in range(12))
            if not CuentaBancaria.objects.filter(numero_cuenta=candidate).exists():
                return candidate
        raise RuntimeError('No se pudo generar un número de cuenta único.')

    def save(self, *args, **kwargs):
        if not self.numero_cuenta:
            self.numero_cuenta = self._generar_numero_cuenta()
        super().save(*args, **kwargs)


class Deposito(models.Model):
    """Registra cada operación de depósito o retiro sobre una cuenta bancaria."""

    class TipoOperacion(models.TextChoices):
        DEPOSITO = 'deposito', 'Depósito'
        RETIRO = 'retiro', 'Retiro'

    cuenta = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.CASCADE,
        related_name='depositos',
    )
    monto = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Monto de la operación (debe ser positivo).',
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha y hora en que se realizó la operación.',
    )
    tipo_operacion = models.CharField(
        max_length=20,
        choices=TipoOperacion.choices,
        default=TipoOperacion.DEPOSITO,
        help_text='Tipo de operación: depósito o retiro.',
    )
    saldo_resultante = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False,
        help_text='Saldo de la cuenta después de aplicar la operación.',
    )
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Descripción opcional de la operación.',
    )
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Depósito / Movimiento'
        verbose_name_plural = 'Depósitos / Movimientos'

    def __str__(self):
        return (
            f'{self.get_tipo_operacion_display()} de {self.monto} '
            f'en cuenta {self.cuenta.numero_cuenta} — '
            f'saldo resultante: {self.saldo_resultante}'
        )


class Transferencia(models.Model):
    """Registra una transferencia entre dos cuentas bancarias."""

    class EstadoTransferencia(models.TextChoices):
        EXITOSA = 'exitosa', 'Exitosa'
        FALLIDA = 'fallida', 'Fallida'

    cuenta_origen = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.PROTECT,
        related_name='transferencias_enviadas',
        help_text='Cuenta desde la que se envía el dinero.',
    )
    cuenta_destino = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.PROTECT,
        related_name='transferencias_recibidas',
        help_text='Cuenta que recibe el dinero.',
    )
    monto = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text='Monto a transferir (debe ser positivo).',
    )
    descripcion = models.CharField(
        max_length=255,
        blank=True,
        default='',
        help_text='Concepto o descripción de la transferencia.',
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        help_text='Fecha y hora en que se realizó la transferencia.',
    )
    estado = models.CharField(
        max_length=20,
        choices=EstadoTransferencia.choices,
        default=EstadoTransferencia.EXITOSA,
        help_text='Estado final de la transferencia.',
    )
    # Referencias a los movimientos generados en cada cuenta
    movimiento_origen = models.OneToOneField(
        Deposito,
        on_delete=models.PROTECT,
        related_name='transferencia_como_origen',
        null=True,
        blank=True,
        help_text='Movimiento (retiro) registrado en la cuenta origen.',
    )
    movimiento_destino = models.OneToOneField(
        Deposito,
        on_delete=models.PROTECT,
        related_name='transferencia_como_destino',
        null=True,
        blank=True,
        help_text='Movimiento (depósito) registrado en la cuenta destino.',
    )
    saldo_origen_resultante = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False,
        help_text='Saldo de la cuenta origen después de la transferencia.',
    )
    saldo_destino_resultante = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        editable=False,
        help_text='Saldo de la cuenta destino después de la transferencia.',
    )

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Transferencia'
        verbose_name_plural = 'Transferencias'

    def __str__(self):
        return (
            f'Transferencia de {self.monto} | '
            f'{self.cuenta_origen.numero_cuenta} → {self.cuenta_destino.numero_cuenta} | '
            f'{self.get_estado_display()}'
        )
