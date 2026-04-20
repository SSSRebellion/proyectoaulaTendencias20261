from django.contrib import admin

<<<<<<< HEAD
from .models import CuentaBancaria, Movimiento, Transferencia
=======
from .models import CuentaBancaria
>>>>>>> 03e623ade403996219ded2a3524448cf8d03d531


@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ('numero_cuenta', 'cliente', 'tipo', 'saldo', 'estado', 'fecha_apertura')
    list_filter = ('tipo', 'estado')
    search_fields = ('numero_cuenta', 'cliente__numero_identificacion')
<<<<<<< HEAD


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cuenta', 'tipo', 'monto', 'saldo_resultante', 'fecha')
    list_filter = ('tipo',)


@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cuenta_origen', 'cuenta_destino', 'monto', 'creado_en')
=======
>>>>>>> 03e623ade403996219ded2a3524448cf8d03d531
