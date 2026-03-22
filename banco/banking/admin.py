from django.contrib import admin

from .models import CuentaBancaria


@admin.register(CuentaBancaria)
class CuentaBancariaAdmin(admin.ModelAdmin):
    list_display = ('numero_cuenta', 'cliente', 'tipo', 'saldo', 'estado', 'fecha_apertura')
    list_filter = ('tipo', 'estado')
    search_fields = ('numero_cuenta', 'cliente__numero_identificacion')
