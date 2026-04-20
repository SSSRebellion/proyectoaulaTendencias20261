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
<<<<<<< HEAD


class Transferencia(models.Model):
    """Operación entre dos cuentas; se registran dos movimientos enlazados."""

    cuenta_origen = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.PROTECT,
        related_name='transferencias_salientes',
    )
    cuenta_destino = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.PROTECT,
        related_name='transferencias_entrantes',
    )
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'Transferencia'
        verbose_name_plural = 'Transferencias'

    def __str__(self):
        return f'{self.cuenta_origen_id} → {self.cuenta_destino_id}: {self.monto}'


class Movimiento(models.Model):
    class Tipo(models.TextChoices):
        DEPOSITO = 'deposito', 'Depósito'
        RETIRO = 'retiro', 'Retiro'
        TRANSFERENCIA_ORIGEN = 'transferencia_origen', 'Transferencia (origen)'
        TRANSFERENCIA_DESTINO = 'transferencia_destino', 'Transferencia (destino)'

    cuenta = models.ForeignKey(
        CuentaBancaria,
        on_delete=models.PROTECT,
        related_name='movimientos',
    )
    tipo = models.CharField(max_length=40, choices=Tipo.choices)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    saldo_resultante = models.DecimalField(max_digits=14, decimal_places=2)
    fecha = models.DateTimeField(auto_now_add=True)
    transferencia = models.ForeignKey(
        Transferencia,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='movimientos',
    )

    class Meta:
        ordering = ['-fecha', '-id']
        verbose_name = 'Movimiento'
        verbose_name_plural = 'Movimientos'
        indexes = [
            models.Index(fields=['cuenta', '-fecha']),
        ]

    def __str__(self):
        return f'{self.get_tipo_display()} {self.monto} → saldo {self.saldo_resultante}'
=======
>>>>>>> 03e623ade403996219ded2a3524448cf8d03d531
