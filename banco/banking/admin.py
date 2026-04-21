from django.contrib import admin

from .models import CuentaBancaria, Deposito, Transferencia


@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ('numero_cuenta', 'cliente', 'tipo', 'saldo', 'estado', 'fecha_apertura')
    list_filter = ('tipo', 'estado')
    search_fields = ('numero_cuenta', 'cliente__numero_identificacion')


@admin.register(Deposito)
class DepositoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cuenta',
        'tipo_operacion',
        'monto',
        'saldo_resultante',
        'fecha',
    )
    list_filter = ('tipo_operacion', 'fecha')
    search_fields = ('cuenta__numero_cuenta', 'descripcion')
    readonly_fields = ('saldo_resultante', 'fecha', 'creado_en')
    ordering = ('-fecha',)


@admin.register(Transferencia)
class TransferenciaAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'cuenta_origen',
        'cuenta_destino',
        'monto',
        'estado',
        'saldo_origen_resultante',
        'saldo_destino_resultante',
        'fecha',
    )
    list_filter = ('estado', 'fecha')
    search_fields = (
        'cuenta_origen__numero_cuenta',
        'cuenta_destino__numero_cuenta',
        'descripcion',
    )
    readonly_fields = (
        'saldo_origen_resultante',
        'saldo_destino_resultante',
        'movimiento_origen',
        'movimiento_destino',
        'fecha',
    )
    ordering = ('-fecha',)
